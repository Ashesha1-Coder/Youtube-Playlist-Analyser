import json
import os
import re
from datetime import timedelta
from googleapiclient.discovery import build
from flask import Flask, Response, request, render_template, url_for
import requests

class YouTubeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.static_url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='

    def get_playlist_id(self, playlist_link):
        pattern = re.compile(r'^([\S]+list=)?([\w_-]+)[\S]*$')
        match = pattern.match(playlist_link)
        if match:
            return match.group(2)
        return 'invalid_playlist_link'

    def fetch_playlist_items(self, playlist_id, page_token=''):
        url = self.static_url.format(self.api_key, playlist_id) + page_token
        response = requests.get(url)
        return response.json()

class TimeFormatter:
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

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/playlist', methods=['POST'])
def get_playlist():
    playlist_link = request.form['playlist_link']
    yt_api = YouTubeAPI(api_key)
    playlist_id = yt_api.get_playlist_id(playlist_link)
    if playlist_id == 'invalid_playlist_link':
        return Response('Invalid playlist link', status=400)
    
    playlist_items = yt_api.fetch_playlist_items(playlist_id)
    return Response(json.dumps(playlist_items), mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)

import json
import re
from datetime import timedelta
from googleapiclient.discovery import build
from flask import Flask, Response, request, render_template
import requests

class YouTubeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.static_url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='

    def get_playlist_id(self, playlist_link):
        pattern = re.compile(r'^([\S]+list=)?([\w_-]+)[\S]*$')
        match = pattern.match(playlist_link)
        if match:
            return match.group(2)
        return 'invalid_playlist_link'

    def fetch_playlist_items(self, playlist_id, page_token=''):
        url = self.static_url.format(self.api_key, playlist_id) + page_token
        response = requests.get(url)
        return response.json()

    def fetch_video_details(self, video_ids):
        vid_request = self.youtube.videos().list(part="contentDetails", id=','.join(video_ids))
        title_request = self.youtube.videos().list(part="snippet", id=','.join(video_ids))
        vid_response = vid_request.execute()
        title_response = title_request.execute()
        return vid_response, title_response

class TimeFormatter:
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

class PlaylistAnalyzer:
    def __init__(self, api_key):
        self.youtube_api = YouTubeAPI(api_key)
        self.time_formatter = TimeFormatter()

    def analyze_playlist(self, playlist_link):
        playlist_id = self.youtube_api.get_playlist_id(playlist_link)
        if playlist_id == 'invalid_playlist_link':
            return ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]

        vid_counter = 0
        total_seconds = 0
        nextPageToken = None
        chart_data = [[], []]

        while True:
            pl_response = self.youtube_api.fetch_playlist_items(playlist_id, nextPageToken)
            vid_ids = [item['contentDetails']['videoId'] for item in pl_response['items']]
            vid_response, title_response = self.youtube_api.fetch_video_details(vid_ids)

            for item_time, item_title in zip(vid_response['items'], title_response['items']):
                duration = item_time['contentDetails']['duration']
                video_title = item_title['snippet']['title']

                hours = self.time_formatter.hours_pattern.search(duration)
                minutes = self.time_formatter.minutes_pattern.search(duration)
                seconds = self.time_formatter.seconds_pattern.search(duration)

                hours = int(hours.group(1)) if hours else 0
                minutes = int(minutes.group(1)) if minutes else 0
                seconds = int(seconds.group(1)) if seconds else 0

                video_seconds = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
                total_seconds += video_seconds
                chart_data[0].append(video_title)
                chart_data[1].append(video_seconds / 60)

            nextPageToken = pl_response.get('nextPageToken')
            vid_counter = len(chart_data[1])
            if not nextPageToken:
                break

        display_text = [
            'No of videos : ' + str(vid_counter),
            'Average length of a video : ' + self.time_formatter.seconds_to_time(total_seconds / vid_counter),
            'Total length of playlist : ' + self.time_formatter.seconds_to_time(total_seconds),
            'At 1.25x : ' + self.time_formatter.seconds_to_time(total_seconds / 1.25),
            'At 1.50x : ' + self.time_formatter.seconds_to_time(total_seconds / 1.5)
        ]
        return display_text

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template("home.html")
    else:
        user_link = request.form.get('search_string').strip()
        analyzer = PlaylistAnalyzer(api_key)
        display_text = analyzer.analyze_playlist(user_link)
        return render_template("home.html", display_text=display_text)

if __name__ == '__main__':
    app.run(debug=True)


# Sure, I'd be happy to explain this Python regular expression to you!

# This regular expression `^([\S]+list=)?([\w_-]+)[\S]*$` can be broken down as follows:

# - `^` : This asserts the start of a line.
# - `([\S]+list=)?` : This is a group that matches one or more non-whitespace characters (`[\S]+`) followed by the
#  string 'list='. The question mark at the end makes this group optional, meaning it will match lines with or without this pattern.
# - `([\w_-]+)` : This is another group that matches one or more word characters (which include alphanumeric 
# characters and underscores) or hyphens.
# - `[\S]*` : This matches zero or more non-whitespace characters.
# - `$` : This asserts the end of a line.

# So, in summary, this regular expression will match any line that optionally 
# starts with one or more non-whitespace characters followed by 'list=', then 
# has one or more word characters or hyphens, and ends with zero or more non-whitespace 
# characters. The two groups in parentheses are capturing groups, which means the portions 
# of the input they match will be saved for later use.