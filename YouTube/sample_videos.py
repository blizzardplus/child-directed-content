import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import json
from pandas.io.json import json_normalize  

CLIENT_SECRETS_FILE = "client_secrets.json"
RANKINGS_DIRECTORY = "./Category Rankings"

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

def setupAPI():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    
    ## Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    return youtube

def getCategories(youtubeAPI):
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode="US"
    )
    response = request.execute()
    return response

def loadCategories():
    file = open("ytCategories.json")
    ytCategories = processResponse(file)

def getMostPopularVideos(youtubeAPI, youtubeCategoryID):
    try:
      request = youtube.videos().list(
                  part="snippet,contentDetails,statistics",
                  chart="mostPopular",
                  maxResults=50,
                  regionCode="US",
                  videoCategoryId=str(youtubeCategoryID)
              )
      response = request.execute()
    except:
      print("Request failed")
    return response

def getAllMostPopularVideos(youtubeAPI, youtubeCategories):
    for categoryID in youtubeCategories["id"]:
      getMostPopularVideos(youtubeAPI, categoryID)

def loadMostPopularVideos():
    mpVideos = list()
    for file in os.listdir(RANKINGS_DIRECTORY):
      if file.endswith(".json"):
          jsonFile = open(RANKINGS_DIRECTORY + "/" + file)
          indexName = ''.join(e for e in file.replace(".json", "") if e.isalnum())
          mpVideos.append(processResponse(jsonFile))
    return mpVideos


def processResponse(jsonReponse):
    data = json.load(jsonReponse)
    items = pd.DataFrame(data["items"])
    dfResponse = json_normalize(items["snippet"])
    dfResponse["id"] = items["id"]
    return dfResponse

def main():
    youtubeAPI = setupAPI()
    
    mpVideos = loadMostPopularVideos()
    print(mpVideos)
    
if __name__ == "__main__":
    main()
