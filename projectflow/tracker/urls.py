from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordChangeDoneView,
)
from django.urls import path, reverse_lazy

from tracker.views import (
    get_index_page,
    get_profile,
    sign_up,
    projects_page_view,
    teams_page_view,
    tasks_page_view,
    create_team_form_view,
    create_project_form_view,
    create_task_form_view,
    CreateTypeView,
    task_details_page_view,
    team_details_page_view,
    project_details_page_view,
    UpdateProjectView,
    UpdateTeamView,
    AddNewMemberToTeam,
    DeleteMemberFromTeam,
    DeleteProjectView,
    DeleteTaskView,
    DeleteTeamView,
    UpdateTaskView,
    DeleteCommentView,
    EmployeePasswordChange,
    PasswordResetEmailFormView, ProfileUpdateView,
)

urlpatterns = [
    path("", get_index_page, name="index"),
    path("profile/", get_profile, name="profile"),
    path("profile/update/<int:pk>/", ProfileUpdateView.as_view(), name="profile-update"),
    path("register/", sign_up, name="register"),
    path("password-change/", EmployeePasswordChange.as_view(), name="password_change"),
    path(
        "password-change/done/",
        PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "password-reset/", PasswordResetEmailFormView.as_view(), name="reset_password"
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(
            template_name="reset_password/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="reset_password/password_reset_confirm.html",
            success_url=reverse_lazy("tracker:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset-password/complete/",
        PasswordResetCompleteView.as_view(
            template_name="reset_password/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("profile/projects/", projects_page_view, name="projects"),
    path("profile/create-project/", create_project_form_view, name="create-project"),
    path(
        "profile/project/delete/<int:pk>/",
        DeleteProjectView.as_view(),
        name="delete-project",
    ),
    path(
        "profile/project/<int:pk>/", project_details_page_view, name="project-details"
    ),
    path(
        "profile/project/update/<int:pk>/",
        UpdateProjectView.as_view(),
        name="project-update",
    ),
    path("profile/teams/", teams_page_view, name="teams"),
    path("profile/create-team/", create_team_form_view, name="create-team"),
    path("profile/team/<int:pk>/", team_details_page_view, name="team-details"),
    path(
        "profile/team/<int:pk>/add-member/",
        AddNewMemberToTeam.as_view(),
        name="add-member",
    ),
    path(
        "profile/team/<int:team_pk>/delete/<int:member_pk>/",
        DeleteMemberFromTeam.as_view(),
        name="delete-member",
    ),
    path("profile/team/delete/<int:pk>/", DeleteTeamView.as_view(), name="team-delete"),
    path("profile/team/update/<int:pk>/", UpdateTeamView.as_view(), name="team-update"),
    path("profile/tasks/", tasks_page_view, name="tasks"),
    path("profile/create-task/", create_task_form_view, name="create-task"),
    path("profile/create-type/", CreateTypeView.as_view(), name="create-type"),
    path("profile/task/<int:pk>/", task_details_page_view, name="task-details"),
    path("profile/task/delete/<int:pk>/", DeleteTaskView.as_view(), name="task-delete"),
    path("profile/task/update/<int:pk>/", UpdateTaskView.as_view(), name="task-update"),
    path(
        "profile/comment/<int:pk>/",
        DeleteCommentView.as_view(),
        name="comment-delete",
    ),
]

app_name = "tracker"