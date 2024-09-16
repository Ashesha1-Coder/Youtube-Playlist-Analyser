import json
import os
import re
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('api_key')


from datetime import timedelta
from googleapiclient.discovery import build
from flask import Flask, Response, request, render_template, url_for
import requests
# URL pattern for fetching Youtube playlist details
static_URL = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='
# Youtube Data API Key

# Initialize Youtube API Client using the API key

youtube = build('youtube', 'v3', developerKey = api_key)

# REGEX to extract playlist ID from the playlist URL
def pl_id(playlist_link):
    # Regex to match YouTube playlist URLs and extract the playlist ID
    # breakdown of regex:
    #^([\S]+list=)? - Matches any non-whitespace characters before 'list='
    #([\w_-]+) -Matches the playlistID (alphanumeric characters,underscores,hyphens)
    #[\s]*$ -Matches any trailing non-whitespace characters
    p_link = re.compile(r'^([\S]+list=)?([\w_-]+)[\S]*$')
    m_link = p_link.match(playlist_link)
    
    
    if m_link:
        # If a match is found, return the playlist ID(group2)
        return m_link.group(2)
    else:
        #Return the error string if the link is invalid
        return 'invalid_playlist_link'


# Patterns to extract the Data from the YT API
hours_pattern = re.compile(r'(\d+)H')
minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')

# Convert total seconds into a human readable time
def seconds_to_time(total_seconds):
    #Convert total seconds into hours, miinutes and seconds
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours =  divmod(hours, 24)
    
    # Construct the time string based on the duration
    if days == 0:
        if hours == 0:
            if minutes == 0:
                return f'{int(seconds)} Seconds'
            return f'{int(minutes)} Minutes, {int(seconds)} Seconds'
        return f'{int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'
    
    return f'{int(days)} Days, {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'
# Initialize the Flask app
app = Flask(__name__, template_folder='static/templates')

# Define the main route for the home page
@app.route("/", methods=['GET', 'POST'])
def home():
    # Render the home page on GET request
    if(request.method == 'GET'):
        return render_template("home.html")
    
    # Handle POST request (form submission)
    else :
        # get playlist link/id as input from the form 
        user_link = request.form.get('search_string').strip()
       
        # Extract the playlist ID from the link
        pl_ID = pl_id(user_link)
        
        # Handle invalid playlist link
        if pl_ID == 'invalid_playlist_link':
            display_text = ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
            return render_template("home.html", display_text = display_text)
    
    # Initialize variables to count videos and accumulate total duration    
    vid_counter = 0
    total_seconds = 0
    nextPageToken = None
    next_page = ''   
    chart_data = [ [], [] ] # For storing video titles and durations
    
    #       snippet -> Title
    
    # Loop through playlist pages, Yooutube API limits to 50 items per
    while True:
         # Construct the request URL using the static URL and page token
        try:
            temp_req = json.loads(requests.get(static_URL.format(api_key, pl_ID) + next_page).text)
    
           # Handle any error returned by the API  
            if "error" in temp_req:
                raise KeyError
            
        except KeyError:
            # If an error occurs, display an error message to the user  
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
        
        # This is the request to get details for the video. Title, Time
        vid_request = youtube.videos().list(
                            part="contentDetails",
                            id=','.join(vid_ids)
                        )
        # Fetch video titles
        title_request = youtube.videos().list(
                        part="snippet",
                        id=','.join(vid_ids)
                    )
       
        # Execute the requests
        vid_response = vid_request.execute()
        title_response = title_request.execute()
        
        
        # Iterate through the video details and titles
        for item_time, item_title in zip(vid_response['items'], title_response['items']):
            # Extract the duration from the response
            duration = item_time['contentDetails']['duration']
            video_title = item_title['snippet']['title']
            # print(f"Titile is :- {video_title}")
            
            # Parse hours, minutes and seconds from the duration
            hours = hours_pattern.search(duration)
            minutes = minutes_pattern.search(duration)
            seconds = seconds_pattern.search(duration)

            hours = int(hours.group(1)) if hours else 0
            minutes = int(minutes.group(1)) if minutes else 0
            seconds = int(seconds.group(1)) if seconds else 0
            # Calculate the total duration of the video in seconds
            video_seconds = timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds
            ).total_seconds()
            
            # Total Seconds of the playlist
            total_seconds += video_seconds
            chart_data[0].append(video_title)
            chart_data[1].append( video_seconds / 60)
            
        # Pagination :Check if there is another page of results 
        # This is required for the next rrequest, 50 -50 videos acn be fetched in one requeset from playlist
        nextPageToken = pl_response.get('nextPageToken')
        
        # Update video Count
        vid_counter = len(chart_data[1])
        
        # If there is no next page , break out of the loop
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
    # Render the results on the home page
    return render_template("home.html", display_text = display_text, chart_data = chart_data)

# Run the Flask app
if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)






