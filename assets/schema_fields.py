from rest_framework import serializers

class StatusModelChoiceField(serializers.ChoiceField):
    """
    A custom ChoiceField to use for StatusModel status fields, avoiding direct serialization of Choices.
    """
    def __init__(self, *args, **kwargs):
        # Define choices manually to avoid using Choices from model-utils
        choices = [('draft', 'Draft'), ('published', 'Published')]
        super().__init__(choices=choices, *args, **kwargs)
