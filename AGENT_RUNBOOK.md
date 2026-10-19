# AGENT RUNBOOK: DAILY DHIKR AUTOMATION
# Master Autonomous Execution & Deployment Guide

> **Directive for AI Agents:**  
> This document is an end-to-end operational runbook designed for an autonomous AI software engineer or DevOps agent. Follow the instructions sequentially to deploy, connect, and verify the Daily Dhikr Instagram automation pipeline. Do not skip verification gates.

---

## 1. PROJECT SPECIFICATION & STATUS

* **Project Name**: Daily Dhikr (`daily-dhikr`)
* **Purpose**: Fully automated daily Instagram publishing system for verified Islamic remembrance (Feed Posts, Stories, Notes) running on GitHub Actions.
* **Target Timezone**: `Asia/Amman` (Jordan Time, UTC+3).
* **Current Status**:
  * Core automation engine, database models, state machine, and API client: **Complete**.
  * Typography & Graphic Engine: **Complete** (Cairo Medium 450 + Inter SemiBold 600, HarfBuzz OpenType layout with zero Tashkeel collisions).
  * Quran API Integration: **Complete** (Sourced from `fawazahmed0/quran-api`, 21 curated short verses seeded).
  * Unit Test Suite: **40/40 Passing** (`pytest`).
  * Git Status: Clean commit history on branch `main`.

---

## 2. REPOSITORY ARCHITECTURE

```
daily-dhikr/
├── app/
│   ├── config.py              # Pydantic Settings & environment variables
│   ├── database.py            # SQLAlchemy database engine & session pool
│   ├── models.py              # ORM models (sources, content, jobs, attempts, audit)
│   ├── schemas.py             # Pydantic validation and response schemas
│   ├── api.py                 # FastAPI admin service & web endpoints
│   ├── content/
│   │   ├── library.py         # Content management & querying
│   │   ├── verification.py    # Authenticity checks & religious safeguards
│   │   ├── captions.py        # Structured bilingual caption formatter
│   │   └── quran_api.py       # Quran API client (fawazahmed0/quran-api)
│   ├── graphics/
│   │   ├── renderer.py        # Pillow graphic rendering engine
│   │   ├── templates.py       # Layout templates for feed, stories, and verse of the day
│   │   └── fonts.py           # Cairo/Inter font loader & HarfBuzz GPOS layout
│   ├── publishing/
│   │   ├── instagram.py       # Official Meta Graph API v21.0 publisher
│   │   ├── notes.py           # Instagram Notes validator & manual workflow
│   │   ├── retry.py           # Exponential backoff & token redaction
│   │   └── storage.py         # Supabase / S3 media asset storage client
│   ├── scheduler/
│   │   ├── queue.py           # Due job selector & atomic claiming
│   │   ├── runner.py          # 12-step master publication pipeline
│   │   └── timezone.py        # Asia/Amman timezone & schedule slots
│   └── notifications/
│       └── sender.py          # Webhook (Discord/Telegram/Slack) alerts
├── assets/
│   ├── logo.svg               # Vector brand logo (Rub el Hizb emblem)
│   └── fonts/                 # Bundled Cairo.ttf and Inter.ttf fonts
├── templates/
│   └── index.html             # Administrative web dashboard UI
├── migrations/
│   └── schema.sql             # Direct PostgreSQL / Supabase DDL schema
├── scripts/
│   ├── seed_demo.py           # Populates authentic Islamic reminders & demo items
│   ├── fetch_verses.py        # CLI for syncing short verses from Quran API
│   ├── validate_content.py    # CI script validating content & rendering
│   └── run_daily.py           # Entrypoint for GitHub Actions & CLI
├── tests/                     # 40 comprehensive pytest unit tests
├── .github/workflows/
│   ├── daily-content.yml      # Primary daily cron scheduler (Jordan time)
│   ├── tests.yml              # CI test runner
│   ├── validate-content.yml   # Content verification workflow
│   └── manual-publish.yml     # On-demand job publishing
├── pyproject.toml             # Project metadata & pytest configuration
└── requirements.txt           # Pinned dependencies
```

---

## 3. DEPLOYMENT & EXECUTION ROADMAP

### PHASE 1: Code Repository Setup (GitHub)

