from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel
import os
import datetime
import shutil
import base64
from downloader import download_social_video
import uuid
import threading
import queue

app = FastAPI()

class VideoDownloadResult(BaseModel):
    message: str = None
    video_base64: str = None
    error: str = None

def download_video_task(video_url: str, dir_path: str, result_queue: queue.Queue):
    try:
        video_file_path = download_social_video(video_url, 'DownloadedVideo', dir_path)
        if video_file_path:
            with open(video_file_path, 'rb') as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
            result = {"message": "Video downloaded successfully", "video_base64": video_base64}
        else:
            result = {"error": "Video download failed"}
    except Exception as e:
        result = {"error": f"Failed to encode video: {e}"}
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        result_queue.put(result)

@app.get("/download_video")
def handle_video_download(video_url: str, background_tasks: BackgroundTasks, response: Response):
    if not video_url:
        response.status_code = 400
        return {"error": "No video URL provided"}

    iat = str(uuid.uuid4())
    base_path = os.getcwd()
    dir_path = os.path.join(base_path, f'{iat}')

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    result_queue = queue.Queue()
    download_thread = threading.Thread(target=download_video_task, args=(video_url, dir_path, result_queue))
    download_thread.start()

    try:
        result = result_queue.get(timeout=20)
        if "error" in result:
            response.status_code = 500
        return result
    except queue.Empty:
        response.status_code = 408
        return {"error": "TIMEOUT"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
