from django.contrib import admin
from .models import Account, AccessLevel, UserAccess

class AccessLevelInline(admin.TabularInline):
    model = AccessLevel
    extra = 0  # Ensures no extra forms are displayed by default

class AccountAdmin(admin.ModelAdmin):
    inlines = [AccessLevelInline]

admin.site.register(Account, AccountAdmin)
admin.site.register(UserAccess)