1. Create a remote Git repository on GitHub (e.g. `https://github.com/<USERNAME>/daily-dhikr.git`).
2. Run the following commands in the workspace root:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<USERNAME>/daily-dhikr.git
   git push -u origin main
   ```
3. Verify that the **Test Suite** workflow (`.github/workflows/tests.yml`) triggers on GitHub and all 40 tests pass.

---

### PHASE 2: Cloud Database & Media Storage Setup (Supabase)

GitHub Actions runners are ephemeral. External persistent storage is strictly required for:
* Persistent database records (PostgreSQL).
* Public, API-accessible image URLs required by Meta Graph API container creation (Supabase Storage).

#### Step 2.1: Supabase Project Setup
1. Create a free project at [supabase.com](https://supabase.com).
2. Copy the **PostgreSQL Connection String (URI)** from:  
   `Project Settings -> Database -> Connection String -> URI`.  
   Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
3. Open the **SQL Editor** in Supabase and execute the complete schema from [`migrations/schema.sql`](migrations/schema.sql).

#### Step 2.2: Media Storage Bucket Setup
1. Navigate to **Storage** -> **New Bucket**.
2. Name the bucket: `dhikr-media`.
3. Set the bucket to **Public** (mandatory so Instagram's servers can download images).
4. Public URL Prefix format:  
   `https://[PROJECT-REF].supabase.co/storage/v1/object/public/dhikr-media`
5. Retrieve the `service_role` secret key from:  
   `Project Settings -> API -> Project API keys -> service_role (secret)`.

#### Step 2.3: Seed Authentic Content
Run from a machine with access to the Supabase database:
```bash
# Set connection environment variable
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Seed core Sahih Hadith & Quran reminders
python scripts/seed_demo.py

# Sync curated short, meaningful verses from Quran API
python scripts/fetch_verses.py --sync-curated
```

---

### PHASE 3: Meta Instagram Graph API Setup

The system interacts exclusively with official Meta Graph API v21.0 endpoints.

#### Step 3.1: Account Prerequisites
1. Ensure the Instagram account (e.g. `@DailyDhikr`) is converted to an **Instagram Professional / Business Account**.
2. Link the Instagram Professional Account to a **Facebook Page** (in Instagram App: `Settings -> Account -> Linked Accounts -> Facebook Page`).

