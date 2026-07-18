# RHCT — Roheen Homeopathic Care & Treatment

Automated daily Facebook page posts about common diseases and their homeopathic treatments.

Every morning at **9:00 AM Pakistan Time**, the bot posts:
- Disease of the Day
- Signs & Symptoms
- Homeopathic Medicine, Potency & Dosage
- Reference link
- Relevant hashtags

## How it works

GitHub Actions runs `poster.py` every day at 9 AM PKT (4 AM UTC).  
It picks a disease from `diseases.py` (cycles through 31 diseases, one per day).  
Then it posts to your Facebook page using the Graph API.

## Setup

### 1. Get Facebook Page Access Token

1. Go to [developers.facebook.com](https://developers.facebook.com) → Create App
2. Add **Facebook Login** product
3. Go to **Graph API Explorer** → select your page → generate a long-lived Page Access Token
4. Copy your **Page ID** (found in your page settings)

### 2. Add secrets to GitHub

In your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name | Value |
|---|---|
| `FB_PAGE_ID` | Your Facebook Page ID |
| `FB_ACCESS_TOKEN` | Your Page Access Token |

### 3. Enable GitHub Actions

Go to **Actions** tab in your repo → Enable workflows.  
You can also trigger a manual post anytime using **Run workflow**.

## Run locally (for testing)

```bash
pip install requests
FB_PAGE_ID=your_id FB_ACCESS_TOKEN=your_token python poster.py
```

---

> ⚠️ All content is for educational purposes only. Always consult a qualified homeopath before taking any medicine.
