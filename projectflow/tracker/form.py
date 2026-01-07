from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordChangeForm,
    PasswordResetForm,
)
from django.core.exceptions import ValidationError

from tracker.utils import clean_ids_field
from tracker.models import (
    Employee,
    Position,
    Team,
    Project,
    Task,
    Comment,
    PRIORITY_CHOICES,
)

STATUS_CHOICES = [
    ("all", "All statuses"),
    ("active", "Active"),
    ("completed", "Completed"),
]


class RegistrationForm(UserCreationForm):
    position = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Select or enter a new position",
            }
        ),
    )

    class Meta:
        model = Employee
        fields = ["username", "email", "position", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "Email address"}
            ),
            "password1": forms.PasswordInput(
                attrs={"class": "form-input", "placeholder": "Password"}
            ),
            "password2": forms.PasswordInput(
                attrs={"class": "form-input", "placeholder": "Confirm password"}
            ),
        }


    def clean_position(self):
        # Check if the position exists. If not, create a new one
        position_name = self.cleaned_data["position"]
        position, created = Position.objects.get_or_create(name=position_name)
        return position


class CreateTeamForm(forms.ModelForm):
    member_ids = forms.CharField(
        label="Member IDs",
        help_text="Enter user IDs separated by commas",
        widget=forms.TextInput(attrs={"placeholder": "e.g., 1, 2, 3"}),
    )

    class Meta:
        model = Team
        fields = ["name", "description", "member_ids"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["member_ids"].initial = str(self.user.id)

    def clean_member_ids(self):
        return clean_ids_field(self, "member_ids", Employee)

    def save(self, commit=True):
        team = super().save(commit=False)
        if commit:
            team.save()
        members = self.cleaned_data["member_ids"]
        team.members.set(members)
        return team


class CreateProjectForm(forms.ModelForm):
    teams_choice = forms.ModelChoiceField(queryset=Team.objects.none(), label="Teams")

    class Meta:
        model = Project
        fields = ["name", "description", "deadline", "is_completed", "teams_choice"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["teams_choice"].queryset = Team.objects.filter(members=self.user)

    def save(self, commit=True):
        project = super().save(commit=False)
        team_name = self.cleaned_data["teams_choice"]
        project.team = Team.objects.get(name=team_name)
        if commit:
            project.save()
        return project


class CreateTasksForm(forms.ModelForm):
    assignees_ids = forms.CharField(
        label="Assignees IDs",
        help_text="Enter user IDs separated by commas",
        widget=forms.TextInput(attrs={"placeholder": "e.g., 1, 2, 3"}),
    )

    project_choice = forms.ModelChoiceField(queryset=Team.objects.none(), label="Teams")

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "deadline",
            "is_completed",
            "priority",
            "task_type",
            "assignees_ids",
            "project_choice",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        project_queryset = Project.objects.filter(team__members=self.user)
        self.fields["project_choice"].queryset = project_queryset
        if not self.instance.pk:
            self.fields["assignees_ids"].initial = str(self.user.id)

    def clean_assignees_ids(self):
        return clean_ids_field(self, "assignees_ids", Employee)

    def save(self, commit=True):
        task = super().save(commit=False)
        assignees = self.cleaned_data.get("assignees_ids")
        project = self.cleaned_data.get("project_choice")
        task.project = project
        if commit:
            task.save()
            task.assignees.set(assignees)
        return task


class CreateCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]


class AddMemberForm(forms.ModelForm):
    employee_id = forms.IntegerField(label="Employee ID", required=True)

    class Meta:
        model = Employee
        fields = ["employee_id"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.team_id = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get("employee_id")
        team = Team.objects.get(pk=self.team_id)
        if self.user and employee_id == self.user.id:
            raise forms.ValidationError("You are already on the team.")
        if not employee_id:
            raise forms.ValidationError(
                "Employee ID cannot be empty. Please enter a valid ID."
            )
        if team.members.filter(id=employee_id).exists():
            raise forms.ValidationError("Member already in the team")
        if not Employee.objects.filter(id=employee_id).exists():
            raise forms.ValidationError(f"Worker with ID '{employee_id}' does not exist.")
        return employee_id


class UpdateTeamForm(forms.ModelForm):
    member_ids = forms.CharField(
        label="Member IDs",
        help_text="Enter user IDs separated by commas",
        widget=forms.TextInput(attrs={"placeholder": "e.g., 1, 2, 3"}),
    )

    class Meta:
        model = Team
        fields = ["name", "description", "member_ids"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            members = self.instance.members.all()
            self.fields["member_ids"].initial = ", ".join(
                str(employee.id) for employee in members
            )

    def clean_member_ids(self):
        return clean_ids_field(self, "member_ids", Employee)


class UpdateTaskForm(forms.ModelForm):
    assignees_ids = forms.CharField(
        label="Assignees IDs",
        help_text="Enter user IDs separated by commas",
        widget=forms.TextInput(attrs={"placeholder": "e.g., 1, 2, 3"}),
    )

    project_choice = forms.ModelChoiceField(
        queryset=Team.objects.none(), label="Project"
    )

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "deadline",
            "is_completed",
            "priority",
            "task_type",
            "assignees_ids",
            "project_choice",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        project_queryset = Project.objects.filter(team__members=self.user)
        self.fields["project_choice"].queryset = project_queryset

        if self.instance and self.instance.pk:
            assignees = self.instance.assignees.all()
            self.fields["assignees_ids"].initial = ", ".join(
                str(worker.id) for worker in assignees
            )

    def clean_assignees_ids(self):
        return clean_ids_field(self, "assignees_ids", Employee)


class UpdateProjectForm(forms.ModelForm):
    teams_choice = forms.ModelChoiceField(queryset=Team.objects.none(), label="Teams")

    class Meta:
        model = Project
        fields = ["name", "description", "deadline", "is_completed", "teams_choice"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["teams_choice"].queryset = Team.objects.filter(members=self.user)


class StatusFilterForm(forms.Form):
    STATUS_CHOICES = STATUS_CHOICES
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)


class TaskFilterForm(forms.Form):
    PRIORITY_CHOICES.insert(0, (("all", "All priorities")))
    team_choices = lambda: [
        (team.id, team.name) for team in Team.objects.all()
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    team = forms.ChoiceField(choices=team_choices, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["team"].choices = [(("all", "All teams"))] + [
                (team.id, team.name) for team in Team.objects.filter(members=self.user)
            ]


class EmployeeChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Old password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True}
        ),
    )
    new_password1 = forms.CharField(
        label="New password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True}
        ),
    )
    new_password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True}
        ),
    )


class ResetPasswordEmailForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not Employee.objects.filter(email=email).exists():
            raise ValidationError("This email is not registered in the system.")
        return email