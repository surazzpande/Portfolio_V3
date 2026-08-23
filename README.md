# surajportfolio.com — Django portfolio

A database-driven rebuild of the portfolio site. Same design as before, but every
piece of content — projects, jobs, skills, education, certifications — lives in the
database and is edited through the Django admin instead of in the code.

**What's new compared with the static version**

- Interactive 3D hero (Three.js) — a constellation particle field that reacts to the cursor
- A 3D robot companion with an on/off toggle, and animated page transitions
- A proper admin dashboard: unread messages, drafts, what you're studying, quick actions
- Django admin at `/admin/` — add, edit, reorder or hide anything without touching code
- Working contact form; messages are stored, readable in the admin, and emailed to you
- A blog at `/writing/`, with drafts only you can see
- Project cards show live GitHub stars, language and last-commit date
- Project filter chips are generated from the technologies actually in use
- Publish/unpublish toggles, so you can hide a project without deleting it
- Upload your CV as a PDF and the "Download Resume" button appears automatically

**Deploying it:** see [DEPLOY.md](DEPLOY.md) for the full step-by-step.

---

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed               # loads all your CV content
python manage.py createsuperuser    # your admin login
python manage.py runserver
```

- Site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

Local development uses SQLite automatically — no database setup needed.

To reload content from scratch: `python manage.py seed --reset`
(this clears content tables but never deletes contact messages or users).

---

## Deploying

Full step-by-step instructions — database, GitHub, Vercel, domain, email and
scheduled GitHub-stat refreshes — are in **[DEPLOY.md](DEPLOY.md)**.

Short version: create a free Neon Postgres, push to GitHub, import into Vercel
with **Framework Preset: Other**, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`,
`DATABASE_URL` and `DJANGO_ALLOWED_HOSTS`, then run `migrate` + `seed` +
`createsuperuser` against the production database.

The same code also runs on Render with no changes — easier if you want the CV
file upload to persist, since Vercel's filesystem is read-only.

---

## Editing your content

Everything is at `/admin/`:

| Section | What it controls |
|---|---|
| **Profile & contact details** | Your name, hero text, about paragraphs, email, phone, links, CV upload |
| **Projects** | Title, problem/solution, tech tags, repo link. Tick *featured* to highlight, untick *published* to hide |
| **Experience** | Jobs and their bullet points. Tick *is technical* to highlight it in the timeline |
| **Education** | Degrees and grades |
| **Certifications** | Courses and certifications — set one to *In progress* with a percentage while you study it, then *Completed* with a date. Add a credential link so people can verify it |
| **Skill categories** | Skill groups and the chips inside them |
| **Exploring areas** | The "Where I'm heading next" cards |
| **Stats** | The four numbers in the About section |
| **Posts** | Blog posts. Untick *published* to keep one as a draft |
| **Contact messages** | Anything sent through the form — read-only, with read/unread marking |

`order` fields control position: lower numbers appear first.

---

## Notes

**File uploads.** The CV upload writes to local disk, which works on Render but not
on Vercel's serverless filesystem. On Vercel, either commit the PDF into the repo
and link to it, or add S3 storage (`django-storages`).

**Email notifications.** Set `CONTACT_NOTIFY_EMAIL` plus the `EMAIL_*` variables
(see `.env.example`) and you get an email each time someone uses the form, with
reply-to set to the sender so you can answer straight from your inbox. Without
them the message still saves — mail failures can never lose an enquiry.

**Keeping projects in sync.** Three ways, all doing the same thing:

1. **The "Sync from GitHub" button** at the top of the Projects list in the admin —
   click it whenever you push something new.
2. **The scheduled workflow** in `.github/workflows/sync-github.yml`, which runs
   every Monday. Add `DATABASE_URL` and `DJANGO_SECRET_KEY` as repo secrets to
   switch it on.
3. **The command**, `python manage.py import_github surazzpande Pande-Suraj`.

All three import new repos as **drafts** and refresh stats on existing ones.
Nothing is ever published without you. Which accounts get synced is the
`GITHUB_USERNAMES` environment variable.

