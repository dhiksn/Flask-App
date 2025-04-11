from flask import Flask, render_template, request, send_file, abort
import yt_dlp
import os
import re
import time
import threading
from datetime import datetime
from werkzeug.utils import safe_join
import tempfile  # gunakan modul tempfile untuk direktori sementara
from flask import after_this_request

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Konfigurasi: gunakan direktori temporary bawaan
DOWNLOAD_FOLDER = tempfile.gettempdir()

# Progress tracking
current_progress = {"progress": 0, "speed": "0 KiB/s", "eta": "0"}

# Regex untuk menghapus ANSI escape sequences
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', '', title).strip()

def delete_file_later(filepath, delay=3600):
    time.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted: {filepath}")
    except Exception as e:
        print(f"Error deleting file: {e}")

def ydl_progress_hook(d):
    global current_progress
    if d['status'] == 'downloading':
        try:
            percent_clean = ansi_escape.sub('', d['_percent_str']).replace('%', '').strip()
            speed_clean = ansi_escape.sub('', d.get('_speed_str', '')).strip()
            eta_clean = ansi_escape.sub('', d.get('_eta_str', '')).strip()

            current_progress = {
                "progress": float(percent_clean or 0),
                "speed": speed_clean,
                "eta": eta_clean
            }
        except Exception as e:
            current_progress = {
                "progress": 0,
                "speed": "0 KiB/s",
                "eta": "0"
            }
            print(f"[HOOK ERROR] Failed parsing progress info: {e}")

@app.route('/')
def index():
    return render_template('index.html', download_url=None, error=None)

@app.route('/', methods=['POST'])
def convert():
    global current_progress
    video_url = request.form['url']
    file_format = request.form['format']
    quality = request.form.get('quality', '192')

    current_progress = {"progress": 0, "speed": "0 KiB/s", "eta": "0"}

    try:
        with yt_dlp.YoutubeDL({
            'quiet': True,
            'no_color': True,
            'cookies': 'cookies.txt'  # ← Tambahkan ini
        }) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            title = sanitize_filename(info_dict.get('title', 'video'))
    except Exception as e:
        return render_template('index.html', download_url=None, error=f"Error getting video info: {str(e)}")

    output_template = os.path.join(DOWNLOAD_FOLDER, f"{title}.%(ext)s")
    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_color': True,
        'cookies': 'cookies.txt',  # ← Tambahkan ini juga di bagian download
        'progress_hooks': [ydl_progress_hook],
    }

    if file_format == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality},
                {'key': 'FFmpegMetadata', 'add_metadata': True},
                {'key': 'EmbedThumbnail'},
            ]
        })
    else:
        ydl_opts['format'] = f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4][height<={quality}]'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            if file_format == 'mp3':
                downloaded_file = os.path.splitext(downloaded_file)[0] + '.mp3'
        threading.Thread(target=delete_file_later, args=(downloaded_file,)).start()
        if os.path.exists(downloaded_file):
            filename = os.path.basename(downloaded_file)
            download_url = f"/download/{filename}"
            return render_template('index.html', download_url=download_url, error=None)
        else:
           return render_template('index.html', download_url=None, error="File conversion failed")
    except Exception as e:
        return render_template('index.html', download_url=None, error=f"Conversion error: {str(e)}")

def delayed_remove(filepath, delay=5):
    def remove():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"✅ File '{os.path.basename(filepath)}' berhasil dihapus setelah {delay} detik.")
            else:
                print(f"⚠️ File sudah tidak ada: {filepath}")
        except Exception as e:
            print(f"[⚠️ ERROR] Gagal hapus file: {e}")
    threading.Thread(target=remove).start()

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        safe_path = safe_join(DOWNLOAD_FOLDER, filename)
        if not os.path.isfile(safe_path):
            abort(404, description="File not found")
        mimetype = 'audio/mpeg' if filename.endswith('.mp3') else 'video/mp4'
        delayed_remove(safe_path, delay=5)
        return send_file(
            safe_path,
            as_attachment=True,
            mimetype=mimetype,
            download_name=filename
        )
    except Exception as e:
        abort(404, description=str(e))

@app.route('/progress')
def progress():
    return current_progress

@app.route('/info', methods=['POST'])
def video_info_api():
    video_url = request.json.get('url', '')
    try:
        with yt_dlp.YoutubeDL({
            'quiet': True,
            'no_color': True,
            'cookies': 'cookies.txt'  # ← Tambahkan di sini juga
        }) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                "success": True,
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)