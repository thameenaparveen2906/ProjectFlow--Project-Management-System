from django import forms


def clean_ids_field(self, field_name, model_class):
    """
    Universal method to clean and validate IDs in a comma-separated string field.

    :param field_name: The name of the field to clean (e.g., 'assignees_ids').
    :param model_class: The model class to check the IDs against (e.g., Employee).
    :return: A queryset of valid objects matching the IDs.
    """
    data_ids = self.cleaned_data.get(field_name)

    if not data_ids:
        raise forms.ValidationError(
            f"{field_name.replace('_', ' ').capitalize()} "
            f"cannot be empty. Please enter valid IDs."
        )
    ids = [id.strip() for id in data_ids.split(",") if id.strip()]
    if not ids:
        raise forms.ValidationError(
            f"{field_name.replace('_', ' ').capitalize()} "
            f"cannot be empty. Please enter valid IDs."
        )
    try:
        ids = [int(id) for id in ids]
    except ValueError:
        raise forms.ValidationError("All IDs must be valid integers.")
    objects = model_class.objects.filter(pk__in=ids)
    if len(objects) != len(ids):
        raise forms.ValidationError(
            f"One or more {field_name.replace('_', ' ')} "
            f"IDs are invalid. Please check the IDs."
        )
    return objects


def clean_project_name(self, field_name, model_class):
    """
    Universal method to clean and validate project_name.

    :param field_name: The name of the field to clean (e.g., 'project_name').
    :param model_class: The model class to check the IDs against (e.g., Employee).
    :return: A queryset of valid objects matching the IDs.
    """
    project_name = self.cleaned_data.get(field_name)
    if not project_name:
        raise forms.ValidationError(
            "Project name cannot be empty. Please enter a valid name."
        )
    try:
        project = model_class.objects.get(name=project_name)
        return project
    except model_class.DoesNotExist:
        raise forms.ValidationError(
            f"Project with name '{project_name}' does not exist."
        )