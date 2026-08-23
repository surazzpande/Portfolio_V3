# Deploying to Vercel — step by step

Follow these in order. Total time is about 30 minutes the first time.
Anything in `like this` is typed into your terminal.

There are five stages:

1. Get it running on your own machine
2. Create a free Postgres database
3. Push the code to GitHub
4. Import into Vercel and set environment variables
5. Set up the production database and point your domain

---

## Stage 1 — Run it locally first

Do this before deploying. If it works locally, deployment problems are
configuration problems, and you'll know where to look.

```bash
cd path/to/the/unzipped/folder

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ — you should see your site.
Open http://127.0.0.1:8000/admin/ and log in with the superuser you just made.

**Check before moving on:** edit a project title in the admin, reload the home
page, and confirm it changed. That's the whole point of the rebuild working.

---

## Stage 2 — Create the database

Vercel's filesystem is read-only and resets between requests, so SQLite cannot
be used there. You need a hosted Postgres. [Neon](https://neon.tech) is free and
takes two minutes.

1. Sign up at neon.tech
2. Create a project — any name, pick the London region for lower latency
3. Copy the connection string. It looks like:
   `postgresql://user:password@ep-something.eu-west-2.aws.neon.tech/neondb?sslmode=require`

**Keep this somewhere safe for now — it contains a password.** Never commit it
to Git; `.gitignore` already excludes `.env` for this reason.

---

## Stage 3 — Push to GitHub

Create a new **empty** repository on GitHub (no README, no .gitignore — this
project already has one). Then:

```bash
git init
git add .
git commit -m "Django portfolio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/portfolio.git
git push -u origin main
```

**Check before moving on:** open the repo on GitHub and confirm there is **no**
`db.sqlite3` and **no** `.env` file. If either is there, stop and tell me.

---

## Stage 4 — Import into Vercel

1. Go to vercel.com → **Add New → Project**
2. Import the repository you just pushed
3. **Framework Preset: Other.** Do not let it guess — it will guess wrong
4. Leave build settings empty; `vercel.json` handles them
5. Before clicking Deploy, open **Environment Variables** and add:

| Name | Value |
|---|---|
| `DJANGO_SECRET_KEY` | a long random string — generate it below |
| `DJANGO_DEBUG` | `False` |
| `DATABASE_URL` | your Neon connection string from Stage 2 |
| `DJANGO_ALLOWED_HOSTS` | `.vercel.app,surajportfolio.com,www.surajportfolio.com` |
| `CONTACT_NOTIFY_EMAIL` | `surajpande20554@gmail.com` |
| `DEFAULT_FROM_EMAIL` | `portfolio@surajportfolio.com` |

Generate the secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`DJANGO_DEBUG` **must** be `False`. With it on, Django shows a full stack trace
including settings to anyone who triggers an error.

6. Click **Deploy**

---

## Stage 5 — Set up the production database

The deploy will succeed but the site will error, because the database is empty.
Fill it from your own machine — you're pointing your local Django at the remote
database for these three commands:

```bash
export DATABASE_URL="your-neon-connection-string"   # Windows: set DATABASE_URL=...

python manage.py migrate
python manage.py seed
python manage.py createsuperuser
```

Reload your `.vercel.app` URL. The site should be live.

Log in at `your-url.vercel.app/admin/` to confirm the admin works.

### Point your domain

In Vercel: **Project → Settings → Domains → Add `surajportfolio.com`.**
Vercel shows the DNS records to set at your registrar. Propagation is usually
minutes, occasionally a few hours.

---

## Optional: email notifications

Contact messages always save to the database, so this only adds the email alert.

**With Gmail** you need an App Password, not your normal password:
Google Account → Security → 2-Step Verification (must be on) → App passwords →
generate one for "Mail". Then add to Vercel:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=surajpande20554@gmail.com
EMAIL_HOST_PASSWORD=the-16-character-app-password
EMAIL_USE_TLS=True
```

**With [Resend](https://resend.com)** (free tier, better deliverability, and you
can send from your own domain):

```
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=re_your_api_key
```

Redeploy after adding these, then send yourself a test message through the form.

---

## Optional: keep GitHub stats fresh

Project cards show stars, language and last-commit date. These update when you
run:

```bash
python manage.py refresh_github
```

To automate it, add `.github/workflows/refresh.yml` to the repo:

```yaml
name: Refresh GitHub stats
on:
  schedule:
    - cron: "0 6 * * 1"     # Mondays at 6am UTC
  workflow_dispatch:         # also lets you run it manually

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python manage.py refresh_github
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          DJANGO_SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY }}
          DJANGO_DEBUG: "False"
```

Add `DATABASE_URL` and `DJANGO_SECRET_KEY` under
**GitHub repo → Settings → Secrets and variables → Actions**.

---

## Optional: import your repos automatically

```bash
python manage.py import_github surazzpande Pande-Suraj
```

Everything imported is a draft. Review in the admin, write the problem/solution,
then publish the ones worth showing.

---

## If something goes wrong

**Build fails on Vercel** — open the build log and read the last error line.
Most often a missing environment variable.

**500 error on the live site** — usually `DATABASE_URL` is wrong or migrations
haven't been run against the production database. Redo Stage 5.

**"DisallowedHost" error** — your domain isn't in `DJANGO_ALLOWED_HOSTS`. Add it
and redeploy.

**CSS missing, page looks unstyled** — static files didn't collect. Check the
build log for the `collectstatic` step.

**Admin page unstyled** — same cause; WhiteNoise serves the admin CSS through
`collectstatic`.

**Contact form returns 403** — a CSRF failure. Check your domain is listed in
`CSRF_TRUSTED_ORIGINS` in `config/settings.py`.

---

## A note on Render

If Vercel's serverless model gets awkward — particularly around the CV file
upload, which needs a writable filesystem — the same code runs on Render with no
changes:

- **Build:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start:** `gunicorn config.wsgi:application`

Render's Postgres add-on sets `DATABASE_URL` for you, and its disk persists, so
file uploads just work. It sleeps on the free tier — the first request after
idle takes a few seconds.
