import requests
import os

def download_social_video(video_url, filename, dir_path):
    api_url = "https://fb-video-reels.p.rapidapi.com/api/getSocialVideo"
    querystring = {"url": video_url, "filename": filename}

    headers = {
        "X-RapidAPI-Key": "536d405d53mshebfc39ec9e2c5c7p1e8489jsna23d14919022",
        "X-RapidAPI-Host": "fb-video-reels.p.rapidapi.com"
    }
    print(f"video_url {video_url}")
    response = requests.get(api_url, headers=headers, params=querystring)
    print(response.json())
    if response.status_code == 200:
        # Parse the JSON response
        response_json = response.json()

        # Check if the 'links' key is in the response and it contains at least one link
        if 'links' in response_json and response_json['links']:
            video_download_url = None

            # Look for an HD link first
            for link in response_json['links']:
                if link['quality'] == 'hd':
                    video_download_url = link['link']
                    break

            # If no HD link is found, look for an SD link
            if not video_download_url:
                for link in response_json['links']:
                    if link['quality'] == 'sd':
                        video_download_url = link['link']
                        break

            # If a video link is found, download the video
            if video_download_url:
                video_response = requests.get(video_download_url)
                if video_response.status_code == 200:
                    video_file_path = os.path.join(dir_path, filename + '.mp4')
                    with open(video_file_path, 'wb') as f:
                        f.write(video_response.content)
                    return video_file_path
                else:
                    print("Failed to download the video from the extracted URL")
                    return None
            else:
                print("No suitable video links found in the response")
                return "TIMEOUT"
        else:
            print("No video links found in the response")
            return None
    else:
        print(f"Error in API response: {response.status_code}")
        return None
