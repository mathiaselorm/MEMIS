import logging
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q

# Configure logging
logger = logging.getLogger(__name__)

def get_object_by_id_or_slug(model, identifier, id_field='id', slug_field='slug'):
    """
    Retrieve a model instance by its ID or slug.
    
    This function tries to determine whether the 'identifier' is intended to be an ID or a slug
    based on its format and contents. It uses regular expressions to check if the identifier
    strictly consists of digits, suggesting an ID, or contains non-digit characters, suggesting a slug.

    :param model: The model class.
    :param identifier: The identifier, which can be either an ID or a slug.
    :param id_field: The field name for the ID (default is 'id').
    :param slug_field: The field name for the slug (default is 'slug').
    :return: The model instance or raise Http404 if not found.
    """
    import re

    # Regex to check if the identifier contains only digits
    if re.match(r'^\d+$', identifier):
        filter_args = {id_field: identifier}
    else:
        filter_args = {slug_field: identifier}
    
    try:
        return model.objects.get(**filter_args)
    except model.DoesNotExist:
        logger.error(f"{model.__name__} not found with {identifier}")
        raise Http404(f"{model.__name__} not found with {identifier}")
