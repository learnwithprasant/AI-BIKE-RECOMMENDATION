from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'email_verified', 'created_at')
    list_filter = ('email_verified',)
    search_fields = ('user__username', 'user__email', 'phone')
