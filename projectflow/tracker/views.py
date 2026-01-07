from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic, View

from tracker.form import (
    RegistrationForm,
    CreateTeamForm,
    CreateProjectForm,
    CreateTasksForm,
    CreateCommentForm,
    AddMemberForm,
    UpdateTeamForm,
    UpdateTaskForm,
    UpdateProjectForm,
    StatusFilterForm,
    TaskFilterForm,
    EmployeeChangePasswordForm,
    ResetPasswordEmailForm,
)
from tracker.models import Employee, Project, Position, Team, Task, TaskType, Comment


def get_index_page(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


@transaction.atomic
def sign_up(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.position = form.cleaned_data["position"]
            employee.save()
            login(request, employee)
            return redirect("tracker:profile")
    else:
        form = RegistrationForm()
    positions = Position.objects.all()
    return render(
        request, "registration/register.html", {"form": form, "positions": positions}
    )


def pagination(request: HttpRequest, queryset, items_per_page=5):
    """
    Function for pagination.

    Arguments:
        request: HttpRequest - the request object.
        queryset: QuerySet or list - the data to paginate.
        items_per_page: int - number of items per page (default is 5).

    Returns:
        page_obj: pagination object for the template.
    """

    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj


@login_required
def get_profile(request: HttpRequest) -> HttpResponse:
    employee = (
        Employee.objects.select_related("position")
        .prefetch_related("teams", "tasks")
        .only(
            "id",
            "position__id",
            "position__name",
            "position_id",
            "username",
            "email",
            "first_name",
            "last_name",
        )
        .get(pk=request.user.id)
    )

    tasks = employee.tasks.aggregate(
        active_tasks=Count("id", filter=Q(is_completed=False)),
        finished_tasks=Count("id", filter=Q(is_completed=True)),
    )

    projects = Project.objects.filter(team__members=employee).aggregate(
        active_projects=Count("id", filter=Q(is_completed=False)),
        finished_projects=Count("id", filter=Q(is_completed=True)),
    )
    tasks_for_page = employee.tasks.filter(is_completed=False)
    page_obj = pagination(request, tasks_for_page, items_per_page=5)
    context = {
        "employee": employee,
        "active_tasks": tasks["active_tasks"],
        "finished_tasks": tasks["finished_tasks"],
        "active_projects": projects["active_projects"],
        "finished_projects": projects["finished_projects"],
        "page_obj": page_obj,
    }

    return render(request, "profile/profile.html", context=context)


@login_required
def projects_page_view(request: HttpRequest) -> HttpResponse:
    employee = Employee.objects.select_related("position").get(pk=request.user.id)
    employee_team = employee.teams.all()
    employee_projects = (
        Project.objects.filter(team__in=employee_team)
        .select_related("team")
        .prefetch_related("team__members")
    )
    form = StatusFilterForm(request.GET)
    if form.is_valid():
        status = form.cleaned_data.get("status")
        if status and status != "all":
            if status == "completed":
                employee_projects = employee_projects.filter(is_completed=True)
            elif status == "active":
                employee_projects = employee_projects.filter(is_completed=False)
    page_obj = pagination(request, employee_projects, items_per_page=8)
    context = {
        "employee_projects": employee_projects,
        "page_obj": page_obj,
    }
    return render(request, "projects/projects.html", context=context)


@login_required
def teams_page_view(request: HttpRequest) -> HttpResponse:
    employee = (
        Employee.objects.select_related("position")
        .prefetch_related("teams")
        .get(pk=request.user.id)
    )
    employee_teams = employee.teams.all()
    page_obj = pagination(request, employee_teams, 8)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "teams/user_teams.html", context=context)


@login_required
def tasks_page_view(request: HttpRequest) -> HttpResponse:
    employee = Employee.objects.select_related("position").get(pk=request.user.id)

    employee_tasks = (
        Task.objects.filter(project__team__members=employee)
        .select_related("task_type", "project__team")
        .only(
            "id",
            "name",
            "is_completed",
            "deadline",
            "priority",
            "task_type__name",
            "project__team__name",
        )
    )

    form = TaskFilterForm(request.GET, user=request.user)
    if form.is_valid():
        status = form.cleaned_data.get("status")
        priority = form.cleaned_data.get("priority")
        team = form.cleaned_data.get("team")
        if status and status != "all":
            if status == "active":
                employee_tasks = employee_tasks.filter(is_completed=False)
            elif status == "completed":
                employee_tasks = employee_tasks.filter(is_completed=True)

        if priority and priority != "all":
            employee_tasks = employee_tasks.filter(priority=priority)

        if team and team != "all":
            employee_tasks = employee_tasks.filter(project__team_id=team)
    page_obj = pagination(request, employee_tasks, items_per_page=6)
    context = {
        "page_obj": page_obj,
        "form": form,
    }
    return render(request, "tasks/tasks.html", context=context)


@transaction.atomic
@login_required
def create_team_form_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CreateTeamForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("tracker:teams")
    else:
        form = CreateTeamForm(user=request.user)
    return render(request, "profile/create_team_form.html", context={"form": form})


@transaction.atomic
@login_required
def create_project_form_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CreateProjectForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("tracker:projects")
    else:
        form = CreateProjectForm(user=request.user)
    return render(request, "profile/create_project_form.html", context={"form": form})


class CreateTypeView(LoginRequiredMixin, generic.CreateView):
    model = TaskType
    fields = "__all__"
    template_name = "tasks/create_type_form.html"
    success_url = reverse_lazy("tracker:tasks")

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        referer = self.request.POST.get("referer", None)
        if referer:
            return HttpResponseRedirect(referer)
        return response


@transaction.atomic
@login_required
def create_task_form_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CreateTasksForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("tracker:tasks")
    else:
        form = CreateTasksForm(user=request.user)
    return render(request, "profile/create_task_form.html", context={"form": form})


@transaction.atomic
@login_required
def task_details_page_view(request: HttpRequest, pk: int) -> HttpResponse:
    task = (
        Task.objects.select_related("project__team", "task_type")
        .prefetch_related("assignees", "assignees__position", "comments__employee")
        .get(pk=pk)
    )
    if request.method == "POST":
        comment_form = CreateCommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.employee = request.user
            new_comment.task = task
            new_comment.save()
            return redirect("tracker:task-details", pk=task.pk)
    else:
        comment_form = CreateCommentForm()
    context = {
        "task": task,
        "comment_form": comment_form,
    }
    return render(request, "tasks/task_details.html", context)


@login_required
def team_details_page_view(request: HttpRequest, pk: int) -> HttpResponse:
    team = Team.objects.prefetch_related("members__position", "projects").get(pk=pk)
    team_projects = team.projects.all()
    page_obj = pagination(request, team_projects, 4)
    return render(
        request,
        "teams/team_profile.html",
        context={"page_obj": page_obj, "team": team},
    )


class AddNewMemberToTeam(LoginRequiredMixin, generic.FormView):
    form_class = AddMemberForm
    template_name = "forms/add_new_member.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["team"] = self.kwargs["pk"]
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        team = get_object_or_404(
            Team.objects.prefetch_related("members"), pk=self.kwargs["pk"]
        )
        if not team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs["pk"])
        member_id = form.cleaned_data["employee_id"]
        new_member = get_object_or_404(Employee, id=member_id)
        if new_member not in team.members.all():
            team.members.add(new_member)
            team.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tracker:team-details", kwargs={"pk": self.kwargs["pk"]})


