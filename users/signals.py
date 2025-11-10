from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from collections import deque
from users.models import CustomUser

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create Profile for new user,
    assign parent_sponsor if not given,
    find the first available parent_node in MLM tree (max 5 children),
    and create MLMTree nodes.
    """
    Profile = apps.get_model('users', 'Profile')
    MLMTree = apps.get_model('mlmtree', 'MLMTree')

    if not created:
        return

    # Create Profile
    Profile.objects.create(user=instance)

    # If superuser (root/admin)
    if instance.is_superuser:
        instance.parent_sponsor = None
        instance.parent_node = None
        instance.save()
        MLMTree.objects.create(user=instance, parent=None)
        return

    # Set parent_sponsor if not already set
    if not instance.parent_sponsor:
        root_user = CustomUser.objects.filter(is_superuser=True).first()
        instance.parent_sponsor = root_user

    # BFS traversal to assign parent_node with < 5 children
    # 🔁 Assign parent_node as parent_sponsor if sponsor has < 5 children
    if not instance.parent_node and instance.parent_sponsor:
        if instance.parent_sponsor.child_nodes.count() < 5:
            instance.parent_node = instance.parent_sponsor
        else:
            # Optional fallback: find another spot via BFS if sponsor is full
            root_user = CustomUser.objects.filter(is_superuser=True).first()
            queue = deque([instance.parent_sponsor])

            while queue:
                current = queue.popleft()
                if current.child_nodes.count() < 5:
                    instance.parent_node = current
                    break
                queue.extend(current.child_nodes.all())

    instance.save()

    # Ensure parent_node has MLMTree record
    if instance.parent_node and not hasattr(instance.parent_node, 'mlm_tree'):
        MLMTree.objects.create(
            user=instance.parent_node,
            parent=instance.parent_node.parent_node.mlm_tree if instance.parent_node.parent_node else None
        )

    # Create MLMTree node for new user
    MLMTree.objects.create(
        user=instance,
        parent=instance.parent_node.mlm_tree if instance.parent_node else None
    )
