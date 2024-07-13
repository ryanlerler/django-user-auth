from django.urls import path
from app import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create-account/', views.create_account, name='create_account'),
    path('create-user/', views.create_user, name='create_user'),
    path('create-access-level/', views.create_access_level, name='create_access_level'),
    path('get-user-access-levels/', views.get_user_access_levels, name='get_user_access_levels'),
    path('change-user-access/', views.change_user_access, name='change_user_access'),
]
