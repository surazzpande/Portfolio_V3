from io import StringIO

from django.conf import settings
from django.contrib import admin, messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    Certification,
    ContactMessage,
    Education,
    EducationBullet,
    Experience,
    ExperienceBullet,
    ExploringArea,
    ExploringTopic,
    Post,
    Profile,
    Project,
    Skill,
    SkillCategory,
    Stat,
    Tag,
)

admin.site.site_header = "Portfolio admin"
admin.site.site_title = "Portfolio admin"
admin.site.index_title = ""


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("full_name", "initials", "brand_name", "role_title")}),
        ("Hero section", {"fields": ("availability_note", "hero_intro", "exploring_tags", "resume")}),
        ("About section", {"fields": ("about_heading", "about_body")}),
        ("Contact & links", {"fields": ("email", "phone", "location", "github_url", "linkedin_url")}),
        ("SEO", {"fields": ("seo_description",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        # Only ever one profile row.
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ("value", "label", "order")
    list_editable = ("order",)


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "skill_count", "order")
    list_editable = ("order",)
    inlines = [SkillInline]

    @admin.display(description="Skills")
    def skill_count(self, obj):
        return obj.skills.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "project_count")
    search_fields = ("name",)

    @admin.display(description="Used by projects")
    def project_count(self, obj):
        return obj.projects.count()


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "featured", "published", "order", "tag_list", "github_summary")
    list_editable = ("featured", "published", "order")
    list_filter = ("published", "featured", "tags")
    search_fields = ("title", "subtitle", "problem", "solution")
    filter_horizontal = ("tags",)
    readonly_fields = ("gh_stars", "gh_forks", "gh_language", "gh_pushed_at", "gh_synced_at")
    fieldsets = (
        (None, {"fields": ("title", "subtitle")}),
        ("The story", {"fields": ("problem", "solution")}),
        ("Tech & links", {"fields": ("tags", "code_url", "live_url")}),
        ("Display", {"fields": ("featured", "published", "order")}),
        (
            "GitHub stats",
            {
                "fields": ("gh_stars", "gh_forks", "gh_language", "gh_pushed_at", "gh_synced_at"),
                "description": (
                    "Filled in automatically from the repository in 'code url'. "
                    "Refresh with: <code>python manage.py refresh_github</code>"
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Tech")
    def tag_list(self, obj):
        return ", ".join(t.name for t in obj.tags.all()[:5])

    @admin.display(description="GitHub")
    def github_summary(self, obj):
        if not obj.has_github_stats:
            return "—"
        parts = [obj.gh_language or "n/a"]
        if obj.gh_stars:
            parts.append(f"★ {obj.gh_stars}")
        return " · ".join(parts)

    # --- One-click GitHub sync ------------------------------------------------

    change_list_template = "admin/portfolio/project/change_list.html"

    def get_urls(self):
        return [
            path(
                "sync-github/",
                self.admin_site.admin_view(self.sync_github),
                name="portfolio_project_sync_github",
            ),
        ] + super().get_urls()

    def sync_github(self, request):
        """Pull new repositories from the accounts in GITHUB_USERNAMES."""
        usernames = [u.strip() for u in settings.GITHUB_USERNAMES if u.strip()]
        redirect_to = reverse("admin:portfolio_project_changelist")

        if not usernames:
            self.message_user(
                request,
                "No GitHub usernames configured. Set GITHUB_USERNAMES in your environment.",
                level=messages.WARNING,
            )
            return HttpResponseRedirect(redirect_to)

        before = Project.objects.count()
        output = StringIO()
        try:
            call_command("import_github", *usernames, stdout=output, stderr=output)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self.message_user(request, f"Sync failed: {exc}", level=messages.ERROR)
            return HttpResponseRedirect(redirect_to)

        added = Project.objects.count() - before
        if added:
            self.message_user(
                request,
                f"Synced {', '.join(usernames)} — {added} new project(s) added as drafts. "
                "Write a problem and solution for the ones worth showing, then tick "
                "'published'.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"Synced {', '.join(usernames)} — no new repositories. "
                "Existing stats refreshed.",
                level=messages.INFO,
            )
        return HttpResponseRedirect(redirect_to)


class ExperienceBulletInline(admin.TabularInline):
    model = ExperienceBullet
    extra = 1


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("role", "organisation", "date_range", "is_technical", "published", "order")
    list_editable = ("is_technical", "published", "order")
    list_filter = ("is_technical", "published")
    filter_horizontal = ("tags",)
    inlines = [ExperienceBulletInline]


class EducationBulletInline(admin.TabularInline):
    model = EducationBullet
    extra = 1


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("qualification", "institution", "date_range", "grade", "order")
    list_editable = ("order",)
    inlines = [EducationBulletInline]


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    """Keep this updated as you study — status and progress are editable in the list."""

    list_display = (
        "name", "issuer", "kind", "status", "progress_bar",
        "completed_on", "published", "order",
    )
    list_editable = ("status", "published", "order")
    list_filter = ("status", "kind", "published")
    search_fields = ("name", "issuer", "credential_id")
    fieldsets = (
        (None, {"fields": ("name", "issuer", "kind")}),
        (
            "Progress",
            {
                "fields": ("status", "progress", "completed_on", "expires_on"),
                "description": (
                    "Set status to <b>In progress</b> and give a percentage while you are "
                    "working through it. Switch to <b>Completed</b> and fill in the date "
                    "when you finish."
                ),
            },
        ),
        (
            "Proof",
            {
                "fields": ("credential_url", "credential_id", "note"),
                "description": (
                    "A credential link lets people verify it. Use <b>note</b> to be precise "
                    "about what something is — e.g. 'self-study course, not an exam "
                    "certification'."
                ),
            },
        ),
        ("Display", {"fields": ("published", "order")}),
    )

    @admin.display(description="Progress")
    def progress_bar(self, obj):
        if obj.status != Certification.STATUS_IN_PROGRESS:
            return "—"
        pct = obj.clamped_progress
        return format_html(
            '<div style="background:#eee;border-radius:6px;width:110px;height:12px;'
            'display:inline-block;overflow:hidden;vertical-align:middle">'
            '<div style="background:#8289FF;height:100%;width:{}%"></div></div> {}%',
            pct, pct,
        )


class ExploringTopicInline(admin.TabularInline):
    model = ExploringTopic
    extra = 1


@admin.register(ExploringArea)
class ExploringAreaAdmin(admin.ModelAdmin):
    list_display = ("title", "status_label", "order")
    list_editable = ("order",)
    inlines = [ExploringTopicInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email_link", "short_message", "received_at", "is_read")
    list_filter = ("is_read", "received_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "received_at")
    date_hierarchy = "received_at"
    actions = ["mark_read", "mark_unread"]

    @admin.display(description="Email")
    def email_link(self, obj):
        return format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)

    @admin.display(description="Message")
    def short_message(self, obj):
        return obj.message[:70] + ("…" if len(obj.message) > 70 else "")

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected as unread")
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "published_at", "reading_time_display")
    list_editable = ("published",)
    list_filter = ("published", "tags", "published_at")
    search_fields = ("title", "excerpt", "body")
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt")}),
        (
            "Content",
            {
                "fields": ("body",),
                "description": (
                    "Blank line between paragraphs. "
                    "<code>## Heading</code> · <code>- bullet</code> · "
                    "<code>**bold**</code> · <code>`code`</code> · "
                    "<code>[link](https://…)</code> · triple backticks for a code block."
                ),
            },
        ),
        ("Publishing", {"fields": ("tags", "published", "published_at")}),
    )

    @admin.display(description="Length")
    def reading_time_display(self, obj):
        return f"{obj.reading_time} min"
