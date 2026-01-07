from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from projectflow.settings import AUTH_USER_MODEL

PRIORITY_CHOICES = [
    ("urgent", "Urgent"),
    ("high", "High"),
    ("medium", "Medium"),
    ("low", "Low"),
]


class TaskType(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self) -> str:
        return self.name


class Position(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    def __str__(self) -> str:
        return self.name


class Employee(AbstractUser):
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="employees",
        null=True,
    )

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self) -> str:
        return f"{self.username}({self.position})"


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        AUTH_USER_MODEL,
        related_name="teams",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    deadline = models.DateField(db_index=True)
    is_completed = models.BooleanField(default=False, db_index=True)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["deadline"]

    def status_display(self):
        return "Completed" if self.is_completed else "In Progress"

    def __str__(self) -> str:
        return f"{self.name}: ({self.deadline} {self.status_display()})"

    def clean(self):
        super().clean()
        if self.deadline <= timezone.now().date():
            raise ValidationError({"deadline": "The deadline cannot be in the past."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Task(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    deadline = models.DateField(db_index=True)
    is_completed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(
        max_length=30,
        choices=PRIORITY_CHOICES,
        default="U",
        db_index=True,
    )
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assignees = models.ManyToManyField(
        AUTH_USER_MODEL,
        related_name="tasks",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    class Meta:
        ordering = ["deadline"]
        indexes = [
            models.Index(fields=["deadline", "is_completed", "priority"]),
        ]

    def status_display(self):
        return "Completed" if self.is_completed else "In Progress"

    def __str__(self) -> str:
        return f"{self.name} ({self.status_display()})"

    def clean(self):
        super().clean()
        if self.deadline <= timezone.now().date():
            raise ValidationError({"deadline": "The deadline cannot be in the past."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Comment(models.Model):
    employee = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Comment by {self.employee} on {self.task} ({self.created_at})"