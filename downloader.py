import requests
import os
from dotenv import load_dotenv
from cloudwatch_logger import CloudWatchLogger as logger
import logging
from aws_secrets import get_secret
load_dotenv()

api_key = get_secret('prod_fb_video_reels')
def download_social_video(video_url, filename, dir_path):

    api_url = "https://fb-video-reels.p.rapidapi.com/api/getSocialVideo"
    querystring = {"url": video_url, "filename": filename}

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "fb-video-reels.p.rapidapi.com"
    }

    logger.log(f"Attempting to download video from URL: {video_url}")
    response = requests.get(api_url, headers=headers, params=querystring, verify=False)

    if response.status_code == 200:
        response_json = response.json()

        if 'links' in response_json and response_json['links']:
            video_download_url = None

            for link in response_json['links']:
                if link['quality'] == 'hd':
                    video_download_url = link['link']
                    break

            if not video_download_url:
                for link in response_json['links']:
                    if link['quality'] == 'sd':
                        video_download_url = link['link']
                        break

            if video_download_url:
                logger.log("Video download URL found, attempting to download...")
                video_response = requests.get(video_download_url)
                if video_response.status_code == 200:
                    video_file_path = os.path.join(dir_path, filename + '.mp4')
                    with open(video_file_path, 'wb') as f:
                        f.write(video_response.content)
                    logger.log("Video downloaded successfully.")
                    return video_file_path
                else:
                    logger.log("Failed to download the video from the extracted URL", level=logging.ERROR)
                    return None
            else:
                logger.log("No suitable video links found in the response", level=logging.ERROR)
                return None
        else:
            logger.log("No video links found in the response", level=logging.ERROR)
            return None
    else:
        logger.log(f"Error in API response: {response.status_code}", level=logging.ERROR)
        return None
