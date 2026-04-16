'''
Connector:Azure video indexer and python code
'''
import os
import time
import logging
import requests
import yt_dlp
from azure.identity import AzureCliCredential

logger = logging.getLogger("video-indexer")

class VideoIndexerService:
    def __init__(self):
        self.account_id = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.api_key = os.getenv("AZURE_VI_API_KEY")

    def get_account_token(self):
        '''
        Exchanges the API Key for a Video Indexer Access Token.
        '''
        url = f"https://api.videoindexer.ai/auth/{self.location}/Accounts/{self.account_id}/AccessToken?allowEdit=true"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get VI access token: {response.text}")
            raise Exception(f"VI Auth Failed: {response.text}")

        # The API returns the token as a string with quotes, e.g., "ey..."
        return response.text.strip('"')

    def download_yt_video(self, url, output_path="temp_video.mp4"):
        logger.info(f"Downloading the YT video: {url}")
        ydl_opts = {
            "format": 'best[ext=mp4]/best',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info("Download complete.")
            return output_path
        except Exception as e:
            logger.error(f"YT Video download failed: {str(e)}")
            return None

    def upload_video(self, video_path, video_name):
        # Directly get the account token using our API Key
        vi_token = self.get_account_token()

        api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
        params = {
            "accessToken": vi_token,
            "name": video_name,
            "privacy": "Private",
            "indexingPreset": "Default"
        }

        logger.info(f"Uploading file {video_path} to Azure..........")
        with open(video_path, "rb") as video_file:
            files = {'file': video_file}
            response = requests.post(api_url, params=params, files=files)

        if response.status_code != 200:
            raise Exception(f"Azure upload failed: {response.text}")
        return response.json().get("id")

    def wait_for_processing(self, video_id):
        logger.info(f"Waiting for video {video_id} to process.")
        while True:
            # Refresh token for each poll to avoid expiration
            vi_token = self.get_account_token()

            url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos/{video_id}/Index"
            params = {"accessToken": vi_token}
            response = requests.get(url, params=params)
            data = response.json()

            state = data.get("state")
            if state == "Processed":
                return data
            elif state == "Failed":
                raise Exception("Video indexing failed in Azure")

            logger.info(f"Status: {state}....Waiting 30 sec")
            time.sleep(30)

    def extract_data(self, vi_json):
        transcript_lines = []
        for v in vi_json.get("videos", []):
            for insights in v.get("insights", {}).get("visualContentModeration", []): # Example extra insight
                pass
            for insights in v.get("insights", {}).get("transcript", []):
                transcript_lines.append(insights.get("text", ""))

        ocr_lines = []
        for v in vi_json.get("videos", []):
            for insights in v.get("insights", {}).get("ocr", []):
                ocr_lines.append(insights.get("text", ""))

        return {
            "transcript": " ".join(transcript_lines),
            "ocr_text": ocr_lines,
            "video_metadata": {
                "duration": vi_json.get("summarizedInsights", {}).get("duration"),
                "platform": "youtube"
            }
        }