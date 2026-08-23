"""Data for the admin dashboard.

Kept as a template tag rather than a custom AdminSite subclass so the standard
Django admin keeps working untouched — this only adds a panel on top of it.
"""

from django import template
from django.db.models import Max
from django.utils import timezone

from portfolio.models import Certification, ContactMessage, Post, Project

register = template.Library()


@register.inclusion_tag("admin/portfolio/dashboard_panel.html")
def dashboard_panel():
    now = timezone.now()

    unread = ContactMessage.objects.filter(is_read=False).count()
    total_messages = ContactMessage.objects.count()

    published_projects = Project.objects.filter(published=True).count()
    draft_projects = Project.objects.filter(published=False).count()

    published_posts = Post.objects.filter(published=True).count()
    draft_posts = Post.objects.filter(published=False).count()

    in_progress = Certification.objects.filter(
        status=Certification.STATUS_IN_PROGRESS
    ).order_by("order")

    last_sync = Project.objects.aggregate(when=Max("gh_synced_at"))["when"]
    sync_stale = bool(last_sync and (now - last_sync).days >= 14)

    return {
        "cards": [
            {
                "label": "Unread messages",
                "value": unread,
                "sub": f"{total_messages} total",
                "url": "/admin/portfolio/contactmessage/?is_read__exact=0",
                "accent": "brand" if unread else "muted",
                "urgent": unread > 0,
            },
            {
                "label": "Projects live",
                "value": published_projects,
                "sub": f"{draft_projects} draft" if draft_projects else "no drafts",
                "url": "/admin/portfolio/project/",
                "accent": "muted",
                "urgent": False,
            },
            {
                "label": "Posts published",
                "value": published_posts,
                "sub": f"{draft_posts} draft" if draft_posts else "no drafts",
                "url": "/admin/portfolio/post/",
                "accent": "muted",
                "urgent": False,
            },
            {
                "label": "Currently learning",
                "value": in_progress.count(),
                "sub": "in progress",
                "url": "/admin/portfolio/certification/",
                "accent": "muted",
                "urgent": False,
            },
        ],
        "recent_messages": ContactMessage.objects.all()[:5],
        "draft_projects": Project.objects.filter(published=False)[:5],
        "in_progress": in_progress[:4],
        "last_sync": last_sync,
        "sync_stale": sync_stale,
        "unread": unread,
    }
