import os

# --- CONFIGURE THESE ---
VIDEO_DIR = r'/home/arjun/0_contingency-plans/videos'  # Path to your folders
THUMBNAIL_DIR = os.path.join(os.getcwd(), 'thumbnail_cache')
HOVER_PLAY = True
PORT = 5000
# -----------------------

if not os.path.exists(THUMBNAIL_DIR):
    os.makedirs(THUMBNAIL_DIR)

CHANNELS_CONFIG_FILE = os.path.join(os.getcwd(), 'channels.json')