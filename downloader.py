import requests
import os
from dotenv import load_dotenv
from cloudwatch_logger import CloudWatchLogger as logger
import logging
from aws_secrets import get_secret
load_dotenv()

api_key = get_secret('prod_social_download_all_in_one')
api_url = "https://social-download-all-in-one.p.rapidapi.com/v1/social/autolink"
api_host = "social-download-all-in-one.p.rapidapi.com"

def download_social_video(video_url, dir_path, uid):
    payload = {"url": video_url}

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }

    logger.log(f"Attempting to download video from URL: {video_url}", uid=uid)
    response = requests.post(api_url, json=payload, headers=headers, timeout=15)

    if response.status_code == 200:
        response_json = response.json()

        if 'medias' in response_json and response_json['medias'] and len(response_json['medias']) > 0:
            video_download_url = response_json['medias'][0]['url']

            if video_download_url:
                logger.log("Video download URL found, attempting to download...", uid=uid)
                video_response = requests.get(video_download_url)
                if video_response.status_code == 200:
                    video_file_path = os.path.join(dir_path, uid + '.mp4')
                    with open(video_file_path, 'wb') as f:
                        f.write(video_response.content)
                    logger.log("Video downloaded successfully.", uid=uid)
                    return video_file_path
                else:
                    logger.log("Failed to download the video from the extracted URL", level=logging.ERROR, uid=uid)
                    return None
            else:
                logger.log("No suitable video links found in the response", level=logging.ERROR, uid=uid)
                return None
        else:
            logger.log("No video links found in the response", level=logging.ERROR, uid=uid)
            return None
    else:
        logger.log(f"Error in API response: {response.status_code}", level=logging.ERROR, uid=uid)
        return None
