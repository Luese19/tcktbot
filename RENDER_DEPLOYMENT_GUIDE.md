# Render Deployment - Environment Variables Setup

## Problem
After deploying testing branch to Render, you're getting:
```
User 5139651410 attempted to list IT members without permission
```

## Root Cause
The `.env` file is **not committed to git** (for security), so Render doesn't have access to your configuration variables.

---

## Solution: Add Environment Variables to Render

### Step 1: Go to Render Dashboard
1. Log in to: `https://dashboard.render.com/`
2. Select your app: **tcktbot** (or whatever it's called)
3. Go to **Settings** tab

### Step 2: Find "Environment" Section
- Click **Environment** on the left sidebar
- Look for: **Environment Variables** section

### Step 3: Add All Required Variables

Click **"Add Environment Variable"** for each variable:

| Variable Name | Value | Purpose |
|---------------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | Bot authentication |
| `ADMIN_USER_IDS` | `5139651410` | Super admin access |
| `IT_TEAM_USER_IDS` | `5139651410,7998468970` | IT team permissions |
| `COMPANY_NAME` | `Marquis Events Place Inc` | Company name |
| `COMPANY_EMAIL_DOMAIN` | `gmail.com` | Company domain |
| `SUPPORT_EMAIL` | `rivaslueseandrey@gmail.com` | Support email |
| `SMTP_SERVER` | `smtp.gmail.com` | Email server |
| `SMTP_PORT` | `587` | Email port |
| `SMTP_USERNAME` | `rivaslueseandrey@gmail.com` | Email username |
| `SMTP_PASSWORD` | `johsremahkugzflm` | Email password |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REACTION_TICKET_ENABLED` | `true` | Enable reaction tickets |
| `TICKET_REACTION_TRIGGERS` | `👍` | Reaction to trigger tickets |

---

## How to Add Each Variable on Render

### Step-by-Step:
1. Click **"+ Add Environment Variable"** button
2. **Key:** Enter variable name (e.g., `TELEGRAM_BOT_TOKEN`)
3. **Value:** Enter the value from your `.env` file
4. Click **"Save"**
5. Repeat for all variables

**Example:**
```
Key: ADMIN_USER_IDS
Value: 5139651410
```

---

## Step 4: Deploy After Adding Variables

After adding all variables:

1. **Option A: Auto-deploy**
   - Changes auto-deploy (if enabled)
   - Check your app status

2. **Option B: Manual redeploy**
   - Go to **Deployments** tab
   - Click **"Trigger Deploy"** or **"Redeploy"**
   - Wait for deployment to complete

---

## Verify It Works

After redeployment:

1. Go to Render **Logs** tab
2. Check for:
   ```
   ✅ Bot initialized and ready!
   ✅ User manager service initialized
   ✅ All handlers configured successfully
   ```

3. Test in Telegram:
   - Send `/admin` command
   - List IT members
   - You should have full permissions ✅

---

## What Each Variable Does

| Variable | Used For |
|----------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot authentication with Telegram API |
| `ADMIN_USER_IDS` | Which users can manage the bot (you) |
| `IT_TEAM_USER_IDS` | Which users can create tickets via reactions |
| `COMPANY_*` | Company branding and domain |
| `SMTP_*` | Email sending configuration |
| `LOG_LEVEL` | How much logging (DEBUG, INFO, WARNING, ERROR) |
| `REACTION_TICKET_ENABLED` | Enable/disable reaction-based ticket creation |

---

## Security Notes

✅ **Best Practices:**
- Use Render's environment variables, not hardcoded values
- Never commit `.env` to git
- Use secrets manager for sensitive data
- Rotate passwords regularly

❌ **Don't:**
- Don't hardcode bot token in code
- Don't commit `.env` file
- Don't share credentials in messages

---

## Troubleshooting

**Error: "attempted to list ... without permission"**
- ✅ Check: `ADMIN_USER_IDS` includes your user ID (5139651410)
- ✅ Check: `IT_TEAM_USER_IDS` includes your user ID or other IT members
- ✅ Re-deploy after changing variables

**Error: "Configuration not loaded"**
- ✅ Check: All variables are set on Render
- ✅ Check: Bot token is correct
- ✅ Trigger a redeploy

**Bot doesn't respond after adding variables**
- ✅ Go to **Logs** and check for errors
- ✅ Restart the app: **Manual → Restart Instance**
- ✅ Check if deployment completed successfully

---

## Full Variable Reference

Copy-paste these with values from your local `.env`:

```
TELEGRAM_BOT_TOKEN=8789305588:AAE...
ADMIN_USER_IDS=5139651410
IT_TEAM_USER_IDS=5139651410,7998468970
COMPANY_NAME=Marquis Events Place Inc
COMPANY_EMAIL_DOMAIN=gmail.com
SUPPORT_EMAIL=rivaslueseandrey@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=rivaslueseandrey@gmail.com
SMTP_PASSWORD=johsremahkugzflm
LOG_LEVEL=INFO
REACTION_TICKET_ENABLED=true
TICKET_REACTION_TRIGGERS=👍
```

---

## After Setup

Once variables are configured:
- ✅ Bot starts without errors
- ✅ Admin commands work
- ✅ IT team permissions work
- ✅ Full functionality available

---

**Status:** Ready to configure Render environment variables ✅  
**Next:** Add all 13 variables to Render dashboard
