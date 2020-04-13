import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import json
import webbrowser
from os import path
from pandas import json_normalize  

CLIENT_SECRETS_FILE = "client_secrets.json"
RANKINGS_DIRECTORY = "./Category Rankings"
NUMBER_OF_VIDEOS_TO_SAMPLE_PER_CATEGORY = 10
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

def questionnaire(id):
    print("\n\nVideo: " + id + "\n")
    print("1. Child Directed")
    print("2. Mixed Content")
    print("3. Not Child Directed\n")

    intTag = None
    while(True):
      tag = input("Tag: ")
      try:
        if int(tag) in range(1,4):
          intTag = int(tag)
          break
        else:
          print("Error!!! Value out of range")
      except:
        print("Error!!! Integer not entered")

    return intTag


def generateViewerHTML(id, description):
    viewerHTML = """<h1>{}</h1><iframe width="560" height="315" src="https://www.youtube.com/embed/{}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe> <br> <br> <p>{}</p>""".format(id, id, description) 
    
    f = open("viewer.html", "w")
    f.write(viewerHTML)
    f.close()

    webbrowser.open("./viewer.html", new=2)
    

def viewer(mpVideos):
    if path.exists('result.json'):
      result = pd.read_json(r'result.json')
    else:
      result = pd.DataFrame()
      result["id"] = None
      result["tag"] = None

    ids = list()
    descriptions = list()
    for category in mpVideos:
      for index in range(0, NUMBER_OF_VIDEOS_TO_SAMPLE_PER_CATEGORY):
        ids.append(category["id"][index])
        descriptions.append(category["description"][index])
    
    for index in range(len(ids)):
      id = ids[index]
      description = descriptions[index]
      
      if result["id"].str.contains(id).any():
        continue

      generateViewerHTML(id, description)

      tag = questionnaire(id)

      result = result.append({'id':id, 'tag':tag}, ignore_index=True)

      result.to_json(r'result.json')



def main():
    #youtubeAPI = setupAPI()

    mpVideos = loadMostPopularVideos()
    viewer(mpVideos)

if __name__ == "__main__":
    main()
