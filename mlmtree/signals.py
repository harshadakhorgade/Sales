from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MLMTree
from users.models import CustomUser

@receiver(post_save, sender=CustomUser)
def create_mlm_tree(sender, instance, created, **kwargs):
    """Automatically create MLMTree node when a user is created."""
    if created and not MLMTree.objects.filter(user=instance).exists():
        parent_tree = None

        if instance.parent_node:
            try:
                parent_tree = MLMTree.objects.get(user=instance.parent_node)
            except MLMTree.DoesNotExist:
                pass

        MLMTree.objects.create(user=instance, parent=parent_tree)
