# Daily Dhikr Automation 🌙

> **A moment of remembrance, every day.**  
> *ذكر يطمئن قلبك*

A production-ready, fully automated Instagram publishing system dedicated to daily Islamic remembrance (adhkar, dua, and Quranic reflections). Engineered to run reliably on a daily schedule using **GitHub Actions**, without requiring a local computer or continuously running server.

---

## ✦ Brand Identity & Visual Language

- **Brand Name**: Daily Dhikr
- **English Tagline**: A moment of remembrance, every day.
- **Arabic Tagline**: ذكر يطمئن قلبك
- **Brand Palette**:
  - **Forest Green**: `#244936` (Primary deep identity)
  - **Cream**: `#FAF8F1` (Warm, elegant canvas)
  - **Sage Green**: `#E7EEE5` (Soft spiritual accent)
  - **Gold**: `#B99A59` (Geometric & decorative accents)
- **Typography & Shaping**:
  - **Arabic**: **Cairo** (Medium 450 weight, bundled in `assets/fonts/Cairo.ttf`) with **HarfBuzz (`uharfbuzz`)** OpenType GPOS anchor positioning and `freetype-py` rasterization. Full Tashkeel (harakat) is 100% preserved with zero diacritic overlap or collisions.
  - **English**: **Inter** (SemiBold 600 weight, bundled in `assets/fonts/Inter.ttf`) for bold, high-contrast mobile readability.
- **Brand Mark**: Clean geometric vector emblem featuring an 8-pointed star (*Rub el Hizb*) in `assets/logo.svg`.

---

## ✦ Key Architecture & Capabilities

1. **Daily Instagram Feed Post (1080 × 1350)**:
   - Automated 4:5 high-resolution graphic generation.
   - Large, shaped Arabic text with English translation and verified source badge.
   - Rich bilingual caption with transliteration, spiritual reflection, and curated hashtags.
