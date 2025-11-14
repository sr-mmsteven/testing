# Reddit API Setup Guide

## The Problem

Reddit has discontinued support for unauthenticated API access. Previously, you could access Reddit's JSON endpoints without credentials, but now Reddit blocks all such requests with 403 errors.

## The Solution

This project now uses **PRAW (Python Reddit API Wrapper)** with OAuth authentication to properly access Reddit's API.

## Setup Instructions

### 1. Create a Reddit App

1. Log in to your Reddit account
2. Go to https://www.reddit.com/prefs/apps
3. Scroll down and click **"create app"** or **"create another app"**
4. Fill in the application form:

   - **name**: Choose any name (e.g., "Sentiment Analysis Tool")
   - **App type**: Select **"script"** (this is important!)
   - **description**: (optional)
   - **about url**: (optional)
   - **redirect uri**: Enter `http://localhost:8080` (required but not actually used)

5. Click **"create app"**

### 2. Get Your Credentials

After creating the app, you'll see:

```
personal use script
<--- This is your CLIENT_ID (14 characters)
sentiment-analysis-tool
by your_username in development
secret           <--- This button reveals your CLIENT_SECRET
```

- **Client ID**: The string directly under "personal use script" (usually 14 characters)
- **Client Secret**: Click the "secret" text to reveal (longer string, ~27 characters)

### 3. Update Your .env File

Add these three lines to your `.env` file:

```bash
REDDIT_CLIENT_ID=your_14_char_client_id
REDDIT_CLIENT_SECRET=your_27_char_client_secret
REDDIT_USER_AGENT=python:srsentiment:v1.0.0 (by /u/your_reddit_username)
```

**Important**: Replace `your_reddit_username` in the USER_AGENT with your actual Reddit username.

### 4. Test the Setup

Run the tool with social media sources:

```bash
news-sentiment --sources social
```

If successful, you should see:

```
✅ Successfully connected to Reddit API (read-only mode)
  Searching r/stocks for 'Company'...
    ✅ Found X posts
```

If you see errors, check the troubleshooting section below.

## Troubleshooting

### ⚠️ "Reddit API not configured"

**Cause**: Missing or empty Reddit credentials in `.env` file

**Fix**:
1. Verify your `.env` file contains all three variables
2. Check that the values are not empty or still set to placeholders
3. Restart your shell/terminal after updating `.env`

### ⚠️ "403 Forbidden" errors

**Cause**: Invalid credentials or wrong app type

**Fix**:
1. Make sure you created a **"script"** type app (not "web app" or "installed app")
2. Double-check your CLIENT_ID and CLIENT_SECRET are copied correctly
3. Verify your Reddit account is in good standing

### ⚠️ "prawcore.exceptions.ResponseException: received 401 HTTP response"

**Cause**: Invalid client secret

**Fix**:
1. Go back to https://www.reddit.com/prefs/apps
2. Click "edit" on your app
3. Generate a new secret and update your `.env` file

### Still Having Issues?

1. **Check your .env file location**: It must be in the project root directory
2. **Verify .env is loaded**: Add `print(os.getenv('REDDIT_CLIENT_ID'))` to test
3. **Check Reddit account status**: Make sure your account isn't shadowbanned
4. **Try regenerating credentials**: Delete the app and create a new one

## Rate Limits

Reddit's API has the following rate limits:

- **60 requests per minute** for OAuth authenticated apps
- The tool includes automatic 1-second delays between requests
- PRAW handles rate limiting automatically

## Why OAuth?

Reddit requires OAuth to:
- Prevent abuse and spam
- Track API usage per app
- Ensure responsible API consumption
- Maintain platform stability

This is standard practice for modern APIs and ensures long-term reliability.

## Additional Resources

- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit App Creation](https://www.reddit.com/prefs/apps)
