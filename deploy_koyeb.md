# Deploy to Koyeb

## Quick Deploy Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/telegram-file-bot.git
git push -u origin main
```

### 2. Deploy on Koyeb

1. Go to [Koyeb Dashboard](https://app.koyeb.com/)
2. Click "Create App"
3. Choose "GitHub" as source
4. Select your repository
5. Set build method to "Dockerfile"

### 3. Set Environment Variables

In Koyeb dashboard, add these environment variables:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
URL_SECRET=your_random_secret_key
BASE_URL=https://your-exact-app-name.koyeb.app
```

### 4. Deploy

Click "Deploy" and wait for deployment to complete.

## Alternative: CLI Deploy

### Install Koyeb CLI
```bash
curl -fsSL https://cli.koyeb.com/install.sh | sh
koyeb auth login
```

### Deploy with CLI
```bash
# Create app
koyeb app create telegram-file-bot

# Deploy service
koyeb service create \
  --app telegram-file-bot \
  --git-repository https://github.com/yourusername/telegram-file-bot \
  --git-branch main \
  --name bot \
  --type web \
  --ports 5000:http \
  --env TELEGRAM_API_ID=your_api_id \
  --env TELEGRAM_API_HASH=your_api_hash \
  --env TELEGRAM_BOT_TOKEN=your_bot_token \
  --env URL_SECRET=your_secret \
  --env BASE_URL=https://telegram-file-bot-your-org.koyeb.app \
  --instance-type nano \
  --min-scale 1 \
  --max-scale 1
```

## Configuration Options

### Instance Types
- **nano**: 0.1 vCPU, 128 MB RAM (recommended for bot)
- **micro**: 0.25 vCPU, 256 MB RAM
- **small**: 0.5 vCPU, 512 MB RAM

### Regions
- **fra**: Frankfurt (Europe)
- **was**: Washington (US East)
- **sin**: Singapore (Asia)

## Health Check

The bot includes a `/health` endpoint for Koyeb health checks:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "telegram-file-link-generator"}
```

## Monitoring

Monitor your deployment:
```bash
# Check logs
koyeb service logs telegram-file-bot/bot

# Check status
koyeb service describe telegram-file-bot/bot
```