# Local Development & Setup Guide

This guide walks you through setting up and running **Daily Dhikr Automation** on your local machine.

---

## 1. Prerequisites

- **Python**: Version 3.12 or newer.
- **Git**: For version control.
- **Operating System**: Windows, macOS, or Linux.

---

## 2. Environment Setup

Clone the repository and enter the directory:

```bash
git clone <your-repo-url> daily-dhikr
cd daily-dhikr
```

Create and activate a virtual environment:

### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install pinned dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configuration

Copy the example environment configuration:

```bash
cp .env.example .env
```

By default, `.env` is configured for **safe local development**:
- `DRY_RUN=true`: Prevents accidental external API calls.
- `PUBLISHING_ENABLED=false`: Master kill switch is active.
- `DATABASE_URL=sqlite:///./daily_dhikr.db`: Uses lightweight local SQLite.
- `TIMEZONE=Asia/Amman`: Standard IANA timezone.

---

## 4. Fonts and Arabic Rendering

The project bundles the open-source **Cairo** (Arabic) and **Inter** (English) fonts in `assets/fonts/`:
- `assets/fonts/Cairo.ttf`
- `assets/fonts/Inter.ttf`

Pillow uses `arabic-reshaper` and `python-bidi` to shape glyph ligatures and reverse visually right-to-left. No manual font installation is required.

---

## 5. Database Initialization & Seeding

Initialize the database schema:

```bash
python -c "from app.database import init_db; init_db()"
```

Or run Alembic migrations:

```bash
alembic upgrade head
```

Seed the content library with verified Islamic reminders:

```bash
python scripts/seed_demo.py
```

This seeds authentic Quranic verses, Sahih Hadiths from Bukhari & Muslim, authentic Adhkar, and clearly marked non-publishable `DEMO` records.

---

## 6. Running Content Validation

Verify that all content records pass Islamic authenticity checks and render cleanly:

```bash
python scripts/validate_content.py
```

---

## 7. Running the Automated Test Suite

Execute the comprehensive test suite with `pytest`:

```bash
pytest
```

All 31 unit tests cover:
- Arabic text shaping & BiDi layout
- Image dimensions (1080x1350 for Feed, 1080x1920 for Stories)
- Source verification & Hadith grading rules
- Demo-record exclusion
- Asia/Amman timezone conversion & catch-up window
- Atomic job claiming & duplicate prevention
- Instagram API error classification & token redaction
- Instagram Notes character limit (≤60 chars) & checklist

---

## 8. Running the Daily Publication Pipeline Locally

Simulate today's daily publication run in safe dry-run mode:

```bash
python scripts/run_daily.py --dry-run
```

---

## 9. Launching the Management Dashboard

Start the FastAPI management dashboard:

```bash
uvicorn app.api:app --reload --port 8000
```

Open your browser at `http://localhost:8000` to access:
- Live status indicators (Amman time, Dry-run switch, Master kill switch).
- Today's Instagram Note with one-click clipboard copy.
- Content Library with Arabic & English previews and verification controls.
- Live image generator preview for Feed and Story layouts.
- Publication Queue and execution logs.
