import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uniform_project.settings")
django.setup()


@pytest.fixture
def django_db_setup():
    """Permite usar @pytest.mark.django_db sin instalar pytest-django."""
    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, verbosity=0)