class DeleteMemberFromTeam(LoginRequiredMixin, View):
    template_name = "forms/confirm_delete_member.html"

    def dispatch(self, request, *args, **kwargs):
        team = get_object_or_404(
            Team.objects.prefetch_related("members"), pk=kwargs["team_pk"]
        )
        if not team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs["team_pk"])
        member_to_delete = get_object_or_404(Employee, id=kwargs["member_pk"])
        error = kwargs.get("error", None)
        return render(
            request,
            self.template_name,
            {"team": team, "member_to_delete": member_to_delete, "error": error},
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs["team_pk"])
        member_to_delete = get_object_or_404(Employee, id=kwargs["member_pk"])
        if member_to_delete == request.user:
            return self.get(
                request,
                *args,
                **kwargs,
                error="You cannot delete yourself from the team."
            )
        team.members.remove(member_to_delete)
        team.save()
        return redirect("tracker:team-details", pk=team.pk)


class DeleteProjectView(generic.DeleteView):
    model = Project
    template_name = "forms/confirm_delete_project.html"
    success_url = reverse_lazy("tracker:projects")

    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project.objects.prefetch_related("team__members"), pk=kwargs.get("pk")
        )
        if not project.team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        
        return super().delete(request, *args, **kwargs)


@login_required
def project_details_page_view(request, pk: int) -> HttpResponse:
    project = (
        Project.objects.select_related("team").prefetch_related("tasks").get(pk=pk)
    )
    project_tasks = project.tasks.all()
    page_obj = pagination(request, project_tasks, 8)
    return render(
        request,
        "projects/project_details.html",
        context={"project": project, "page_obj": page_obj},
    )


