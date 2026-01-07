from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from tracker.models import TaskType, Position, Employee, Project, Task, Team, Comment


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["name"]
    search_fields = ["name"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["name"]
    search_fields = ["name"]


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position",)
    fieldsets = UserAdmin.fieldsets + (("Additional info", {"fields": ("position",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "position",
                )
            },
        ),
    )


class UserFilter(SimpleListFilter):
    """Custom SimpleListFilter"""

    title = None
    parameter_name = None
    field_name = None

    def lookups(self, request, model_admin):
       # Get the list of users for filtering
        return [(user.id, user.username) for user in get_user_model().objects.all()]

    def queryset(self, request, queryset):
        if self.value():
           # Filter by the specified field (field_name))
            filter_kwargs = {f"{self.field_name}__id": self.value()}
            return queryset.filter(**filter_kwargs)
        return queryset


class MemberFilter(UserFilter):
    title = "Members"
    parameter_name = "member"
    field_name = "members"


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "get_members"]
    list_filter = [MemberFilter]
    search_fields = [
        "name",
        "description",
    ]

    def get_members(self, obj):
        return ", ".join([member.username for member in obj.members.all()])

    get_members.short_description = "Members"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "deadline", "is_completed", "team"]
    list_filter = ["deadline", "is_completed", "team__name"]
    search_fields = ["name", "description", "deadline", "is_completed", "team__name"]


class AssigneeFilter(UserFilter):
    title = "Assignees"
    parameter_name = "assignee"
    field_name = "assignees"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "deadline",
        "status_display",
        "created_at",
        "priority",
        "task_type",
        "get_assignees",
        "project",
    ]
    list_filter = [
        "deadline",
        "is_completed",
        "priority",
        "task_type__name",
        AssigneeFilter,
        "project__name",
    ]
    search_fields = [
        "name",
        "description",
        "deadline",
        "created_at",
        "priority",
        "task_type__name",
        "project__name",
    ]

    def get_assignees(self, obj):
        return ", ".join([employee.username for employee in obj.assignees.all()])

    get_assignees.short_description = "Assignees"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("employee", "task", "created_at")
    search_fields = ("content", "employee__username", "task__name")
    list_filter = ("created_at",)