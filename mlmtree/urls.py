from django.urls import path
from .views import mlm_tree_view, get_mlm_tree

urlpatterns = [
    path("tree-view/", mlm_tree_view, name="mlm_tree_view"),  # ✅ Fix: Correct URL path
    path("api/tree/", get_mlm_tree, name="get_mlm_tree"),
]
