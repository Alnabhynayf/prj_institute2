from django.core.cache import cache
from dean.models import *

def notifications_context(request):
    context = {}
    if request.user.is_authenticated and request.user.is_student:
        cache_key = f"student_{request.user.student.id}_notifications"
        notifications = cache.get(cache_key)
        
        if notifications is None:
            notifications = Announcement.objects.filter(
                # models.Q(is_public=True) |
                models.Q(student=request.user.student) |
                models.Q(group__statuses__application__student=request.user.student)
            ).order_by('-created_at')[:5]
            cache.set(cache_key, notifications, 300)  # Cache for 5 minutes
        
        context['notifications'] = notifications
        context['unread_count'] = Announcement.objects.filter(
            # models.Q(is_public=True) |
            models.Q(student=request.user.student) |
            models.Q(group__statuses__application__student=request.user.student),
            is_read=False
        ).count()
    
    return context


# في context_processors.py
# from .models import Announcement

# def public_announcements_processor(request):
#     public_unread_count = Announcement.objects.filter(
#         is_public=True,
#         is_read=False
#     ).count()
    
#     return {
#         'public_unread_count': public_unread_count,
#         'public_announcements': Announcement.objects.filter(
#             is_public=True
#         ).order_by('-created_at')[:3]  # آخر 3 إعلانات عامة
#     }