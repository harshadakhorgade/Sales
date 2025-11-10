from django.shortcuts import render
from django.http import JsonResponse
from .models import MLMTree

def mlm_tree_view(request):
    """Renders the HTML page for MLM tree visualization in Django Admin."""
    return render(request, "admin/mlm_tree_view.html")

def get_mlm_tree(request):
    """Returns the MLM tree as JSON for visualization."""
    def serialize_tree(node):
        return {
            "id": node.user.id,
            "name": f"{node.user.first_name} {node.user.last_name}",
            "children": [serialize_tree(child) for child in node.get_children()]
        }

    root_nodes = MLMTree.objects.filter(parent=None)
    tree_data = [serialize_tree(node) for node in root_nodes]
    return JsonResponse(tree_data, safe=False)
