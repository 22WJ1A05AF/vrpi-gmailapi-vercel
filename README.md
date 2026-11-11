# VR PI Group — Vercel + Gmail API

This project keeps the original offer-letter PDF layout and original email text/HTML template from your supplied `app.py`. Only the email transport changes: SMTP is replaced by Gmail API OAuth 2.0, sending as `vrpigroupoftechnology@gmail.com`.

## Project files

- `app.py` — Google Sheets reader, original PDF template, original email template, Gmail API sender.
- `api/process.py` — secured Vercel endpoint. GET is for Vercel Cron; POST is for a website webhook/external scheduler.
- `oauth_setup.py` — run locally once to obtain a Gmail refresh token.
- `vercel.json` — daily Hobby-compatible cron example. Hobby is not a one-minute polling solution.

## 1. Google Cloud setup

1. Open https://console.cloud.google.com/ and create/select a project.
2. Enable **Gmail API** and **Google Sheets API**.
3. Configure OAuth consent screen. Add your own Gmail account as a test user while in Testing.
4. Create an OAuth Client ID of type **Desktop app** and download its JSON file.
5. Save that downloaded file in this project folder as `oauth_client.json`.
6. Install local dependencies: `py -m pip install -r requirements.txt`.
7. Run `py oauth_setup.py`, sign in as `vrpigroupoftechnology@gmail.com`, approve Gmail sending, and copy the printed client ID, client secret and refresh token.

**OAuth warning:** Google states that refresh tokens for an External consent screen left in Testing expire after 7 days for Gmail scopes. For ongoing use, review the consent-screen publishing/verification requirements and do not assume a test-mode token will run forever. Publishing an app with sensitive Gmail scopes may require Google verification. Keep this app private and authorize only your own account.

## 2. Google Sheets service account

1. In the same Google Cloud project, create a Service Account and download its JSON key.
2. Share your spreadsheet with the service account's `client_email` as an Editor.
3. Keep the JSON key private. For Vercel, paste the complete one-line JSON into `GOOGLE_SERVICE_ACCOUNT_JSON`.
4. Set `SPREADSHEET_ID` to the ID between `/d/` and `/edit` in your Google Sheets URL.

The script keeps the original column mapping: application id, full name, email address, internship domain track, and letter sent. It writes status, PDF filename, timestamp, and note to columns 18–21 (R–U), matching your original code.

## 3. Local environment variables

Create `.env` only for local testing (do not commit it):

```env
SPREADSHEET_ID=YOUR_SHEET_ID
GOOGLE_SERVICE_ACCOUNT_JSON={...complete service-account JSON...}
GMAIL_USER=vrpigroupoftechnology@gmail.com
GMAIL_CLIENT_ID=YOUR_OAUTH_CLIENT_ID
GMAIL_CLIENT_SECRET=YOUR_OAUTH_CLIENT_SECRET
GMAIL_REFRESH_TOKEN=YOUR_REFRESH_TOKEN
CRON_SECRET=MAKE_A_LONG_RANDOM_SECRET
MAX_ROWS_PER_RUN=5
```

Vercel does not automatically load `.env`; add each value in Project → Settings → Environment Variables. Add them to Production (and Preview only if needed). Never upload `oauth_client.json`, service-account JSON, `.env`, or refresh tokens to GitHub.

## 4. Deploy to Vercel

1. Install Git and Vercel CLI, or push this folder to a private GitHub repository.
2. From this folder run `vercel` and follow the prompts.
3. Add all environment variables in Vercel Project Settings.
4. Run `vercel --prod`.
5. Test the protected endpoint with a POST request using header `X-Webhook-Secret: YOUR_CRON_SECRET`, or a GET request with `Authorization: Bearer YOUR_CRON_SECRET`.

Example PowerShell test:

```powershell
Invoke-RestMethod -Method Post -Uri "https://YOUR-PROJECT.vercel.app/api/process" -Headers @{"X-Webhook-Secret"="YOUR_CRON_SECRET"}
```

## 5. Automation frequency

- Vercel Hobby Cron is daily, not every minute. This repository uses `0 0 * * *` (midnight UTC) as a safe Hobby-compatible example.
- Vercel Pro supports per-minute Cron schedules; after upgrading, change the schedule to `* * * * *` if you truly need one-minute polling.
- Alternatively, configure the internship form to call `POST /api/process` after it writes a new row to Sheets. This is event-driven and avoids polling. The website developer or form integration must be able to add this webhook. If you cannot change the form, use a permitted external scheduler to call the secured endpoint at the desired interval.
- Vercel Hobby is intended for personal, non-commercial use. A company recruitment workflow may require a paid plan under Vercel's terms; check the current plan terms before deploying for company operations.

## 6. Important operational notes

- Gmail API `messages.send` acceptance means Gmail accepted the message for sending. It does not prove the recipient received it, nor that it landed in Primary rather than Promotions/Spam.
- The code marks a row `PROCESSING` before sending and skips `PROCESSING` and `SENT` rows to reduce accidental duplicate sends. If a function stops after Gmail accepted a message but before Sheets updates to SENT, inspect Gmail Sent and the row before manually resetting it.
- `FAILED` rows are eligible for retry on the next run. Correct the cause before retrying.
- Send only to candidates who applied and expect the message. Do not use this system for unsolicited bulk mail.
- Keep `MAX_ROWS_PER_RUN` small to stay within function execution limits.
- Do not store OAuth tokens or service-account keys in source code or Git.
