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
import argparse

parser = argparse.ArgumentParser(description='Run FastAPI server.')
parser.add_argument('--port', type=int, default=3001, help='Port to run the server on')
args = parser.parse_args()
load_dotenv()

app = FastAPI()

class VideoDownloadResult(BaseModel):
    message: str = None
    video_base64: str = None
    error: str = None

def download_video_task(video_url: str, dir_path: str, result_queue: queue.Queue, uid: str):
    try:
        logger.log(f"Starting download for URL: {video_url}", uid=uid)
        video_file_path = download_social_video(video_url, 'DownloadedVideo', dir_path, uid)
        if video_file_path:
            with open(video_file_path, 'rb') as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
            result = {"message": "Video downloaded successfully", "video_base64": video_base64}
            logger.log("Video downloaded and encoded successfully.", uid=uid)
        else:
            result = {"error": "Video download failed"}
            logger.log("Video download failed.", level=logging.ERROR, uid=uid)
    except Exception as e:
        result = {"error": f"Failed to encode video: {e}"}
        logger.log(f"Exception occurred during video download and encoding: {e}", level=logging.ERROR, uid=uid)
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        result_queue.put(result)

@app.get("/health")
def is_up():
    return {"status": "UP"}
@app.get("/download_video")
def handle_video_download(video_url: str, response: Response):
    uid = str(uuid.uuid4())
    try:
        if not video_url:
            logger.log(f"No video URL provided in the request. video_url is {video_url}", level=logging.ERROR, uid=uid)
            response.status_code = 400
            return {"error": "No video URL provided"}

        base_path = os.getcwd()
        dir_path = os.path.join(base_path, f'{uid}')
        logger.log(f"Creating directory for download: {dir_path}", uid=uid)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        result_queue = queue.Queue()
        download_thread = threading.Thread(target=download_video_task, args=(video_url, dir_path, result_queue, uid))
        download_thread.start()
        logger.log("Video download initiated in a separate thread.", uid=uid)

        result = result_queue.get(timeout=20)
        if "error" in result:
            logger.log(f"Error in video download result. result is {result}", level=logging.ERROR, uid=uid)
            response.status_code = 500
        return result

    except queue.Empty:
        logger.log("Video download request timed out.", level=logging.ERROR, uid=uid)
        response.status_code = 408
        return {"error": "TIMEOUT"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=args.port)