#### Step 3.2: Meta Developer App
1. Go to [developers.facebook.com](https://developers.facebook.com) -> **My Apps** -> **Create App**.
2. Select App Type: **Business** (or "Other" -> "Business").
3. Add the **Instagram Graph API** product to your app.

#### Step 3.3: Permissions & Access Token
1. Open the **Graph API Explorer** (`developers.facebook.com/tools/explorer`).
2. Select your App and Facebook Page.
3. Add permissions:
   * `instagram_basic`
   * `instagram_content_publish`
   * `pages_show_list`
   * `pages_read_engagement`
4. Generate the User Token -> Exchange for a **Long-Lived Page Access Token** (60 days) or create a **System User Token** in Meta Business Manager (permanent).

#### Step 3.4: Retrieve Instagram Account ID
Run in Graph API Explorer or via curl:
```bash
curl -X GET "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_ACCESS_TOKEN"
```
Locate your Facebook Page ID, then query:
```bash
curl -X GET "https://graph.facebook.com/v21.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_ACCESS_TOKEN"
```
The returned `instagram_business_account.id` (17 digits) is your `INSTAGRAM_ACCOUNT_ID`.

---

### PHASE 4: GitHub Secrets Configuration

In your GitHub repository, navigate to:  
**Settings -> Secrets and variables -> Actions -> New repository secret**

Add the following 10 configuration secrets:

| Secret Name | Required | Example / Description |
| :--- | :---: | :--- |
| `DATABASE_URL` | **Yes** | `postgresql://postgres:pass@db.xxxx.supabase.co:5432/postgres` |
| `STORAGE_BACKEND` | **Yes** | `supabase` |
| `STORAGE_ENDPOINT` | **Yes** | `https://xxxx.supabase.co/storage/v1` |
| `STORAGE_BUCKET` | **Yes** | `dhikr-media` |
| `STORAGE_SECRET_KEY` | **Yes** | Supabase `service_role` secret key |
| `STORAGE_PUBLIC_URL_PREFIX` | **Yes** | `https://xxxx.supabase.co/storage/v1/object/public/dhikr-media` |
| `INSTAGRAM_ACCOUNT_ID` | **Yes** | `17841400000000000` (17-digit Meta ID) |
| `INSTAGRAM_ACCESS_TOKEN` | **Yes** | Meta Graph API access token |
| `PUBLISHING_ENABLED` | **Yes** | `false` for initial verification; `true` for live |
| `DRY_RUN` | **Yes** | `true` for testing without publishing; `false` in production |
| `NOTIFICATION_WEBHOOK_URL` | Optional | Discord or Telegram webhook for alerts |

---

### PHASE 5: Workflow Execution & Verification

The primary scheduled workflow is `.github/workflows/daily-content.yml`.

#### Step 5.1: Verification Run (Dry-Run)
1. Go to GitHub **Actions** tab.
2. Select **Daily Dhikr Content Automation**.
3. Click **Run workflow** with input: `dry_run = true`.
4. Observe step output:
   * Database connectivity verification: `True`.
   * Due jobs claimed atomically.
   * Graphics rendered with Cairo Medium and full Tashkeel.
   * Summary output displayed in `GITHUB_STEP_SUMMARY`.

#### Step 5.2: Live Activation
1. Update GitHub Secret `DRY_RUN` to `false` and `PUBLISHING_ENABLED` to `true`.
2. Trigger **Run workflow** with `dry_run = false`.
3. Check the Instagram profile: Feed post and story should appear immediately.
4. Verify database: `publication_jobs.status` transitions to `PUBLISHED` with recorded `instagram_media_id`.

#### Step 5.3: Scheduled Daily Slots (Asia/Amman Time)
GitHub Actions triggers on the following UTC schedule matching Jordan Time:
* **07:00 Jordan (04:00 UTC)**: Morning Story (`morning_story` template)
* **09:00 Jordan (06:00 UTC)**: Main Feed Post (`feed_post` or `verse_of_the_day`)
* **13:00 Jordan (10:00 UTC)**: Reminder Story (`dua_story`)
* **17:00 Jordan (14:00 UTC)**: Evening Story (`evening_story`)
* **20:00 Jordan (17:00 UTC)**: Note Preparation (`AWAITING_MANUAL_ACTION`)

---

## 4. COMMAND REFERENCE FOR MAINTENANCE AGENTS

### Local Testing & Development
```bash
# Activate virtual environment
source .venv/bin/activate # Linux/macOS
.\.venv\Scripts\Activate.ps1 # Windows

# Run complete test suite (must be 40/40 passing)
pytest -v

# Run dry-run execution
python scripts/run_daily.py --dry-run

# Run web administration dashboard
uvicorn app.api:app --reload --port 8000
```

### Content Ingestion
```bash
# Sync 21 pre-curated short verses from Quran API
python scripts/fetch_verses.py --sync-curated

# Fetch and import a specific Ayah (e.g. Surah 94, Ayah 5)
python scripts/fetch_verses.py --chapter 94 --verse 5 --render-latest

# List curated short verses
python scripts/fetch_verses.py --list
```

---

## 5. TROUBLESHOOTING & ERROR CODES

| Error Code | Root Cause | Solution |
| :--- | :--- | :--- |
| **Meta 190** | Access token expired or invalidated | Generate a new long-lived token in Graph API Explorer and update `INSTAGRAM_ACCESS_TOKEN`. |
| **Meta 100** | Invalid media URL or inaccessible image | Ensure Supabase bucket `dhikr-media` is **Public** and `STORAGE_PUBLIC_URL_PREFIX` returns 200 HTTP. |
| **Meta 2207001** | Unsupported image aspect ratio | Images must be 4:5 (1080x1350) for Feed or 9:16 (1080x1920) for Stories. Already enforced by renderer. |
| **Tashkeel Clashing** | Fallback to basic Pillow renderer | Ensure `uharfbuzz` and `freetype-py` are installed. Handled in `.github/workflows/daily-content.yml`. |
| **Job Skipped** | Content not approved or marked demo | Run `python -c "from app.content.library import approve_content; ..."` or use the Admin UI. |
