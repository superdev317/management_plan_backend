from rest_framework import permissions

from .models import Project


class IsProjectOwner(permissions.BasePermission):
    """
    Check if current user is project owner
    """
    def has_permission(self, request, view):
        return Project.objects.filter(pk=view.kwargs['pk'],
                                      owner=request.user).exists()


class IsMilestoneOwner(permissions.BasePermission):
    """
    Check if current user is milestone owner
    """
    def has_object_permission(self, request, view, obj):
        return obj.project.owner == request.user
