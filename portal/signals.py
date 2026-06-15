from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from portal.models import Site
from portal.services import sync_site_to_yaml


@receiver(post_save, sender=Site)
def site_saved(sender, instance: Site, **kwargs) -> None:
    sync_site_to_yaml(instance)


@receiver(post_delete, sender=Site)
def site_deleted(sender, instance: Site, **kwargs) -> None:
    from src.config_store import delete_site

    try:
        delete_site(instance.slug)
    except KeyError:
        pass
