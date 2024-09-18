import os
import re
import json
from datetime import timedelta
from googleapiclient.discovery import build
from flask import Flask, request, render_template
import v.env

load_dotenv()

class YouTubeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.static_URL = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='

    def get_playlist_id(self, playlist_link):
        p_link = re.compile(r'^([\S]+list=)?([\w_-]+)[\S]*$')
        m_link = p_link.match(playlist_link)
        if m_link:
            return m_link.group(2)
        return 'invalid_playlist_link'

    def fetch_playlist_details(self, playlist_id, page_token=None):
        url = self.static_URL.format(self.api_key, playlist_id) + (page_token or '')
        response = requests.get(url)
        return response.json()

    def fetch_video_details(self, video_ids):
        vid_request = self.youtube.videos().list(
            part="contentDetails",
            id=','.join(video_ids)
        )
        title_request = self.youtube.videos().list(
            part="snippet",
            id=','.join(video_ids)
        )
        vid_response = vid_request.execute()
        title_response = title_request.execute()
        return vid_response, title_response

class DurationConverter:
    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')

    @staticmethod
    def seconds_to_time(total_seconds):
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days == 0:
            if hours == 0:
                if minutes == 0:
                    return f'{int(seconds)} Seconds'
                return f'{int(minutes)} Minutes, {int(seconds)} Seconds'
            return f'{int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'
        return f'{int(days)} Days, {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'

class PlaylistProcessor:
    def __init__(self, youtube_api):
        self.youtube_api = youtube_api

    def process_playlist(self, playlist_link):
        playlist_id = self.youtube_api.get_playlist_id(playlist_link)
        if playlist_id == 'invalid_playlist_link':
            return ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
        
        vid_counter = 0
        total_seconds = 0
        nextPageToken = None
        chart_data = [[], []]

        while True:
            playlist_details = self.youtube_api.fetch_playlist_details(playlist_id, nextPageToken)
            if "error" in playlist_details:
                return ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
            
            vid_ids = [item['contentDetails']['videoId'] for item in playlist_details.get('items', [])]
            vid_response, title_response = self.youtube_api.fetch_video_details(vid_ids)

            for item_time, item_title in zip(vid_response['items'], title_response['items']):
                duration = item_time['contentDetails']['duration']
                video_title = item_title['snippet']['title']
                
                hours = DurationConverter.hours_pattern.search(duration)
                minutes = DurationConverter.minutes_pattern.search(duration)
                seconds = DurationConverter.seconds_pattern.search(duration)

                hours = int(hours.group(1)) if hours else 0
                minutes = int(minutes.group(1)) if minutes else 0
                seconds = int(seconds.group(1)) if seconds else 0

                video_seconds = timedelta(
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds
                ).total_seconds()

                total_seconds += video_seconds
                chart_data[0].append(video_title)
                chart_data[1].append(video_seconds / 60)

            nextPageToken = playlist_details.get('nextPageToken')
            if not nextPageToken:
                break

        vid_counter = len(chart_data[1])
        display_text = [
            'No of videos : ' + str(vid_counter),
            'Average length of a video : ' + DurationConverter.seconds_to_time(total_seconds / vid_counter),
            'Total length of playlist : ' + DurationConverter.seconds_to_time(total_seconds),
            'At 1.25x : ' + DurationConverter.seconds_to_time(total_seconds / 1.25),
            'At 1.50x : ' + DurationConverter.seconds_to_time(total_seconds / 1.5),
            'At 1.75x : ' + DurationConverter.seconds_to_time(total_seconds / 1.75),
            'At 2.00x : ' + DurationConverter.seconds_to_time(total_seconds / 2)
        ]
        return display_text, chart_data

app = Flask(__name__, template_folder='static/templates')

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template("home.html")
    else:
        user_link = request.form.get('search_string').strip()
        youtube_api = YouTubeAPI(api_key=os.getenv('api_key'))
        processor = PlaylistProcessor(youtube_api)
        result = processor.process_playlist(user_link)
        if isinstance(result, list):
            return render_template("home.html", display_text=result)
        display_text, chart_data = result
        return render_template("home.html", display_text=display_text, chart_data=chart_data)

if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)





