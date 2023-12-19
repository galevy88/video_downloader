import requests
import base64

def get_video_data(video_url):
    # The API endpoint you are requesting data from
    api_url = "http://3.238.98.134:3001//download_video"

    # Parameters to be sent with the request
    params = {'video_url': video_url}

    # Perform the GET request
    response = requests.get(api_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        response_data = response.json()
        if 'video_base64' in response_data:
            # Decode the base64 string to binary data
            video_data = base64.b64decode(response_data['video_base64'])

            # Save the video data to a file
            video_file_path = 'downloaded_video.mp4'
            with open(video_file_path, 'wb') as video_file:
                video_file.write(video_data)

            return f"Video saved successfully as {video_file_path}"
        else:
            return "No video data found in response"
    else:
        return f"Error: {response.status_code}"

# Example usage
video_url = "https://www.facebook.com/LADbibleAustralia/videos/386779267026839/?extid=CL-UNK-UNK-UNK-AN_GK0T-GK1C&mibextid=Nif5oz"
result = get_video_data(video_url)
print(result)