2. **Verse of the Day (آية اليوم)**:
   - Automated ingestion of short, meaningful Quranic verses from [`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api) (Quran Academy Uthmani script + Sahih International translation).
   - Dedicated feed post (`verse_of_the_day`) and story (`verse_story`) templates with 21+ pre-curated short verses.
3. **Two to Four Daily Instagram Stories (1080 × 1920)**:
   - Dedicated branded templates for Morning Adhkar, Evening Adhkar, Du'a of the Day, and Friday Reminders.
   - Built-in safe margins (top ~280px, bottom ~280px) ensuring no overlap with Instagram UI elements.
3. **Instagram Notes Preparation (≤ 60 Characters)**:
   - Validates character length and prepares daily Note text.
   - Transitions state to `AWAITING_MANUAL_ACTION` with an automated checklist and one-click clipboard copy.
4. **Official Meta Graph API (v21.0)**:
   - Uses exclusively official, supported endpoints (Media Container creation → Status Polling → Container Publishing).
   - Zero private scraping, zero browser automation, zero password hacks.
5. **Religious Content Safeguards**:
   - Strictly enforces authenticity: Quran verses require Surah & Ayah citations; Hadith require recognized collection references and authentic gradings (Sahih, Hasan).
   - Prohibits fabricated, weak, or unverified claims.
   - Clearly marked `DEMO` records are strictly barred from live publication.
6. **Timezone-Aware Jordan Scheduling (`Asia/Amman`)**:
   - Accounts for timezone rules dynamically using Python's `zoneinfo`.
   - UTC cron execution aligned to Jordan time slots:
     - 07:00 Jordan (04:00 UTC): Morning Story
     - 09:00 Jordan (06:00 UTC): Main Feed Post
     - 13:00 Jordan (10:00 UTC): Reminder Story
     - 17:00 Jordan (14:00 UTC): Evening Story
     - 20:00 Jordan (17:00 UTC): Note Preparation
7. **Idempotency & Duplicate Prevention**:
   - Concurrency group in GitHub Actions prevents overlapping workflow runs.
   - Atomic database status locks (`UPDATE publication_jobs SET status='PROCESSING' WHERE status IN ('READY', 'SCHEDULED')`) ensure exactly-once processing.
   - 24-hour catch-up window safely processes delayed runs without double-posting.
8. **Ambiguous Timeout Reconciliation**:
   - If an API publish request times out after submission, the system inspects recent media to verify if it was posted before attempting any retry, preventing duplicate posts.
10. **Full Test Suite**:
    - 40 automated unit tests covering HarfBuzz OpenType layout, Cairo/Inter font rendering, Quran API, approval gates, state machine, and error policies.

---

## ✦ Repository Layout

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
│   │   └── captions.py        # Structured bilingual caption formatter
│   ├── graphics/
│   │   ├── renderer.py        # Pillow graphic rendering engine
│   │   ├── templates.py       # Layout templates for feed and stories
│   │   └── fonts.py           # Cairo/Inter font loader & Arabic BiDi shaper
│   ├── publishing/
│   │   ├── instagram.py       # Official Meta Graph API publisher
│   │   ├── notes.py           # Instagram Notes validator & manual workflow
│   │   ├── retry.py           # Exponential backoff & token redaction
│   │   └── storage.py         # Supabase / S3 media asset storage client
│   ├── scheduler/
│   │   ├── queue.py           # Due job selector & atomic claiming
│   │   ├── runner.py          # 12-step master publication pipeline
│   │   └── timezone.py        # Asia/Amman timezone & schedule slots
│   └── notifications/
│       └── sender.py          # Webhook (Discord/Slack) & email alerts
├── assets/
│   ├── logo.svg               # Vector brand logo (Rub el Hizb emblem)
│   └── fonts/                 # Bundled Cairo.ttf and Inter.ttf fonts
├── templates/
│   └── index.html             # Administrative web dashboard UI
├── migrations/
│   ├── schema.sql             # Direct PostgreSQL / Supabase DDL schema
│   ├── env.py                 # Alembic migration environment
│   └── versions/              # Migration revisions
├── scripts/
│   ├── seed_demo.py           # Populates authentic Islamic reminders & demo items
│   ├── validate_content.py    # CI script validating content & rendering
│   └── run_daily.py           # Entrypoint for GitHub Actions & CLI
├── tests/                     # 31 comprehensive pytest unit tests
├── docs/
│   ├── setup.md               # Local setup & development guide
│   ├── deployment.md          # GitHub Actions & Supabase deployment
│   ├── meta-api.md            # Meta Developer Portal & Token setup
│   └── troubleshooting.md     # Error diagnosis & troubleshooting
├── .github/workflows/
│   ├── daily-content.yml      # Primary daily cron scheduler
│   ├── tests.yml              # CI test runner
│   ├── validate-content.yml   # Content verification workflow
│   └── manual-publish.yml     # On-demand job publishing
├── .env.example               # Template environment configuration
├── Dockerfile                 # Production container image
├── pyproject.toml             # Project metadata & pytest configuration
└── requirements.txt           # Pinned dependencies
```

---

## ✦ Quick Start

### 1. Local Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .\.venv\Scripts\Activate.ps1 on Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database and seed authentic reminders
python scripts/seed_demo.py

# Validate content library
python scripts/validate_content.py

# Run all 31 automated tests
pytest
```

### 2. Run the Daily Pipeline Locally (Dry-Run Mode)
```bash
python scripts/run_daily.py --dry-run
```

Output:
```
Daily Dhikr Automation
Date: 2026-10-19
Feed posts published: 1
Stories published: 2
Notes prepared: 0
Jobs skipped: 0
Jobs failed: 0

Execution completed successfully.
```

### 3. Launch the Management Dashboard
```bash
uvicorn app.api:app --reload --port 8000
```
Visit `http://localhost:8000` to preview generated images, copy Note drafts, and approve content.

---

## ✦ Documentation Guides

- **[🤖 Autonomous Agent Runbook (Handoff Guide)](AGENT_RUNBOOK.md)**: Master step-by-step instructions for AI agents to deploy and operate this repository autonomously.
- [Local Development & Setup Guide](docs/setup.md)
- [GitHub Actions & Production Deployment](docs/deployment.md)
- [Meta & Instagram Graph API Setup](docs/meta-api.md)
- [Operational Troubleshooting](docs/troubleshooting.md)

---

## ✦ License & Dedication

Released under the **MIT License**.  
*May Allah accept this work and make it a continuous source of beneficial knowledge and remembrance.*
