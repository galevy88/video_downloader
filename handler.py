from flask import Flask, request, jsonify
import os
import datetime
import shutil
import base64
import threading
import queue
from downloader import download_social_video
import time

app = Flask(__name__)

def download_video_task(video_url, dir_path, result_queue):
    try:
        video_file_path = download_social_video(video_url, 'DownloadedVideo', dir_path)
        if video_file_path:
            with open(video_file_path, 'rb') as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
            result = {"message": "Video downloaded successfully", "video_base64": video_base64}
        else:
            result = {"error": "Video download failed"}, 500
    except Exception as e:
        result = {"error": f"Failed to encode video: {e}"}, 500
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        result_queue.put(result)

@app.route('/download_video', methods=['GET'])
def handle_video_download():
    video_url = request.args.get('video_url')
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    iat = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    base_path = os.getcwd()
    dir_path = os.path.join(base_path, f'{iat}')

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    result_queue = queue.Queue()
    download_thread = threading.Thread(target=download_video_task, args=(video_url, dir_path, result_queue))
    download_thread.start()

    try:
        result = result_queue.get(timeout=20)
        return jsonify(result)
    except queue.Empty:
        return jsonify({"error": "TIMEOUT"}), 408

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3001, debug=True)
