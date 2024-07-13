from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_accounts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Account {self.pk} - Owned by {self.owner.username}"
    
    class Meta:
        permissions = [
            ("manage_users", "Can manage users"),
            ("view_head_office", "Can view head office"),
            ("view_district_office", "Can view district office"),
            ("view_branch_location", "Can view branch location"),
        ]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            content_type = ContentType.objects.get_for_model(Account)
            for codename, name in self._meta.permissions:
                Permission.objects.create(
                    codename=codename,
                    name=name,
                    content_type=content_type,
                )

    def get_or_create_head_office(self):
        head_office, created = AccessLevel.objects.get_or_create(
            account=self,
            name=AccessLevel.HEAD_OFFICE,
            defaults={'parent': None}
        )
        return head_office

class AccessLevel(models.Model):
    HEAD_OFFICE = 'HO'
    DISTRICT_OFFICE = 'DO'
    BRANCH_LOCATION = 'BL'
    LEVEL_CHOICES = [
        (HEAD_OFFICE, 'Head Office'),
        (DISTRICT_OFFICE, 'District Office'),
        (BRANCH_LOCATION, 'Branch Location'),
    ]

    name = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='access_levels')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    class Meta:
        unique_together = ['name', 'account']

    def __str__(self):
        return self.get_name_display()
    
    def save(self, *args, **kwargs):
        if self.name == self.HEAD_OFFICE:
            if AccessLevel.objects.filter(account=self.account, name=self.HEAD_OFFICE).exists():
                raise ValidationError("Only one Head Office is allowed per account.")
        super().save(*args, **kwargs)

class UserAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_accesses')
    access_level = models.ForeignKey(AccessLevel, on_delete=models.CASCADE, related_name='user_accesses')

    class Meta:
        unique_together = ['user', 'access_level']

    def __str__(self):
        return f"{self.user.username} - {self.access_level}"
