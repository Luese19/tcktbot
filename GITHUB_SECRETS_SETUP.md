# GitHub Secrets Setup Guide

## Problem

CI/CD workflows fail because they don't have access to your `.env` file (which is in `.gitignore` for security).

## Solution

Use **GitHub Secrets** to store sensitive credentials, and the workflows will use them to create a `.env` file during CI/CD runs.

---

## How to Add Secrets

### Step 1: Go to GitHub Repository Settings

1. Go to: `https://github.com/Luese19/tcktbot/settings/secrets/actions`
2. Or: **Settings** → **Secrets and variables** → **Actions**

### Step 2: Click "New repository secret"

### Step 3: Add Each Secret

Add these secrets with the values from your local `.env` file:

| Secret Name | Example Value | Where to Find |
|-------------|---------------|---------------|
| `TELEGRAM_BOT_TOKEN` | `8789305588:AAE...` | Your `.env` file |
| `COMPANY_NAME` | `Marquis Events Place Inc` | Your `.env` file |
| `COMPANY_EMAIL_DOMAIN` | `gmail.com` | Your `.env` file |
| `SUPPORT_EMAIL` | `rivaslueseandrey@gmail.com` | Your `.env` file |
| `SMTP_SERVER` | `smtp.gmail.com` | Your `.env` file |
| `SMTP_PORT` | `587` | Your `.env` file |
| `SMTP_USERNAME` | `rivaslueseandrey@gmail.com` | Your `.env` file |
| `SMTP_PASSWORD` | `johsremahkugzflm` | Your `.env` file |
| `ADMIN_USER_IDS` | `5139651410` | Your `.env` file |
| `IT_TEAM_USER_IDS` | `5139651410,7998468970` | Your `.env` file |

---

## Example: Adding a Secret

### Step 1

- Secret name: `TELEGRAM_BOT_TOKEN`
- Secret value: `8789305588:AAE...` (your actual token)
- Click **"Add secret"**

### Step 2

Repeat for all 10 secrets above

---

## How It Works

When GitHub Actions runs:

1. ✅ Workflow triggers (push, PR, etc.)
2. ✅ Checks out your code
3. ✅ Creates `.env` file from secrets:

   ```bash
   cat > .env << EOF
   TELEGRAM_BOT_TOKEN=${{ secrets.TELEGRAM_BOT_TOKEN }}
   COMPANY_NAME=${{ secrets.COMPANY_NAME }}
   ...
   EOF
   ```

4. ✅ Runs tests with configured environment
5. ✅ `.env` file is only used during CI, never committed

---

## Security Notes

✅ **Secrets are:**

- Encrypted at rest
- Masked in logs (never displayed)
- Only accessible to workflows in your repo
- Only visible to repo admins

❌ **Secrets are NOT:**

- Visible in logs or workflow output
- Committed to git
- Visible to collaborators (unless they're admins)

---

## Verify Setup

After adding secrets, run a workflow:

1. Make a commit and push:

   ```bash
   git add .github/workflows/
   git commit -m "Update CI/CD to use GitHub Secrets"
   git push origin testing
   ```

2. Go to **Actions** tab on GitHub
3. Look for your workflow run
4. Check logs - should show:

   ```
   ✅ All checks passed
   ✅ Docker build successful
   ```

---

## Troubleshooting

**Error:** `Configuration not loaded`

- ✅ Check: Did you add all 10 secrets?
- ✅ Check: Secret names match exactly (case-sensitive)
- ✅ Check: Secret values aren't empty

**Error:** `Docker build failed`

- ✅ Check: `TELEGRAM_BOT_TOKEN` is correct
- ✅ Check: All SMTP settings are correct

**Logs show*** (masked value)**

- ✅ This is normal! Secrets are hidden for security

---

## Full Secret List (Copy-Paste Template)

```
Secret Name: TELEGRAM_BOT_TOKEN
Value: [from your .env]

Secret Name: COMPANY_NAME
Value: [from your .env]

Secret Name: COMPANY_EMAIL_DOMAIN
Value: [from your .env]

Secret Name: SUPPORT_EMAIL
Value: [from your .env]

Secret Name: SMTP_SERVER
Value: [from your .env]

Secret Name: SMTP_PORT
Value: [from your .env]

Secret Name: SMTP_USERNAME
Value: [from your .env]

Secret Name: SMTP_PASSWORD
Value: [from your .env]

Secret Name: ADMIN_USER_IDS
Value: [from your .env]

Secret Name: IT_TEAM_USER_IDS
Value: [from your .env]
```

---

## After Setup

Once secrets are configured:

- ✅ CI/CD tests will pass
- ✅ Docker builds will work
- ✅ Deployment pipeline is ready
- ✅ No need to commit `.env` to git

---

**Next Steps:**

1. Add all 10 secrets to GitHub
2. Push your changes
3. GitHub Actions will run automatically
4. Check the workflow logs to verify everything works

**Status:** Ready to configure secrets ✅
