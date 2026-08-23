from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .mail import notify_new_message
from .models import (
    Certification,
    Education,
    Experience,
    ExploringArea,
    Post,
    Profile,
    Project,
    SkillCategory,
    Stat,
    Tag,
)


def _visible_posts(request):
    """Published posts for everyone; staff also see drafts."""
    posts = Post.objects.prefetch_related("tags")
    if request.user.is_authenticated and request.user.is_staff:
        return posts
    return posts.filter(published=True)


def home(request):
    profile = Profile.load()

    context = {
        "profile": profile,
        "stats": Stat.objects.all(),
        "skill_categories": SkillCategory.objects.prefetch_related("skills"),
        "projects": Project.objects.filter(published=True).prefetch_related("tags"),
        "filter_tags": (
            Tag.objects.filter(projects__published=True)
            .annotate(n=Count("projects"))
            .order_by("name")
            .distinct()
        ),
        "experiences": Experience.objects.filter(published=True).prefetch_related("bullets", "tags"),
        "education": Education.objects.filter(published=True).prefetch_related("bullets"),
        "certifications": Certification.objects.all(),
        "exploring": ExploringArea.objects.prefetch_related("topics"),
        "recent_posts": _visible_posts(request)[:3],
        "form": ContactForm(),
    }
    return render(request, "portfolio/index.html", context)


def post_list(request):
    posts = _visible_posts(request)

    tag_slug = request.GET.get("tag")
    active_tag = None
    if tag_slug:
        for tag in Tag.objects.filter(posts__isnull=False).distinct():
            if tag.slug == tag_slug:
                active_tag = tag
                break
        posts = posts.filter(tags=active_tag) if active_tag else posts.none()

    return render(
        request,
        "portfolio/post_list.html",
        {
            "profile": Profile.load(),
            "posts": posts,
            "post_tags": Tag.objects.filter(posts__published=True).distinct().order_by("name"),
            "active_tag": active_tag,
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(_visible_posts(request), slug=slug)
    related = (
        _visible_posts(request)
        .filter(tags__in=post.tags.all())
        .exclude(pk=post.pk)
        .distinct()[:2]
    )
    return render(
        request,
        "portfolio/post_detail.html",
        {"profile": Profile.load(), "post": post, "related": related},
    )


@require_POST
def contact(request):
    """Handle the contact form. Responds with JSON to fetch(), HTML otherwise."""
    form = ContactForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if form.is_valid():
        message = form.save()
        # Never let a mail failure lose the message — it is already saved.
        notify_new_message(message)

        if is_ajax:
            return JsonResponse({"ok": True, "message": "Thanks — your message has been sent."})
        messages.success(request, "Thanks — your message has been sent.")
        return redirect("/#contact")

    if is_ajax:
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    messages.error(request, "Please check the form and try again.")
    return redirect("/#contact")
