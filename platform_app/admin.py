from django.contrib import admin
from .models import RuleProfile, Submission, StudyGroup, RosterStudent


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ("programme", "group_number", "programme_code", "intake", "year", "roster_loaded")
    filter_horizontal = ("curators",)


@admin.register(RosterStudent)
class RosterStudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "group", "position", "user")
    list_filter = ("group",)
    search_fields = ("full_name", "user__username")
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "enrollment_code")


@admin.register(RuleProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "active")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "created_at")
    list_filter = ("status", "language")
    readonly_fields = ("id", "result", "profile", "file", "created_at", "started_at", "finished_at")
