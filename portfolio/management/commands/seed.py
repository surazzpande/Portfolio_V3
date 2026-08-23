"""Load the portfolio content.

Everything here comes from Suraj Pandey's CV. Run with --reset to wipe the
content tables first (contact messages and users are never touched).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from portfolio.models import (
    Certification,
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

HERO_INTRO = (
    "MSc Software Engineering (Distinction) with three years of commercial development "
    "experience. I design data models and REST APIs, then ship the responsive interfaces "
    "on top. Open to UK software roles."
)

ABOUT_BODY = """I'm a software engineer with an MSc in Software Engineering (Distinction) from the University of West London and three years of commercial development experience.

At Pragmatic Technology in Nepal (2020–2023) I worked across the stack — designing Django data models and REST APIs, then building the React interfaces on top. I care about clean architecture, readable code and shipping features that hold up in production.

Since finishing my MSc I've been working in the UK while continuing to build software, and I'm now focused on full-stack and backend engineering roles. I hold the UK Graduate visa, which gives me full and unrestricted right to work."""

STATS = [
    ("3+", "YEARS EXPERIENCE"),
    ("8+", "PROJECTS SHIPPED"),
    ("12+", "CORE TECHNOLOGIES"),
    ("Distinction", "MSC GRADE"),
]

SKILLS = [
    ("Frontend", ["HTML5", "CSS3", "JavaScript", "TypeScript", "React", "Tailwind CSS"]),
    ("Backend", ["Python", "Django", "Django REST Framework", "REST APIs"]),
    ("Database", ["PostgreSQL", "MySQL", "SQLite"]),
    ("Cloud & DevOps", ["Microsoft Azure (foundations)", "Git", "CI/CD basics"]),
    ("Tools", ["Git", "GitHub", "Postman", "VS Code", "Linux"]),
    ("AI & Emerging", ["OpenAI / LLM APIs", "LangChain", "RAG pipelines", "Prompt engineering"]),
]

PROJECTS = [
    {
        "title": "WalkNex — AI E-commerce Chatbot",
        "subtitle": "MSc dissertation: an AI assistant that answers product and support queries for an e-commerce store.",
        "problem": "Shoppers abandon stores when they cannot quickly find answers about products and orders.",
        "solution": "An LLM-backed chatbot with a retrieval layer over the catalogue, served by a Django API and a React UI.",
        "tags": ["Python", "Django", "React", "LLM/GPT", "LangChain", "Weaviate"],
        "code_url": "https://github.com/Pande-Suraj/Walknex",
        "featured": True,
    },
    {
        "title": "IMS-Connect",
        "subtitle": "A support and messaging hub with ticketing, role-based access and real-time chat.",
        "problem": "Teams lose context when support requests and internal comms live in separate tools.",
        "solution": "A unified hub combining tickets, chat and admin analytics in one React + Django app.",
        "tags": ["React", "Django", "Firebase", "Tailwind"],
        "code_url": "https://github.com/surazzpande/Ims_Connect",
    },
    {
        "title": "GreenFuture",
        "subtitle": "Sustainability idea-management platform with voting, rewards and regional dashboards.",
        "problem": "Good sustainability ideas inside an organisation get lost with nowhere to submit or rank them.",
        "solution": "A React and Firebase platform where staff submit and vote on ideas, with admin and regional dashboards tracking what gets adopted.",
        "tags": ["React", "Firebase", "JavaScript"],
        "code_url": "https://github.com/surazzpande/GreenFuture",
    },
    {
        "title": "AirCraft System",
        "subtitle": "Full-stack aircraft management platform built design-first with TDD/BDD testing.",
        "problem": "Operational tooling needs to be reliable and testable, not just functional.",
        "solution": "A React + Django platform developed with TDD/BDD (Jest, Cucumber) for maintainability.",
        "tags": ["React", "Django", "Python", "Jest", "Cucumber"],
        "code_url": "https://github.com/Pande-Suraj/AirCraft_System",
    },
    {
        "title": "Ehaat",
        "subtitle": "BSc project: a Django marketplace connecting rural farmers directly with consumers.",
        "problem": "Middlemen reduce farmer margins and limit market access.",
        "solution": "A marketplace with listings, order tracking and fair, transparent pricing.",
        "tags": ["Python", "Django", "JavaScript", "HTML5", "CSS3"],
        "code_url": "https://github.com/surazzpande/ehaat",
    },
]

EXPERIENCE = [
    {
        "role": "Administrator",
        "organisation": "First Call Contract Services — Evri International Hub, Feltham",
        "date_range": "Aug 2026 – Present",
        "location": "UK",
        "is_technical": False,
        "bullets": [
            "Administration and data handling in a high-volume international logistics operation, working accurately to tight deadlines.",
            "Continuing to build software and study AI/ML engineering alongside the role while returning to development full-time.",
        ],
    },
    {
        "role": "Operations & Logistics Roles",
        "organisation": "dnata Catering; Royal Mail (via Angard Staffing); First Call Contract Services (Heathrow)",
        "date_range": "Dec 2023 – Jul 2026",
        "location": "UK",
        "is_technical": False,
        "bullets": [
            "Worked shifts in regulated airport and warehouse environments while completing a full-time MSc with Distinction.",
            "Maintained strong performance in deadline-driven environments alongside ongoing technical development.",
        ],
    },
    {
        "role": "Software Developer (Full-Stack)",
        "organisation": "Pragmatic Technology Pvt. Ltd.",
        "date_range": "Mar 2020 – Oct 2023",
        "location": "Nepal",
        "is_technical": True,
        "tags": ["Python", "Django", "DRF", "React", "PostgreSQL", "MySQL"],
        "bullets": [
            "Developed full-stack web applications with Python, Django, JavaScript and React, delivering features end to end — from data models and REST APIs through to responsive interfaces.",
            "Built and maintained Django backend services: data models, ORM queries, DRF REST endpoints, authentication flows and admin tooling.",
            "Built React frontends consuming internal REST APIs, with reusable components, client-side state management and responsive layouts.",
            "Created a library of reusable React components and Django templates that cut new-feature build time by ~30%.",
            "Designed MySQL/PostgreSQL schemas and optimised slow endpoints through indexing and query tuning.",
            "Delivered in an Agile/Scrum team: sprint planning, stand-ups, code reviews and retrospectives.",
        ],
    },
]

EDUCATION = [
    {
        "qualification": "MSc Software Engineering",
        "institution": "University of West London",
        "date_range": "2023 – 2025",
        "grade": "Distinction",
        "bullets": [
            "Dissertation: WalkNex, an AI-driven e-commerce chatbot (Django backend + LLM retrieval layer).",
            "Advanced Software Engineering, Cloud Computing, Database Systems, Agile Project Management.",
        ],
    },
    {
        "qualification": "BSc Computer Science & IT",
        "institution": "Birendra Memorial College",
        "date_range": "2016 – 2020",
        "grade": "BSc (Hons)",
        "bullets": [
            "Final project: secure banking network simulation (C/C++).",
            "Foundations in algorithms, databases, operating systems and networking.",
        ],
    },
]

# Accurate wording — the Azure material was studied through LinkedIn Learning,
# it is not a Microsoft exam certification.
CERTIFICATIONS = [
    {
        "name": "AI/ML Engineering",
        "issuer": "Coursera",
        "kind": "course",
        "status": "in_progress",
        "progress": 45,
        "note": "",
    },
    {
        "name": "Microsoft Azure Fundamentals (AZ-900 syllabus)",
        "issuer": "LinkedIn Learning",
        "kind": "course",
        "status": "completed",
        "progress": 100,
        "note": "self-study course — not the Microsoft exam certification",
    },
    {
        "name": "Python Essential Training",
        "issuer": "LinkedIn Learning",
        "kind": "course",
        "status": "completed",
        "progress": 100,
        "note": "",
    },
    {
        "name": "IELTS Academic",
        "issuer": "British Council",
        "kind": "other",
        "status": "completed",
        "progress": 100,
        "note": "Overall Band 6.5",
    },
]

EXPLORING = [
    {
        "title": "AI / Machine Learning",
        "grounding": "Built on my MSc dissertation — an AI-driven e-commerce chatbot using an LLM and a retrieval layer.",
        "topics": ["RAG pipelines", "Model fine-tuning", "Vector databases", "MLOps basics"],
    },
    {
        "title": "Cybersecurity",
        "grounding": "Extending my BSc project — a secure banking network simulation in C/C++.",
        "topics": ["OWASP Top 10", "Secure API design", "Auth & threat modelling", "Pen-testing basics"],
    },
    {
        "title": "DevOps",
        "grounding": "Building on my Azure fundamentals self-study and everyday Git workflows.",
        "topics": ["Docker", "GitHub Actions / CI-CD", "Infrastructure as Code", "Observability"],
    },
]


STARTER_POST = {
    "title": "Rebuilding my portfolio as a Django app",
    "excerpt": (
        "Why I moved my portfolio off hardcoded HTML and onto a database, and what "
        "the admin panel actually changed about how I keep it up to date."
    ),
    "body": """My portfolio used to be a static site. Every project, every job, every skill chip was written directly into the markup. Adding anything meant editing HTML and redeploying, which in practice meant I did not add anything for months at a time.

