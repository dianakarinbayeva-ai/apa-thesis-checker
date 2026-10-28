from django.contrib import admin
from .models import RuleProfile, Submission


@admin.register(RuleProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "active")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "created_at")
    list_filter = ("status", "language")
    readonly_fields = ("id", "result", "profile", "file", "created_at", "started_at", "finished_at")
