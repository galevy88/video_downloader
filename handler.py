from flask import Flask, request, jsonify
import os
import datetime
import shutil
import base64
from downloader import download_social_video

app = Flask(__name__)


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

    video_file_path = download_social_video(video_url, 'DownloadedVideo', dir_path)

    if video_file_path:
        try:
            # Read the video file and encode it to base64
            with open(video_file_path, 'rb') as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode('utf-8')

            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
            return jsonify({"message": "Video downloaded successfully", "video_base64": video_base64})

        except Exception as e:
            return jsonify({"error": f"Failed to encode video: {e}"}), 500
    else:
        return jsonify({"error": "Video download failed"}), 50
    print(f"dir_path {dir_path}")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3001, debug=True)