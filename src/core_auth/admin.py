# templates/app_template/admin.py
from django.contrib import admin
from .adapters.models import Core_auth, CoreAuthProfile, PasswordResetRequest


@admin.register(Core_auth)
class CoreAuthItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(CoreAuthProfile)
class CoreAuthProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "must_change_password", "updated_at")
    list_filter = ("must_change_password",)
    search_fields = ("user__username", "user__email")
    ordering = ("-updated_at",)


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "short_code", "username_input", "email_input", "user", "status", "created_at", "processed_by", "processed_at", "delivered_at", "expires_at")
    list_filter = ("status", "created_at", "processed_at", "delivered_at")
    search_fields = ("short_code", "username_input", "email_input", "user__username", "user__email")
    readonly_fields = ("created_at", "processed_at", "delivered_at", "expires_at", "created_ip", "user_agent", "short_code")
    ordering = ("-created_at",)