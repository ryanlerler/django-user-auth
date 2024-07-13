from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Account, AccessLevel, UserAccess
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Permission
from django.contrib.auth.decorators import permission_required

@require_POST
@require_POST
def create_account(request):
    username = request.POST['username']
    password = request.POST['password']
    user = User.objects.create_user(username=username, password=password)
    account = Account.objects.create(owner=user)
    
    # Use the new method to get or create the head office
    head_office = account.get_or_create_head_office()
    
    UserAccess.objects.create(user=user, access_level=head_office)

    # Grant all permissions to the account owner
    permissions = Permission.objects.filter(content_type__app_label='account')
    user.user_permissions.add(*permissions)

    return JsonResponse({'message': 'Account created successfully'}, status=201)

@login_required
@permission_required('account.manage_users')
@require_POST
def create_user(request):
    username = request.POST['username']
    password = request.POST['password']
    access_level_id = request.POST['access_level']
    user = User.objects.create_user(username=username, password=password)
    access_level = get_object_or_404(AccessLevel, id=access_level_id)
    UserAccess.objects.create(user=user, access_level=access_level)
    
    # Assign permissions based on access level
    if access_level.name == AccessLevel.HEAD_OFFICE:
        permission = Permission.objects.get(codename='view_head_office')
    elif access_level.name == AccessLevel.DISTRICT_OFFICE:
        permission = Permission.objects.get(codename='view_district_office')
    elif access_level.name == AccessLevel.BRANCH_LOCATION:
        permission = Permission.objects.get(codename='view_branch_location')
    
    user.user_permissions.add(permission)
    
    return JsonResponse({'message': 'User created successfully'}, status=201)

@login_required
@require_POST
def create_access_level(request):
    name = request.POST['name']
    account_id = request.POST['account']
    parent_id = request.POST.get('parent')
    
    account = get_object_or_404(Account, id=account_id)
    
    # Ensure only the account owner can create access levels
    if request.user != account.owner:
        return JsonResponse({'error': 'Only the account owner can create access levels'}, status=403)
    
    parent = get_object_or_404(AccessLevel, id=parent_id) if parent_id else None
    
    # Check hierarchy
    if name == AccessLevel.DISTRICT_OFFICE and (not parent or parent.name != AccessLevel.HEAD_OFFICE):
        return JsonResponse({'error': 'District Office must have a Head Office as parent'}, status=400)
    if name == AccessLevel.BRANCH_LOCATION and (not parent or parent.name != AccessLevel.DISTRICT_OFFICE):
        return JsonResponse({'error': 'Branch Location must have a District Office as parent'}, status=400)
    
    AccessLevel.objects.create(name=name, account=account, parent=parent)
    return JsonResponse({'message': 'Access level created successfully'}, status=201)

@login_required
def get_user_access_levels(request):
    user_access_levels = UserAccess.objects.filter(user=request.user).select_related('access_level')
    access_levels = [ua.access_level.name for ua in user_access_levels]
    return JsonResponse({'access_levels': access_levels}, status=200)

@login_required
@permission_required('account.manage_users')
@require_POST
def change_user_access(request):
    user_id = request.POST['user_id']
    new_access_level_id = request.POST['new_access_level']
    
    user = get_object_or_404(User, id=user_id)
    new_access_level = get_object_or_404(AccessLevel, id=new_access_level_id)
    
    # Ensure the user being modified belongs to the same account
    if not UserAccess.objects.filter(user=user, access_level__account=new_access_level.account).exists():
        return JsonResponse({'error': 'Cannot modify access for users from different accounts'}, status=403)
    
    user_access = UserAccess.objects.get(user=user)
    user_access.access_level = new_access_level
    user_access.save()
    
    # Update permissions
    user.user_permissions.clear()
    if new_access_level.name == AccessLevel.HEAD_OFFICE:
        permission = Permission.objects.get(codename='view_head_office')
    elif new_access_level.name == AccessLevel.DISTRICT_OFFICE:
        permission = Permission.objects.get(codename='view_district_office')
    elif new_access_level.name == AccessLevel.BRANCH_LOCATION:
        permission = Permission.objects.get(codename='view_branch_location')
    
    user.user_permissions.add(permission)
    
    return JsonResponse({'message': 'User access level changed successfully'}, status=200)