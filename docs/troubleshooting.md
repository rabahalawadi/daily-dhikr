# Operational Troubleshooting Guide

This guide covers common errors encountered during development, automated scheduling, and Instagram publishing, along with concrete solutions.

---

## 1. Authentication & Meta API Errors

### Error: `Code 190: Error validating access token: Session has expired.`
- **Cause**: You are using a temporary user access token rather than a permanent System User Token.
- **Solution**: Follow [docs/meta-api.md](meta-api.md#6-generating-a-never-expiring-system-user-token) to generate a permanent System User Token in Meta Business Manager.

### Error: `Code 10 / 200: Application does not have permission.`
- **Cause**: The access token lacks one of the required scopes or the Instagram Account is not linked to the Facebook Page.
- **Solution**:
  1. Confirm your token includes `instagram_content_publish`, `instagram_basic`, and `pages_show_list`.
  2. In Instagram Mobile App, verify that your account is switched to Professional (Business or Creator) and connected to your Facebook Page.

### Error: `The image could not be loaded from the provided URL.`
- **Cause**: Instagram's servers tried to fetch your image container from `STORAGE_PUBLIC_URL_PREFIX`, but the image is private or blocked by CORS/firewall.
- **Solution**:
  1. Open the image URL in an incognito browser window. If it prompts for login or returns 403 Forbidden, your Supabase or S3 bucket is not set to **Public**.
  2. In Supabase Storage, toggle the `dhikr-media` bucket to **Public Bucket**.

---

## 2. Scheduling & GitHub Actions

### Issue: GitHub Actions did not trigger at the exact minute
- **Explanation**: GitHub Actions scheduled cron runs are shared on public queue infrastructure and can experience delays of 10 to 45 minutes during peak hours.
- **Built-in Solution**: Daily Dhikr includes an automatic **24-hour catch-up window**. When the runner wakes up, it retrieves any due jobs scheduled within that window and processes them. Duplicate execution is strictly blocked by atomic database status locks.

### Issue: Duplicate jobs or race conditions
- **Explanation**: If two workflows run concurrently, could both publish the same post?
- **Protection**:
  1. GitHub workflow concurrency: `group: daily-dhikr-publisher` cancels or blocks overlapping GitHub Actions runs.
  2. Database atomic locks: `UPDATE publication_jobs SET status='PROCESSING' WHERE status IN ('READY', 'SCHEDULED')` updates exactly 1 row. Any concurrent worker that receives `rowcount == 0` skips the job immediately.

---

## 3. Ambiguous Publish Timeouts

### Issue: Publish container request timed out after submission
- **Danger**: Submitting the publish request again without checking could create a duplicate post on the feed.
- **Built-in Handling**:
  1. When a timeout occurs on `media_publish`, the publisher triggers `reconcile_recent_publication()`.
  2. It queries `GET /{account_id}/media` to see if a post with the same image appeared within the last 5 minutes.
  3. If found, it recovers the real Instagram Media ID and marks the job `PUBLISHED`.
  4. If inconclusive, it sets `status = AWAITING_MANUAL_ACTION` and sends an alert, completely preventing duplicate postings.

---

## 4. Arabic Font Rendering

### Issue: Arabic letters appear disconnected or left-to-right
- **Cause**: Standard graphics libraries draw text left-to-right without glyph joining.
- **Solution**: The engine applies `arabic-reshaper` (for medial, initial, final glyph ligatures) followed by `bidi.algorithm.get_display` (for RTL display reordering) before drawing with Pillow. The Cairo font (`assets/fonts/Cairo.ttf`) is bundled directly in the repository.

---

## 5. Emergency Master Kill Switch

If you need to halt all automated publishing immediately:
- In GitHub Repository Secrets, set `PUBLISHING_ENABLED=false`.
- Or in `.env`, set `PUBLISHING_ENABLED=false`.
- Or via the Admin API:
  ```bash
  curl -X POST "http://localhost:8000/api/settings/toggle-publishing?enable=false"
  ```
The runner will immediately stop making live API calls and switch to safe dry-run mode.
