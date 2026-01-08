import os
from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

# Configure your media directory here
MEDIA_FOLDER = ''
ALLOWED_EXTENSIONS = {'.mp4', '.webm', '.ogg', '.jpg', '.jpeg', '.png', '.gif'}

if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

def get_media_files():
    files = []
    for filename in os.listdir(MEDIA_FOLDER):
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            files.append({
                'name': filename,
                'type': 'video' if ext in {'.mp4', '.webm', '.ogg'} else 'image',
                'url': filename
            })
    return files

@app.route('/')
def index():
    files = get_media_files()
    return render_template('index.html', files=files)

@app.route('/watch/<path:filename>')
def watch(filename):
    files = get_media_files()
    # Find the current file type
    ext = os.path.splitext(filename)[1].lower()
    file_type = 'video' if ext in {'.mp4', '.webm', '.ogg'} else 'image'
    return render_template('watch.html', filename=filename, file_type=file_type, all_files=files)

@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)