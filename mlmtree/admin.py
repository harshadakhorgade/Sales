from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from .models import MLMTree

class MLMTreeAdmin(MPTTModelAdmin):
    mptt_level_indent = 20
    list_display = ("user", "get_parent", "get_sponsor", "view_tree_link")  # ✅ Added get_sponsor

    def get_parent(self, obj):
        """Returns the parent placement (who the user is placed under in the tree)."""
        return obj.parent.user.first_name if obj.parent else "Company"
    get_parent.short_description = "Placed Under"

    def get_sponsor(self, obj):
        """Returns the parent sponsor (who referred the user)."""
        return obj.user.parent_sponsor.first_name if obj.user.parent_sponsor else "N/A"
    get_sponsor.short_description = "Referred By"

    def view_tree_link(self, obj):
        """Provides a clickable link to view the MLM tree."""
        return format_html('<a href="/mlmtree/tree-view/" target="_blank">🔍 View MLM Tree</a>')
    view_tree_link.short_description = "MLM Tree"

admin.site.register(MLMTree, MLMTreeAdmin)