**Tracking what you're learning.** Certifications have a status (Completed /
In progress / Planned) and a percentage. Anything marked in progress shows a
progress bar on the site that fills as it scrolls into view, so the section stays
current while you study rather than only after you finish. The `kind` field
distinguishes a real exam certification from a course — keep that honest.

**Importing projects from GitHub.** `python manage.py import_github surazzpande Pande-Suraj`
pulls every repository from those accounts and creates projects for them. New ones
arrive **unpublished**, so nothing reaches the live site until you write a proper
problem/solution in the admin and tick 'published'. Re-running refreshes stats on
existing projects without overwriting wording you've edited. Forks and archived
repos are skipped; `--min-pushed 2024-01-01` limits it to recent work.

**GitHub stats.** `python manage.py refresh_github` reads each project's
`code_url`, fetches stars, forks, language and last-commit date, and stores them.
Rendering never waits on the API. DEPLOY.md includes a GitHub Actions workflow to
run it weekly.

**The 3D hero.** `portfolio/static/portfolio/js/hero3d.js` — a rotating
icosahedral wireframe in a particle field, reacting to the cursor. Three.js is
vendored into `js/vendor/` rather than loaded from a CDN, so the site works
offline and does not depend on anyone else's uptime. It deliberately does not run
when the visitor prefers reduced motion, on screens under 760px, or where WebGL
is unavailable — the CSS gradient shows instead. Rendering pauses when the hero
scrolls out of view or the tab is hidden. To tune it, the constants at the top of
the file (`PARTICLE_COUNT`, `FIELD_RADIUS`, `BRAND`) are the main dials; to remove
it, delete the `<div id="hero3d">` from `index.html`.

**The admin dashboard.** `/admin/` opens on a dashboard rather than the bare
model list: unread messages, live vs draft counts, courses in progress, a
"Sync from GitHub" button and a warning when the last sync is over a fortnight
old. It is built from `templates/admin/index.html` plus the
`dashboard_panel` tag in `portfolio/templatetags/dashboard.py`; the theme is
`static/portfolio/css/admin.css`, which mostly just redefines Django's own CSS
variables to the site palette. The standard admin is untouched underneath.

**The robot.** `static/portfolio/js/robot.js` — built from Three.js primitives,
so there is no model file to download. It tracks the cursor, blinks, bobs, and
waves with a different line each time you click it. The toggle beside it stores
the choice in `localStorage` under `portfolio:robot`. Edit the `GREETINGS` array
to change what it says. Hidden under reduced-motion, below 900px, and without
WebGL.

**Page transitions.** `static/portfolio/js/transitions.js` wipes three bars
across the screen before navigating and back out on arrival. It only intercepts
plain left-clicks on same-origin page links — modifier keys, new tabs, downloads,
anchors, `/admin/`, `/media/`, `/static/` and file extensions all fall through to
normal browser behaviour, and a hard timeout guarantees the navigation happens
even if something stalls. Add `data-no-transition` to any link to opt it out.

**Writing posts.** Post bodies use a small subset of Markdown handled in
`portfolio/templatetags/postmarkup.py` — `## heading`, `- bullet`, `**bold**`,
`*italic*`, `` `code` ``, `> quote`, `---`, `[link](url)` and triple-backtick code
blocks. Everything is escaped before formatting, so a post can't inject HTML.

**Accuracy.** The Azure entry is deliberately worded as a LinkedIn Learning
self-study course rather than a Microsoft exam certification. Please keep it that
way — the previous site claimed "Microsoft Certified", which was not accurate and
is the kind of thing an interviewer can check.

## Project layout

```
config/           settings, urls, wsgi
portfolio/
  models.py       10 models — content lives here
  admin.py        the editing interface
  views.py        home, blog list/detail, contact
  forms.py        contact form + honeypot
  mail.py         notification email (never raises)
  github.py       GitHub API client
  templatetags/   post body formatter
  management/commands/
    seed.py             loads your CV content
    refresh_github.py   updates repo stats
  templates/portfolio/
  static/portfolio/
```

## Tech

Django 5.2 · PostgreSQL (SQLite locally) · WhiteNoise · vanilla JS · no build step
#   P o r t f o l i o _ V 3  
 