# Deploy Your Telegram Bot to Koyeb

## Step-by-Step Deployment Guide

### 1. Prepare Your Repository
```bash
# Initialize git and push to GitHub
git init
git add .
git commit -m "Telegram File Link Bot for Koyeb"
git remote add origin https://github.com/yourusername/telegram-file-bot.git
git push -u origin main
```

### 2. Deploy to Koyeb

1. **Go to Koyeb Dashboard**: https://app.koyeb.com/
2. **Create New App**: Click "Create App"
3. **Connect GitHub**: Select "GitHub" as source
4. **Select Repository**: Choose your bot repository
5. **Build Settings**: 
   - Build method: "Dockerfile" (automatically detected)
   - Port: 5000 (automatically detected)

### 3. Set Environment Variables

In Koyeb dashboard, add these environment variables:

**Required Variables:**
```
TELEGRAM_API_ID = your_api_id_number
TELEGRAM_API_HASH = your_api_hash_string  
TELEGRAM_BOT_TOKEN = your_bot_token_from_botfather
URL_SECRET = your_random_secret_key
BASE_URL = https://your-app-name.koyeb.app
```

**Important**: Replace `your-app-name` with your actual Koyeb app URL!

### 4. Get Your Koyeb App URL

After deployment, Koyeb will give you a URL like:
- `https://telegram-bot-yourname.koyeb.app`
- `https://filebot-yourname.koyeb.app`

**Update BASE_URL** with your actual Koyeb URL in the environment variables.

### 5. How It Works

Once deployed:
1. **Bot receives files** on Telegram
2. **Generates streaming links** like: `https://yourapp.koyeb.app/watch/file123/video.mp4`
3. **Creates download links** directly to Telegram's CDN
4. **Users can stream/download** from any browser

### 6. Instance Recommendations

- **nano**: Perfect for personal use (0.1 vCPU, 128MB RAM)
- **micro**: Good for small teams (0.25 vCPU, 256MB RAM)

## Your Bot is Ready!

The bot will:
- Accept any file type (videos, audio, images, documents)
- Generate instant streaming pages with built-in players
- Provide direct download links via Telegram's CDN
- Work 24/7 on Koyeb's infrastructure

No files are stored on your server - everything uses Telegram's CDN!