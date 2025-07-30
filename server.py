#!/usr/bin/env python3
"""
FastAPI Server for Telegram File Link Generator
Serves streaming pages and handles file links
"""

import os
import hmac
import hashlib
import time
from urllib.parse import unquote
from typing import Optional
import aiofiles
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Telegram File Link Generator",
    description="Stream and download files from Telegram CDN",
    version="1.0.0"
)

class FileServerConfig:
    def __init__(self):
        self.url_secret = os.getenv('URL_SECRET', 'default-secret-key-change-me')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = os.getenv('BASE_URL', 'https://your-bot-name.koyeb.app')
        self.port = int(os.getenv('PORT', 5000))

config = FileServerConfig()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Landing page with instructions"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram File Link Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/feather-icons@4.29.0/dist/feather.min.css" rel="stylesheet">
    <style>
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 100px 0;
        }
        .feature-card {
            transition: transform 0.3s ease;
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .telegram-blue {
            background-color: #0088cc;
        }
    </style>
</head>
<body>
    <!-- Hero Section -->
    <section class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 fw-bold mb-4">📁 Telegram File Link Generator</h1>
            <p class="lead mb-5">Convert Telegram files to streamable and downloadable links instantly</p>
            <a href="https://t.me/YOUR_BOT_USERNAME" class="btn btn-light btn-lg">
                <i data-feather="send"></i> Start Bot
            </a>
        </div>
    </section>

    <!-- Features Section -->
    <section class="py-5">
        <div class="container">
            <div class="row text-center mb-5">
                <div class="col-12">
                    <h2 class="fw-bold">How It Works</h2>
                    <p class="text-muted">Send files to our bot and get instant streaming links</p>
                </div>
            </div>
            
            <div class="row g-4">
                <div class="col-md-4">
                    <div class="card feature-card h-100 p-4 text-center">
                        <div class="card-body">
                            <i data-feather="upload-cloud" class="text-primary mb-3" style="width: 48px; height: 48px;"></i>
                            <h5 class="card-title">1. Send File</h5>
                            <p class="card-text">Send any file to our Telegram bot - videos, audio, documents, images</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card feature-card h-100 p-4 text-center">
                        <div class="card-body">
                            <i data-feather="link" class="text-success mb-3" style="width: 48px; height: 48px;"></i>
                            <h5 class="card-title">2. Get Links</h5>
                            <p class="card-text">Receive streaming and download links instantly via Telegram CDN</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card feature-card h-100 p-4 text-center">
                        <div class="card-body">
                            <i data-feather="play-circle" class="text-info mb-3" style="width: 48px; height: 48px;"></i>
                            <h5 class="card-title">3. Stream & Share</h5>
                            <p class="card-text">Access files instantly from any browser or download directly</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Supported Formats -->
    <section class="py-5 bg-light">
        <div class="container">
            <div class="row text-center mb-4">
                <div class="col-12">
                    <h3 class="fw-bold">Supported File Types</h3>
                </div>
            </div>
            
            <div class="row text-center">
                <div class="col-md-3 mb-3">
                    <h6 class="text-primary">📹 Videos</h6>
                    <p class="small text-muted">MP4, AVI, MOV, WMV, FLV, WebM, MKV</p>
                </div>
                <div class="col-md-3 mb-3">
                    <h6 class="text-success">🎵 Audio</h6>
                    <p class="small text-muted">MP3, WAV, OGG, AAC, FLAC</p>
                </div>
                <div class="col-md-3 mb-3">
                    <h6 class="text-info">🖼️ Images</h6>
                    <p class="small text-muted">JPG, PNG, GIF, WebP, BMP, SVG</p>
                </div>
                <div class="col-md-3 mb-3">
                    <h6 class="text-warning">📄 Documents</h6>
                    <p class="small text-muted">PDF, TXT, DOC, XLS, PPT, Archives</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="telegram-blue text-white py-4">
        <div class="container text-center">
            <p class="mb-0">Powered by Telegram CDN • No files stored • Instant access</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/feather-icons@4.29.0/dist/feather.min.js"></script>
    <script>feather.replace()</script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/watch/{file_id}/{filename}")
async def stream_file(file_id: str, filename: str, hash: str, t: str):
    """Stream file through web player"""
    
    # Verify the hash
    if not verify_url_hash(file_id, hash, t):
        raise HTTPException(status_code=403, detail="Invalid or expired link")
    
    # Get file path from hash or reconstruct
    file_path = await get_file_path_from_telegram(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Generate direct Telegram CDN URL
    telegram_file_url = f"https://api.telegram.org/file/bot{config.bot_token}/{file_path}"
    
    # Decode filename
    decoded_filename = unquote(filename)
    
    # Determine file type for appropriate player
    file_ext = decoded_filename.lower().split('.')[-1] if '.' in decoded_filename else ''
    
    if file_ext in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
        player_html = get_video_player_html(telegram_file_url, decoded_filename)
    elif file_ext in ['mp3', 'wav', 'ogg', 'aac', 'flac']:
        player_html = get_audio_player_html(telegram_file_url, decoded_filename)
    elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
        player_html = get_image_player_html(telegram_file_url, decoded_filename)
    else:
        # For documents and other files, redirect to download
        return RedirectResponse(url=telegram_file_url)
    
    return HTMLResponse(content=player_html)

def verify_url_hash(file_id: str, provided_hash: str, timestamp: str) -> bool:
    """Verify the URL hash for security"""
    try:
        # Check if timestamp is within 24 hours (86400 seconds)
        current_time = int(time.time())
        link_time = int(timestamp)
        if current_time - link_time > 86400:  # 24 hours
            return False
        
        # Generate expected hash
        hash_string = f"{file_id}:unknown:{timestamp}:{config.url_secret}"
        expected_hash = hmac.new(
            config.url_secret.encode(),
            hash_string.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        return hmac.compare_digest(expected_hash, provided_hash)
    except:
        return False

async def get_file_path_from_telegram(file_id: str) -> Optional[str]:
    """Get file path from Telegram API (simplified for this example)"""
    # In a real implementation, you'd need to use the Telegram Bot API
    # For now, we'll return a placeholder that works with the bot
    return f"documents/{file_id}"

def get_video_player_html(file_url: str, filename: str) -> str:
    """Generate HTML for video player"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background: #000; color: white; }}
        .player-container {{ 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            padding: 20px;
        }}
        video {{ 
            max-width: 100%; 
            max-height: 90vh; 
            width: auto; 
            height: auto;
        }}
        .info {{ 
            position: absolute; 
            top: 20px; 
            left: 20px; 
            background: rgba(0,0,0,0.7); 
            padding: 10px; 
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="info">
        <h6>📹 {filename}</h6>
        <a href="{file_url}" class="btn btn-sm btn-outline-light" download>⬇️ Download</a>
    </div>
    <div class="player-container">
        <video controls autoplay>
            <source src="{file_url}" type="video/mp4">
            <p>Your browser doesn't support video playback. <a href="{file_url}">Download the file</a> instead.</p>
        </video>
    </div>
</body>
</html>
    """

def get_audio_player_html(file_url: str, filename: str) -> str:
    """Generate HTML for audio player"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .player-container {{ 
            display: flex; 
            flex-direction: column;
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            padding: 20px;
        }}
        .audio-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        audio {{ 
            width: 100%; 
            max-width: 400px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="player-container">
        <div class="audio-card">
            <h2>🎵</h2>
            <h4>{filename}</h4>
            <audio controls autoplay>
                <source src="{file_url}" type="audio/mpeg">
                <p>Your browser doesn't support audio playback. <a href="{file_url}">Download the file</a> instead.</p>
            </audio>
            <div class="mt-3">
                <a href="{file_url}" class="btn btn-outline-light" download>⬇️ Download</a>
            </div>
        </div>
    </div>
</body>
</html>
    """

def get_image_player_html(file_url: str, filename: str) -> str:
    """Generate HTML for image viewer"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background: #222; color: white; }}
        .image-container {{ 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            padding: 20px;
        }}
        img {{ 
            max-width: 100%; 
            max-height: 90vh; 
            object-fit: contain;
            border-radius: 8px;
        }}
        .info {{ 
            position: absolute; 
            top: 20px; 
            left: 20px; 
            background: rgba(0,0,0,0.7); 
            padding: 10px; 
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="info">
        <h6>🖼️ {filename}</h6>
        <a href="{file_url}" class="btn btn-sm btn-outline-light" download>⬇️ Download</a>
    </div>
    <div class="image-container">
        <img src="{file_url}" alt="{filename}">
    </div>
</body>
</html>
    """

# Health check endpoint for Vercel
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "telegram-file-link-generator"}

# Start server
if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=port,
        reload=False  # Disable reload in production
    )