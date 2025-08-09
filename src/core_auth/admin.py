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
    list_display = ("id", "identifier_submitted", "user", "status", "created_at", "processed_by", "processed_at")
    list_filter = ("status", "created_at")
    search_fields = ("identifier_submitted", "user__username", "user__email")
    readonly_fields = ("created_at", "processed_at", "created_ip", "user_agent")
    ordering = ("-created_at",)