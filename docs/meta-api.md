# Official Meta & Instagram Graph API Integration Guide

This guide details the exact steps required to obtain credentials for the **Instagram Graph API (v21.0)** to publish feed posts and stories legitimately.

---

## 1. Account Eligibility Requirements

The official Meta Instagram Content Publishing API requires:
1. An **Instagram Professional Account** (either **Business** or **Creator**). Personal accounts cannot publish via API.
2. A **Facebook Page** connected to the Instagram account.
3. A **Meta Developer Account** with a registered App in **Business** mode.

---

## 2. Setting Up Your Accounts

### Step 2.1: Convert Instagram Account to Professional
1. Open Instagram on your mobile device.
2. Go to **Settings & Privacy → Account Type and Tools → Switch to Professional Account**.
3. Select **Creator** or **Business**.

### Step 2.2: Connect Facebook Page
1. Go to **Edit Profile** on Instagram.
2. Under Public Business Information, select **Page**.
3. Connect or create a Facebook Page dedicated to your brand (e.g. *Daily Dhikr*).

---

## 3. Creating a Meta App

1. Visit [developers.facebook.com](https://developers.facebook.com) and log in.
2. Click **My Apps → Create App**.
3. Select **Other → Next → Business**.
4. Set App Display Name (e.g. `Daily Dhikr Automation`) and create the app.
5. In App Dashboard, add the **Instagram Graph API** product.

---

## 4. Required API Permissions

To publish feed posts and Stories, your access token must have the following scopes:

| Permission | Purpose |
|---|---|
| `instagram_basic` | Read basic Instagram profile information and IDs |
| `instagram_content_publish` | Create media containers and publish feed posts/stories |
| `pages_show_list` | Discover connected Facebook Pages |
| `pages_read_engagement` | Authenticate page management roles |

---

## 5. Locating Your Instagram Account ID

Using the **Graph API Explorer** at `https://developers.facebook.com/tools/explorer/`:

1. Select your App from the top dropdown.
2. Add permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
3. Click **Generate Access Token**.
4. Run the query:
   ```http
   GET /v21.0/me/accounts?fields=id,name,instagram_business_account
   ```
5. Response:
   ```json
   {
     "data": [
       {
         "id": "100293847561023",
         "name": "Daily Dhikr",
         "instagram_business_account": {
           "id": "17841400123456789"
         }
       }
     ]
   }
   ```
6. The `instagram_business_account.id` is your `INSTAGRAM_ACCOUNT_ID`.

---

## 6. Generating a Never-Expiring System User Token

Short-lived User Tokens expire in 1 hour. For an automated GitHub Actions scheduler, generate a **System User Token** in Meta Business Suite:

1. Go to [business.facebook.com/settings](https://business.facebook.com/settings).
2. Under **Users**, click **System Users → Add**.
3. Name: `Dhikr Publisher Bot`, Role: `Admin`.
4. Click **Add Assets**:
   - Assign your Facebook Page (full control).
   - Assign your Instagram Account.
5. Click **Generate New Token**:
   - Select your App.
   - Token Expiration: **Never**.
   - Check scopes: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
6. Copy the generated token. This is your `INSTAGRAM_ACCESS_TOKEN`.

---

## 7. Understanding the Publishing Workflow

Meta employs an asynchronous two-step container architecture:

```
[1. Upload Image]
       │
       ▼
[2. Create Container] ───► POST /{ig_user_id}/media
                               (image_url, caption, media_type)
       │
       ▼
[3. Poll Status]     ───► GET /{container_id}?fields=status_code
                               (wait for FINISHED)
       │
       ▼
[4. Publish Container] ──► POST /{ig_user_id}/media_publish
                               (creation_id = container_id)
       │
       ▼
[5. Response]        ───► { "id": "17901234567890" } (Media ID)
```

### Instagram Notes Notice
Meta does **not** provide any public endpoint or permission for publishing Instagram Notes via third-party software. The application honestly respects platform capabilities: Notes are automatically prepared and formatted to ≤60 characters with status `AWAITING_MANUAL_ACTION`.
