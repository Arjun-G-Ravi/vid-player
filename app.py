import os
import cv2
import json
import random
from flask import Flask, render_template, send_from_directory, request, jsonify
from config import VIDEO_DIR, THUMBNAIL_DIR, HOVER_PLAY, CHANNELS_CONFIG_FILE

app = Flask(__name__)

def get_channels_data():
    if os.path.exists(CHANNELS_CONFIG_FILE):
        with open(CHANNELS_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_channels_data(data):
    with open(CHANNELS_CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def generate_thumbnail(video_path, thumb_name):
    target_path = os.path.join(THUMBNAIL_DIR, thumb_name + ".jpg")
    if os.path.exists(target_path):
        return
    
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 1000) # Capture at 1 second
    success, image = cap.read()
    if success:
        cv2.imwrite(target_path, image)
    cap.release()

def scan_videos():
    channels = [d for d in os.listdir(VIDEO_DIR) if os.path.isdir(os.path.join(VIDEO_DIR, d))]
    video_data = []
    channel_prefs = get_channels_data()

    for channel in channels:
        channel_path = os.path.join(VIDEO_DIR, channel)
        # Default to True if not in json
        show_on_home = channel_prefs.get(channel, True)
        
        for file in os.listdir(channel_path):
            if file.lower().endswith(('.mp4', '.mkv', '.mov')):
                vid_id = f"{channel}_{file}".replace(" ", "_")
                generate_thumbnail(os.path.join(channel_path, file), vid_id)
                video_data.append({
                    'id': vid_id,
                    'title': file,
                    'channel': channel,
                    'path': f"{channel}/{file}",
                    'show_on_home': show_on_home
                })
    return video_data, channels

@app.route('/')
def index():
    videos, _ = scan_videos()
    home_videos = [v for v in videos if v['show_on_home']]
    random.shuffle(home_videos)
    return render_template('index.html', videos=home_videos, hover_play=HOVER_PLAY, title="Home")

@app.route('/subscriptions')
def subscriptions():
    _, channels = scan_videos()
    return render_template('subscriptions.html', channels=channels)

@app.route('/channel/<name>')
def channel(name):
    videos, _ = scan_videos()
    channel_videos = [v for v in videos if v['channel'] == name]
    prefs = get_channels_data()
    is_subscribed = prefs.get(name, True)
    return render_template('channel.html', channel_name=name, videos=channel_videos, is_subscribed=is_subscribed)

@app.route('/toggle_subscription', methods=['POST'])
def toggle_subscription():
    data = request.json
    channel = data.get('channel')
    prefs = get_channels_data()
    prefs[channel] = not prefs.get(channel, True)
    save_channels_data(prefs)
    return jsonify({'status': 'success', 'new_state': prefs[channel]})

@app.route('/video_file/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

@app.route('/thumbnail/<vid_id>')
def serve_thumbnail(vid_id):
    return send_from_directory(THUMBNAIL_DIR, vid_id + ".jpg")

if __name__ == '__main__':
    app.run(debug=True, port=5000)