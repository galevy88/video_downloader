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
import logging
from dotenv import load_dotenv
from cloudwatch_logger import CloudWatchLogger as logger

load_dotenv()

app = FastAPI()

class VideoDownloadResult(BaseModel):
    message: str = None
    video_base64: str = None
    error: str = None

def download_video_task(video_url: str, dir_path: str, result_queue: queue.Queue):
    try:
        logger.log(f"Starting download for URL: {video_url}")
        video_file_path = download_social_video(video_url, 'DownloadedVideo', dir_path)
        if video_file_path:
            with open(video_file_path, 'rb') as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
            result = {"message": "Video downloaded successfully", "video_base64": video_base64}
            logger.log("Video downloaded and encoded successfully.")
        else:
            result = {"error": "Video download failed"}
            logger.log("Video download failed.", level=logging.ERROR)
    except Exception as e:
        result = {"error": f"Failed to encode video: {e}"}
        logger.log(f"Exception occurred during video download and encoding: {e}", level=logging.ERROR)
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        result_queue.put(result)

@app.get("/download_video")
def handle_video_download(video_url: str, background_tasks: BackgroundTasks, response: Response):
    if not video_url:
        logger.log("No video URL provided in the request.", level=logging.ERROR)
        response.status_code = 400
        return {"error": "No video URL provided"}

    iat = str(uuid.uuid4())
    base_path = os.getcwd()
    dir_path = os.path.join(base_path, f'{iat}')
    logger.log(f"Creating directory for download: {dir_path}")

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    result_queue = queue.Queue()
    download_thread = threading.Thread(target=download_video_task, args=(video_url, dir_path, result_queue))
    download_thread.start()
    logger.log("Video download initiated in a separate thread.")

    try:
        result = result_queue.get(timeout=20)
        if "error" in result:
            logger.log("Error in video download result.", level=logging.ERROR)
            response.status_code = 500
        return result
    except queue.Empty:
        logger.log("Video download request timed out.", level=logging.ERROR)
        response.status_code = 408
        return {"error": "TIMEOUT"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
