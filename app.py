import os
import json
import random
import cv2
import hashlib
from flask import Flask, render_template, send_from_directory, request, jsonify, url_for
import config

app = Flask(__name__)
app.secret_key = 'metube_secret'

SUBS_FILE = 'subscriptions.json'
THUMB_FOLDER = os.path.join('static', 'thumbnails')

# Ensure thumbnail directory exists
os.makedirs(THUMB_FOLDER, exist_ok=True)

def load_subscriptions():
    if not os.path.exists(SUBS_FILE):
        return {}
    with open(SUBS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_subscriptions(data):
    with open(SUBS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_thumbnail(video_path, video_id):
    """Generates a thumbnail if it doesn't exist."""
    thumb_filename = f"{video_id}.jpg"
    thumb_path = os.path.join(THUMB_FOLDER, thumb_filename)
    
    if not os.path.exists(thumb_path):
        cam = cv2.VideoCapture(video_path)
        # Get total frames to pick a frame from the middle/start
        total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
        cam.set(cv2.CAP_PROP_POS_FRAMES, min(100, total_frames // 2)) # Grab frame at 100 or middle
        ret, frame = cam.read()
        if ret:
            # Resize to reduce size (standard YT thumb ratio roughly)
            height, width = frame.shape[:2]
            new_width = 480
            new_height = int(height * (new_width / width))
            frame = cv2.resize(frame, (new_width, new_height))
            cv2.imwrite(thumb_path, frame)
        cam.release()
    
    return thumb_filename

def scan_library():
    """Scans the MEDIA_PATH and updates subscriptions.json."""
    subs = load_subscriptions()
    
    if not os.path.exists(config.MEDIA_PATH):
        print(f"Error: Media path {config.MEDIA_PATH} not found.")
        return {}, []

    channels = [d for d in os.listdir(config.MEDIA_PATH) if os.path.isdir(os.path.join(config.MEDIA_PATH, d))]
    
    # Update JSON with new channels, remove old ones
    current_subs = {}
    for channel in channels:
        if channel in subs:
            current_subs[channel] = subs[channel]
        else:
            # Default new channel settings
            current_subs[channel] = {
                "display_name": channel,
                "show_in_home": True,
                "color": f"#{random.randint(0, 0xFFFFFF):06x}" # Random avatar color
            }
    
    save_subscriptions(current_subs)
    return current_subs

def get_all_videos(filter_channel=None):
    subs = scan_library()
    videos = []
    
    channels_to_scan = [filter_channel] if filter_channel else subs.keys()

    for channel in channels_to_scan:
        # If we are on home page (no filter), check if channel is enabled
        if not filter_channel and not subs.get(channel, {}).get('show_in_home', True):
            continue

        channel_path = os.path.join(config.MEDIA_PATH, channel)
        if not os.path.exists(channel_path): continue

        for file in os.listdir(channel_path):
            if file.lower().endswith(config.VIDEO_EXTENSIONS):
                full_path = os.path.join(channel_path, file)
                # Create a unique ID for the video based on path
                vid_id = hashlib.md5(full_path.encode()).hexdigest()
                
                # Generate thumbnail on the fly (or check cache)
                thumb = get_thumbnail(full_path, vid_id)
                
                videos.append({
                    "id": vid_id,
                    "title": os.path.splitext(file)[0],
                    "filename": file,
                    "channel": channel,
                    "thumbnail": thumb,
                    "channel_color": subs[channel]['color']
                })
    
    if not filter_channel:
        random.shuffle(videos)
        
    return videos, subs

@app.route('/')
def index():
    videos, subs = get_all_videos()
    return render_template('index.html', videos=videos, subs=subs, config=config, page='home')

@app.route('/channel/<name>')
def channel(name):
    videos, subs = get_all_videos(filter_channel=name)
    if name not in subs:
        return "Channel not found", 404
    return render_template('channel.html', videos=videos, subs=subs, current_channel=subs[name], channel_name=name, config=config, page='channel')

@app.route('/subscriptions')
def subscriptions_page():
    subs = scan_library()
    return render_template('subscriptions.html', subs=subs, config=config, page='subs')

@app.route('/api/toggle_home', methods=['POST'])
def toggle_home():
    data = request.json
    channel_name = data.get('channel')
    subs = load_subscriptions()
    
    if channel_name in subs:
        subs[channel_name]['show_in_home'] = not subs[channel_name]['show_in_home']
        save_subscriptions(subs)
        return jsonify({"status": "success", "new_state": subs[channel_name]['show_in_home']})
    return jsonify({"status": "error"}), 400

@app.route('/video_stream/<channel>/<filename>')
def video_stream(channel, filename):
    # Serve video file with range support (handled by Flask/Werkzeug automatically)
    return send_from_directory(os.path.join(config.MEDIA_PATH, channel), filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)