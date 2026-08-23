import re

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Singleton(models.Model):
    """Base for models that should only ever have one row."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Profile(Singleton):
    """Everything in the hero, about section and contact block."""

    full_name = models.CharField(max_length=120, default="Suraj Pandey")
    initials = models.CharField(max_length=4, default="SP", help_text="Shown in the nav logo badge.")
    brand_name = models.CharField(max_length=60, default="suraj.dev", help_text="Wordmark next to the badge.")
    role_title = models.CharField(
        max_length=200,
        default="Software Engineer — Python · Django · React · TypeScript",
    )
    availability_note = models.CharField(
        max_length=140,
        blank=True,
        default="Open to UK roles · Graduate visa",
        help_text="Small pill above your name. Leave blank to hide it.",
    )
    hero_intro = models.TextField(default="", help_text="One or two sentences under your name.")
    about_heading = models.CharField(max_length=140, default="A developer who ships, end to end")
    about_body = models.TextField(
        blank=True,
        default="",
        help_text="Separate paragraphs with a blank line.",
    )
    exploring_tags = models.CharField(
        max_length=200,
        blank=True,
        default="AI/ML · Cybersecurity · DevOps",
        help_text="Small text under the 'Exploring' link in the hero.",
    )
    email = models.EmailField(default="surajpande20554@gmail.com")
    phone = models.CharField(max_length=40, blank=True, default="+44 7587 546294")
    location = models.CharField(max_length=120, blank=True, default="London, UK")
    github_url = models.URLField(blank=True, default="https://github.com/surazzpande")
    linkedin_url = models.URLField(blank=True, default="https://linkedin.com/in/surajpande-dev")
    resume = models.FileField(
        upload_to="resume/",
        blank=True,
        null=True,
        help_text="Upload your CV as a PDF — the 'Download Resume' button links to it.",
    )
    seo_description = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        verbose_name = "Profile & contact details"
        verbose_name_plural = "Profile & contact details"

    def __str__(self):
        return self.full_name

    @property
    def about_paragraphs(self):
        return [p.strip() for p in self.about_body.split("\n\n") if p.strip()]


class Stat(models.Model):
    """The four numbers in the About section."""

    value = models.CharField(max_length=30, help_text="e.g. '3+' or 'Distinction'")
    label = models.CharField(max_length=60, help_text="e.g. 'YEARS EXPERIENCE'")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.value} — {self.label}"


class SkillCategory(models.Model):
    name = models.CharField(max_length=80, help_text="e.g. 'Backend'")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "Skill categories"

    def __str__(self):
        return self.name


class Skill(models.Model):
    category = models.ForeignKey(SkillCategory, related_name="skills", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Technology tags, reused across projects and used for the filter bar."""

    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower().replace(" ", "-").replace("/", "-")


class Project(models.Model):
    title = models.CharField(max_length=140)
    subtitle = models.CharField(max_length=300, blank=True, help_text="The line under the title.")
    problem = models.TextField(blank=True, help_text="Shown after the PROBLEM label.")
    solution = models.TextField(blank=True, help_text="Shown after the SOLUTION label.")
    tags = models.ManyToManyField(Tag, blank=True, related_name="projects")
    code_url = models.URLField(blank=True, help_text="Link to the repository.")
    live_url = models.URLField(blank=True, help_text="Optional link to a live demo.")
    featured = models.BooleanField(default=False, help_text="Featured projects show a highlight border.")
    published = models.BooleanField(default=True, help_text="Untick to hide without deleting.")
    order = models.PositiveIntegerField(default=0)

    # --- Populated automatically by `manage.py refresh_github` ---
    gh_stars = models.PositiveIntegerField(null=True, blank=True, verbose_name="GitHub stars")
    gh_forks = models.PositiveIntegerField(null=True, blank=True, verbose_name="GitHub forks")
    gh_language = models.CharField(max_length=60, blank=True, verbose_name="Main language")
    gh_pushed_at = models.DateTimeField(null=True, blank=True, verbose_name="Last commit")
    gh_synced_at = models.DateTimeField(null=True, blank=True, verbose_name="Stats last refreshed")

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def tag_slugs(self):
        return " ".join(t.slug for t in self.tags.all())

    @property
    def github_repo(self):
        """'owner/name' parsed from code_url, or None if it isn't a GitHub URL."""
        if not self.code_url:
            return None
        match = re.search(r"github\.com/([^/]+)/([^/?#]+)", self.code_url)
        if not match:
            return None
        return f"{match.group(1)}/{match.group(2).removesuffix('.git')}"

    @property
    def has_github_stats(self):
        return self.gh_synced_at is not None


