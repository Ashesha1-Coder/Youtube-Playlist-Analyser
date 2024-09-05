import json
import os
import re
from datetime import timedelta
from googleapiclient.discovery import build
from flask import Flask, Response, request, render_template, url_for
import re
import requests


static_URL = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='

api_key = 'AIzaSyCYIU3i74rWF1ex3ebLUXMRbIkJArL0EOE'







 # os.environ.get('YT_API_KEY')
print("Api Key", api_key)

youtube = build('youtube', 'v3', developerKey = api_key)

# To get the playlistId from the link
def pl_id(playlist_link):
    # Regex
    p_link = re.compile(r'^([\S]+list=)?([\w_-]+)[\S]*$')
    m_link = p_link.match(playlist_link)
    if m_link:
        return m_link.group(2)
    else:
        return 'invalid_playlist_link'


# Patter of the Data Received from the YT API
hours_pattern = re.compile(r'(\d+)H')
minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')

# To seconds_to_time the datetime object into readable time
def seconds_to_time(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours =  divmod(hours, 24)
    if days == 0:
        if hours == 0:
            if minutes == 0:
                return f'{int(seconds)} Seconds'
            return f'{int(minutes)} Minutes, {int(seconds)} Seconds'
        return f'{int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'
    
    return f'{int(days)} Days, {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    if(request.method == 'GET'):
        return render_template("home.html")
    else :
        # get playlist link/id as input from the form 
        user_link = request.form.get('search_string').strip()
        pl_ID = pl_id(user_link)
        if pl_ID == 'invalid_playlist_link':
            display_text = ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
            return render_template("home.html", display_text = display_text)
        
    vid_counter = 0
    total_seconds = 0
    nextPageToken = None
    next_page = ''   
    chart_data = [ [], [] ]
    # Playist REquest -> Vid ID
    # for each Vid ID
    #       ContentDetials -> duration
    #       snippet -> Title
    while True:

        # Checking if the palylist is valid or not
        try:
            temp_req = json.loads(requests.get(static_URL.format(api_key, pl_ID) + next_page).text)
            if "error" in temp_req:
                raise KeyError
        except KeyError:
            display_text = ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
            return render_template("home.html", display_text = display_text)
        
        # If it is valid, creat the request
        pl_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=pl_ID,
                maxResults=50,
                pageToken=nextPageToken
            )
        # Execute the request and get the response
        pl_response = pl_request.execute()
        vid_ids = []

        for item in pl_response['items']:
            vid_ids.append(item['contentDetails']['videoId'])
        
        # This is the reuest to gee details for the video. Title, Time
        vid_request = youtube.videos().list(
                            part="contentDetails",
                            id=','.join(vid_ids)
                        )

        title_request = youtube.videos().list(
                        part="snippet",
                        id=','.join(vid_ids)
                    )


        vid_response = vid_request.execute()
        title_response = title_request.execute()

        for item_time, item_title in zip(vid_response['items'], title_response['items']):
            duration = item_time['contentDetails']['duration']
            
            video_title = item_title['snippet']['title']
            # print(f"Titile is :- {video_title}")
            
            hours = hours_pattern.search(duration)
            minutes = minutes_pattern.search(duration)
            seconds = seconds_pattern.search(duration)

            hours = int(hours.group(1)) if hours else 0
            minutes = int(minutes.group(1)) if minutes else 0
            seconds = int(seconds.group(1)) if seconds else 0

            video_seconds = timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds
            ).total_seconds()
            
            # Total Secods of the paylis
            total_seconds += video_seconds
            chart_data[0].append(video_title)
            chart_data[1].append( video_seconds / 60)

        # This is required for the next rrequest, 50 -50 videos acn be fetched in one requeset from playlist
        nextPageToken = pl_response.get('nextPageToken')

        vid_counter = len(chart_data[1])
        if not nextPageToken:
            break
    
    #### Now we have all the data ####
    display_text = []
    display_text += ['No of videos : ' + str(vid_counter),
        'Average length of a video : ' + seconds_to_time(total_seconds/vid_counter), 
        'Total length of playlist : ' + seconds_to_time(total_seconds), 
        'At 1.25x : ' + seconds_to_time(total_seconds/1.25), 
        'At 1.50x : ' + seconds_to_time(total_seconds/1.5), 
        'At 1.75x : ' + seconds_to_time(total_seconds/1.75), 
        'At 2.00x : ' + seconds_to_time(total_seconds/2)]

    return render_template("home.html", display_text = display_text, chart_data = chart_data)


if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)






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