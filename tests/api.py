import requests
import base64
import uuid

def get_video_data(video_url):
    # The API endpoint you are requesting data from
    api_url = "http://127.0.0.1:3004/download_video"

    # Data to be sent in the request body
    data = {
        'video_url': video_url,
        'uid': str(uuid.uuid4())  # Generate a unique identifier
    }

    # Perform the POST request
    response = requests.put(api_url, json=data, verify=False)

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
video_url = "https://www.youtube.com/shorts/Wuxq3fVoAig"
result = get_video_data(video_url)
print(result)