class Experience(models.Model):
    role = models.CharField(max_length=140)
    organisation = models.CharField(max_length=180)
    date_range = models.CharField(max_length=80, help_text="e.g. 'Aug 2026 – Present'")
    location = models.CharField(max_length=80, blank=True, help_text="e.g. 'UK'")
    is_technical = models.BooleanField(
        default=False,
        help_text="Tick for software roles — these are highlighted in the timeline.",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="experiences")
    published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="0 = top of the timeline.")

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "Experience"

    def __str__(self):
        return f"{self.role} — {self.organisation}"


class ExperienceBullet(models.Model):
    experience = models.ForeignKey(Experience, related_name="bullets", on_delete=models.CASCADE)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Education(models.Model):
    qualification = models.CharField(max_length=180)
    institution = models.CharField(max_length=180)
    date_range = models.CharField(max_length=80)
    grade = models.CharField(max_length=60, blank=True, help_text="e.g. 'Distinction'")
    published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "Education"

    def __str__(self):
        return self.qualification


class EducationBullet(models.Model):
    education = models.ForeignKey(Education, related_name="bullets", on_delete=models.CASCADE)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Certification(models.Model):
    """Certifications, courses and anything you're currently studying.

    Keep this updated as you go — set something to 'In progress' with a
    percentage while you work through it, then switch it to 'Completed'.
    """

    KIND_CERTIFICATION = "certification"
    KIND_COURSE = "course"
    KIND_DEGREE = "degree"
    KIND_OTHER = "other"
    KIND_CHOICES = [
        (KIND_CERTIFICATION, "Certification (passed an exam)"),
        (KIND_COURSE, "Course / training"),
        (KIND_DEGREE, "Degree or diploma"),
        (KIND_OTHER, "Other"),
    ]

    STATUS_COMPLETED = "completed"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_PLANNED = "planned"
    STATUS_CHOICES = [
        (STATUS_COMPLETED, "Completed"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_PLANNED, "Planned"),
    ]

    name = models.CharField(max_length=180)
    issuer = models.CharField(max_length=140, blank=True, help_text="Who actually issued it.")
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        default=KIND_COURSE,
        help_text="Be accurate: only pick 'Certification' if you sat and passed the exam.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    progress = models.PositiveSmallIntegerField(
        default=0,
        help_text="0–100. Only shown while the status is 'In progress'.",
    )
    completed_on = models.DateField(
        null=True,
        blank=True,
        help_text="When you finished it. Leave blank if still in progress.",
    )
    expires_on = models.DateField(
        null=True,
        blank=True,
        help_text="Only if the certification expires.",
    )
    credential_url = models.URLField(
        blank=True,
        help_text="Link to the certificate or credential page, so it can be verified.",
    )
    credential_id = models.CharField(max_length=120, blank=True)
    note = models.CharField(
        max_length=160,
        blank=True,
        help_text="Optional qualifier, e.g. 'self-study course, not an exam certification'.",
    )
    published = models.BooleanField(default=True, help_text="Untick to hide without deleting.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    @property
    def is_in_progress(self):
        return self.status == self.STATUS_IN_PROGRESS

    @property
    def is_expired(self):
        from django.utils import timezone as tz

        return bool(self.expires_on and self.expires_on < tz.now().date())

    @property
    def clamped_progress(self):
        return max(0, min(100, self.progress))


class ExploringArea(models.Model):
    """The 'Where I'm heading next' cards."""

    title = models.CharField(max_length=120)
    grounding = models.TextField(help_text="The line explaining what real work this builds on.")
    status_label = models.CharField(max_length=60, default="CURRENTLY LEARNING")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class ExploringTopic(models.Model):
    area = models.ForeignKey(ExploringArea, related_name="topics", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Post(models.Model):
    """A blog post — write-ups of what you build."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Leave blank and it is generated from the title.",
    )
    excerpt = models.TextField(
        max_length=400,
        help_text="One or two sentences shown on the blog listing and in search results.",
    )
    body = models.TextField(
        help_text=(
            "Separate paragraphs with a blank line. "
            "Start a line with '## ' for a subheading, '- ' for a bullet, "
            "and wrap code in a line of ``` above and below."
        )
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    published = models.BooleanField(
        default=False,
        help_text="Drafts are only visible to you while logged into the admin.",
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        help_text="Used for ordering and shown on the post.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "post"
            slug, n = base, 2
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("post_detail", args=[self.slug])

    @property
    def reading_time(self):
        words = len(self.body.split())
        return max(1, round(words / 200))