class DeleteTaskView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    template_name = "forms/confirm_delete_task.html"
    success_url = reverse_lazy("tracker:tasks")

    def dispatch(self, request, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.prefetch_related("project"), pk=kwargs.get("pk")
        )
        if not task.project.team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        
        return super().delete(request, *args, **kwargs)


class UpdateProjectView(LoginRequiredMixin, generic.UpdateView):
    model = Project
    form_class = UpdateProjectForm
    template_name = "projects/project_update.html"

    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project.objects.prefetch_related("team__members"), pk=kwargs.get("pk")
        )
        if not project.team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        team_update = form.cleaned_data["teams_choice"]
        project = self.object
        project.team = team_update
        project.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tracker:project-details", kwargs={"pk": self.object.pk})


class DeleteTeamView(LoginRequiredMixin, generic.DeleteView):
    model = Team
    template_name = "forms/confirm_delete_team.html"
    success_url = reverse_lazy("tracker:teams")

    def dispatch(self, request, *args, **kwargs):
        team = get_object_or_404(
            Team.objects.prefetch_related("members"), pk=kwargs.get("pk")
        )
        if not team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        
        return super().delete(request, *args, **kwargs)


class UpdateTeamView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    form_class = UpdateTeamForm
    template_name = "teams/team_update.html"

    def dispatch(self, request, *args, **kwargs):
        team = get_object_or_404(
            Team.objects.prefetch_related("members"), pk=kwargs.get("pk")
        )
        if not team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        workers = form.cleaned_data["member_ids"]
        team = self.object
        team.members.set(workers)
        team.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tracker:team-details", kwargs={"pk": self.object.pk})


class UpdateTaskView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = UpdateTaskForm
    template_name = "tasks/task_update.html"

    def dispatch(self, request, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.prefetch_related("project"), pk=kwargs.get("pk")
        )
        if not task.project.team.members.filter(id=request.user.id).exists():
            return render(request, "permission.html")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        workers = form.cleaned_data["assignees_ids"]
        project = form.cleaned_data["project_choice"]
        task = self.object
        task.assignees.set(workers)
        task.project = project
        task.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tracker:task-details", kwargs={"pk": self.object.pk})


class DeleteCommentView(LoginRequiredMixin, generic.DeleteView):
    model = Comment

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        task_id = self.object.task.pk
        return reverse_lazy("tracker:task-details", kwargs={"pk": task_id})


class EmployeePasswordChange(PasswordChangeView):
    form_class = EmployeeChangePasswordForm
    success_url = reverse_lazy("tracker:password_change_done")
    template_name = "registration/password_change_form.html"

    @transaction.atomic
    def form_valid(self, form):
        return super().form_valid(form)


class PasswordResetEmailFormView(PasswordResetView):
    form_class = ResetPasswordEmailForm
    template_name = "reset_password/password_reset_form.html"
    email_template_name = "reset_password/password_reset_email.html"
    success_url = reverse_lazy("tracker:password_reset_done")

    @transaction.atomic
    def form_valid(self, form):
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Employee
    template_name = "profile/update_profile.html"
    fields = ["username", "email", "first_name", "last_name", "position"]
    success_url = reverse_lazy("tracker:profile")

    def get_queryset(self):
        return Employee.objects.select_related("position").filter(pk=self.request.user.pk)