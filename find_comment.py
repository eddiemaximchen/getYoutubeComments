import requests
import json
import os
from googleapiclient.discovery import build

YOUTUBE_API_KEY = "Your key"
MOVIENAME='ironman4'
def main():
    youtube = build('youtube','v3',developerKey = 'AIzaSyCLNdL_6bmA5Gmqyp7u160DBZhF7iBqZ-s')
    request = youtube.search().list(q=MOVIENAME,part='snippet',type='comment',maxResults=50)
    #youtube==>find channelId  
    res = request.execute()
    myoutube = YoutubeSpider(YOUTUBE_API_KEY)
    #myoutube==>find comment
    for item in res['items']:
        youtube_channel_id = item['snippet']['channelId']
        uploads_id = myoutube.get_channel_uploads_id(youtube_channel_id)
        video_ids = myoutube.get_playlist(uploads_id, max_results=5)

        for video_id in video_ids:
            print("----------------------")
            video_info = myoutube.get_video(video_id)
            video_title=video_info['title'].replace('/','') 
            video_url=video_info['video_url']
            next_page_token = ''
            while 1:
                video_title, next_page_token = myoutube.get_comments(video_id,video_title,video_url,page_token=next_page_token)
                print(f"{video_title} is ok")
                # if no comment then escape
                if not next_page_token:
                    break
    comm=f"cat *.json | jq -s add >json/comments.json"
    os.system(comm)
    os.system("rm *.json")
    os.system("exit")
    print("comments.json is saved")

class YoutubeSpider():
    def __init__(self, api_key):
        self.base_url = "https://www.googleapis.com/youtube/v3/"
        self.api_key = api_key

    def get_html_to_json(self, path):
        api_url = f"{self.base_url}{path}&key={self.api_key}"
        r = requests.get(api_url)
        if r.status_code == requests.codes.ok:
            data = r.json()
        else:
            data = None
        return data

    def get_channel_uploads_id(self, channel_id, part='contentDetails'):
        path = f'channels?part={part}&id={channel_id}'
        data = self.get_html_to_json(path)
        try:
            uploads_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        except KeyError:
            uploads_id = None
        return uploads_id

    def get_playlist(self, playlist_id, part='contentDetails', max_results=10):
        path = f'playlistItems?part={part}&playlistId={playlist_id}&maxResults={max_results}'
        data = self.get_html_to_json(path)
        if not data:
            return []

        video_ids = []
        for data_item in data['items']:
            video_ids.append(data_item['contentDetails']['videoId'])
        return video_ids

    def get_video(self, video_id, part='snippet,statistics'):

        # part = 'contentDetails,id,liveStreamingDetails,localizations,player,recordingDetails,snippet,statistics,status,topicDetails'
        path = f'videos?part={part}&id={video_id}'
        data = self.get_html_to_json(path)
        if not data:
            return {}
        data_item = data['items'][0]

        url_ = f"https://www.youtube.com/watch?v={data_item['id']}"

        info = {
            #'id': data_item['id'],
            'channelTitle': data_item['snippet']['channelTitle'],
            'video_url': url_,
            'title': data_item['snippet']['title'],
            #'description': data_item['snippet']['description'],
            #'likeCount': data_item['statistics']['likeCount'],
            #'commentCount': data_item['statistics']['commentCount'], # will have NA and cause Error
            #'viewCount': data_item['statistics']['viewCount']
        }
        return info

    def get_comments(self, video_id,video_title,video_url, page_token='', part='snippet', max_results=100):
        path = f'commentThreads?part={part}&videoId={video_id}&maxResults={max_results}&pageToken={page_token}'
        data = self.get_html_to_json(path)
        if not data:
            return [], ''
        next_page_token = data.get('nextPageToken', '')

        # prepare json file
        comments = []
        count=0
        prev_id=''
        prev_comt=''
        for data_item in data['items']:
            data_item = data_item['snippet']
            top_comment = data_item['topLevelComment']

            if 'authorChannelId' in top_comment['snippet']:
                ru_id = top_comment['snippet']['authorChannelId']['value']
            else:
                ru_id = ''

            ru_name = top_comment['snippet'].get('authorDisplayName', '')
            if not ru_name:
                ru_name = ''

            comments.append({
                #'reply_id': top_comment['id'],
                'movie_name':video_title,
                'movie_url':video_url,
                'ru_id': ru_id,
                #'ru_name': ru_name,
                'reply_content': top_comment['snippet']['textOriginal'],
                #'rm_positive': int(top_comment['snippet']['likeCount']),
                'rn_comment': int(data_item['totalReplyCount'])#回覆的回覆
            })
            if prev_id==ru_id and prev_comt==top_comment['snippet']['textOriginal']: #prevent redundent in the same video
                continue 
            else:
                with open(f"{count}.json", "w", encoding="utf-8") as file:
                    file.write(json.dumps(comments, ensure_ascii=False, indent=4))
            prev_id=ru_id
            prev_comt=top_comment['snippet']['textOriginal']
            count=count+1 #these file is temp file and will combine in the end and file name can be too long causing saving problem,therefore use count.
        return video_title, next_page_token


if __name__ == "__main__":
    main()
