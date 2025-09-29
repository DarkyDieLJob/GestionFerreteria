# Expose models to Django by importing from adapters.models
# This ensures makemigrations and migrate discover them reliably.
from .adapters.models import *  # noqa: F401,F403
