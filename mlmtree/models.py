from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ Fix: Avoid circular import

class MLMTree(MPTTModel):
    """Model to store MLM hierarchical structure using MPTT."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mlm_tree")
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['user']

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.unique_id})"

    def get_downline(self):
        """Returns all users under this user in the hierarchy."""
        return self.get_descendants()

    def get_upline(self):
        """Returns the chain of sponsors above this user."""
        return self.get_ancestors()