## The problem with hardcoded content

A portfolio is not a finished artefact. Projects get built, roles change, and a certification gets a new qualifier. When each of those is a code change, the friction is enough that the site quietly goes stale — which is the opposite of what a portfolio is for.

## What I changed

I rebuilt it as a Django application. The design stayed exactly the same; what moved was where the content lives:

- Nine models covering profile, projects, experience, education, skills, certifications and posts
- A customised Django admin, so editing is filling in a form
- A contact form that saves to the database and emails me
- Project cards that pull live stars and last-commit dates from the GitHub API

## What I would do differently

Two things caught me out. Vercel's filesystem is read-only, so file uploads need object storage or a different host — worth knowing before you design around `FileField`. And blocking on the GitHub API during page render is a bad idea on serverless: I moved that to a management command that writes the numbers into the database.

```bash
python manage.py refresh_github
```

## Was it worth it

For a static brochure site, honestly, no — a JSON file would have done. I did it because the site is also a work sample. If I am applying for Django roles, the portfolio may as well be a Django app that someone can read the source of.

---

*This is a draft that came with the site build. Edit or delete it in the admin.*""",
    "tags": ["Python", "Django"],
}


class Command(BaseCommand):
    help = "Load the portfolio content from the CV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing content first (contact messages and users are kept).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            for model in (
                Stat, Skill, SkillCategory, Project, ExperienceBullet, Experience,
                EducationBullet, Education, Certification, ExploringTopic, ExploringArea, Tag,
            ):
                model.objects.all().delete()
            self.stdout.write("Cleared existing content.")

        # --- Profile ---
        profile = Profile.load()
        profile.full_name = "Suraj Pandey"
        profile.initials = "SP"
        profile.brand_name = "suraj.dev"
        profile.role_title = "Software Engineer — Python · Django · React · TypeScript"
        profile.availability_note = "Open to UK roles · Graduate visa, full right to work"
        profile.hero_intro = HERO_INTRO
        profile.about_heading = "A developer who ships, end to end"
        profile.about_body = ABOUT_BODY
        profile.exploring_tags = "AI/ML · Cybersecurity · DevOps"
        profile.email = "surajpande20554@gmail.com"
        profile.phone = "+44 7587 546294"
        profile.location = "London, UK"
        profile.github_url = "https://github.com/surazzpande"
        profile.linkedin_url = "https://linkedin.com/in/surajpande-dev"
        profile.seo_description = (
            "Suraj Pandey — software engineer in London. Python, Django, React and "
            "TypeScript. MSc Software Engineering (Distinction)."
        )
        profile.save()

        # --- Stats ---
        for i, (value, label) in enumerate(STATS):
            Stat.objects.update_or_create(label=label, defaults={"value": value, "order": i})

        # --- Skills ---
        for i, (cat_name, skills) in enumerate(SKILLS):
            category, _ = SkillCategory.objects.update_or_create(
                name=cat_name, defaults={"order": i}
            )
            for j, skill_name in enumerate(skills):
                Skill.objects.update_or_create(
                    category=category, name=skill_name, defaults={"order": j}
                )

        # --- Projects ---
        for i, data in enumerate(PROJECTS):
            tags = data.pop("tags", [])
            project, _ = Project.objects.update_or_create(
                title=data["title"], defaults={**data, "order": i}
            )
            project.tags.set(self._tags(tags))

        # --- Experience ---
        for i, data in enumerate(EXPERIENCE):
            bullets = data.pop("bullets", [])
            tags = data.pop("tags", [])
            job, _ = Experience.objects.update_or_create(
                role=data["role"],
                organisation=data["organisation"],
                defaults={**data, "order": i},
            )
            job.tags.set(self._tags(tags))
            job.bullets.all().delete()
            for j, text in enumerate(bullets):
                ExperienceBullet.objects.create(experience=job, text=text, order=j)

        # --- Education ---
        for i, data in enumerate(EDUCATION):
            bullets = data.pop("bullets", [])
            edu, _ = Education.objects.update_or_create(
                qualification=data["qualification"], defaults={**data, "order": i}
            )
            edu.bullets.all().delete()
            for j, text in enumerate(bullets):
                EducationBullet.objects.create(education=edu, text=text, order=j)

        # --- Certifications ---
        for i, data in enumerate(CERTIFICATIONS):
            Certification.objects.update_or_create(
                name=data["name"], defaults={**data, "order": i}
            )

        # --- Exploring ---
        for i, data in enumerate(EXPLORING):
            topics = data.pop("topics", [])
            area, _ = ExploringArea.objects.update_or_create(
                title=data["title"], defaults={**data, "order": i}
            )
            area.topics.all().delete()
            for j, name in enumerate(topics):
                ExploringTopic.objects.create(area=area, name=name, order=j)

        # --- Starter blog post (draft — publish or delete it in the admin) ---
        if not Post.objects.exists():
            data = dict(STARTER_POST)
            tags = data.pop("tags", [])
            post = Post.objects.create(published=False, **data)
            post.tags.set(self._tags(tags))
            self.stdout.write("Added one draft blog post — edit or delete it in the admin.")

        self.stdout.write(self.style.SUCCESS("Portfolio content loaded."))

    @staticmethod
    def _tags(names):
        return [Tag.objects.get_or_create(name=n)[0] for n in names]
