# Production Deployment & GitHub Actions Guide

Daily Dhikr Automation is designed to run completely unattended via **GitHub Actions** without requiring a local machine or continuously running server.

---

## 1. Pushing the Project to GitHub

If you have created a new empty repository on GitHub (`https://github.com/YOUR_USERNAME/daily-dhikr`), run the following commands from the project directory:

```bash
git add .
git commit -m "feat: complete production-ready Daily Dhikr automation system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/daily-dhikr.git
git push -u origin main
```

---

## 2. Setting Up Persistent PostgreSQL & Storage (Supabase)

Because GitHub Actions runners are ephemeral (local files and databases disappear after each job finishes), the system requires persistent external storage for:
1. Approved content, publication queue, and audit logs (PostgreSQL).
2. Publicly accessible image URLs required by Meta Graph API container creation (Supabase Storage / S3).

### Step 2.1: Create a Free Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a free project.
2. Note your **Database Connection String** under **Project Settings → Database → Connection String → URI**.
   Format:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
3. In the **SQL Editor**, paste and execute the schema from `migrations/schema.sql` (or let Alembic migrate automatically).

### Step 2.2: Create a Media Storage Bucket
1. Go to **Storage → Create Bucket**.
2. Name the bucket: `dhikr-media`.
3. Check the **Public Bucket** toggle (Instagram Graph API must be able to download the image to generate containers).
4. Note your bucket public URL prefix:
   ```
   https://[YOUR-PROJECT-REF].supabase.co/storage/v1/object/public/dhikr-media
   ```

---

## 3. Configuring GitHub Actions Secrets

In your GitHub repository, navigate to **Settings → Secrets and variables → Actions** and click **New repository secret**.

Add the following required secrets:

| Secret Name | Description | Example / Recommended Value |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:pass@db.ref.supabase.co:5432/postgres` |
| `INSTAGRAM_ACCESS_TOKEN` | Meta User/Page Access Token | Long-lived System/Page token |
| `INSTAGRAM_ACCOUNT_ID` | Instagram Business/Creator ID | `17841400000000000` |
| `STORAGE_BACKEND` | Storage provider | `supabase` |
| `STORAGE_ENDPOINT` | Supabase S3 / REST endpoint | `https://[PROJECT-REF].supabase.co/storage/v1/s3` |
| `STORAGE_BUCKET` | Storage bucket name | `dhikr-media` |
| `STORAGE_SECRET_KEY` | Supabase Service Role Key | `eyJhbGciOi...` |
| `STORAGE_PUBLIC_URL_PREFIX` | Public base URL for media | `https://[REF].supabase.co/storage/v1/object/public/dhikr-media` |
| `NOTIFICATION_WEBHOOK_URL` | Webhook for Discord/Slack alerts | `https://discord.com/api/webhooks/...` |
| `DRY_RUN` | Safety switch (`true` or `false`) | `false` (once tested) |
| `PUBLISHING_ENABLED` | Global publishing kill switch | `true` (when ready to go live) |

---

## 4. GitHub Actions Automated Scheduler

The workflow `.github/workflows/daily-content.yml` is the primary orchestrator.

### Execution Schedule
Configured using UTC cron expressions matching standard Jordan time slots (`Asia/Amman`, UTC+3 year-round):
- **07:00 Jordan (04:00 UTC)**: Morning Story
- **09:00 Jordan (06:00 UTC)**: Main Feed Post
- **13:00 Jordan (10:00 UTC)**: Reminder Story
- **17:00 Jordan (14:00 UTC)**: Evening Story
- **20:00 Jordan (17:00 UTC)**: Daily Note preparation

### Concurrency & Exactly-Once Protection
- GitHub concurrency group: `daily-dhikr-publisher` prevents concurrent workflow runs.
- Database atomic job claiming: Updates `status = 'PROCESSING'` in a single atomic SQL statement so that even if runners overlap, double-publishing is strictly impossible.
- Catch-up window: If a GitHub Actions scheduled run is delayed by 15–45 minutes, overdue jobs within the 24-hour grace window are safely executed without duplicate submission.

---

## 5. Live Production Checklist

Before toggling `PUBLISHING_ENABLED=true`:
1. [ ] Push code and verify that `.github/workflows/tests.yml` passes all 31 tests.
2. [ ] Run `.github/workflows/validate-content.yml` to confirm content authenticity.
3. [ ] Run `.github/workflows/daily-content.yml` manually via **Run workflow** with `dry_run=true`.
4. [ ] Check the run summary in GitHub Actions UI (`GITHUB_STEP_SUMMARY`) to ensure rendered images, captions, and jobs match expectations.
5. [ ] Verify that your Instagram account is an **Instagram Business or Creator Account** linked to a Facebook Page.
6. [ ] Set `DRY_RUN=false` and `PUBLISHING_ENABLED=true` in GitHub Secrets.
