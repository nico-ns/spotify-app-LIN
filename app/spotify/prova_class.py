import requests
import json
import pandas as pd
import math
import random
from collections import Counter
from  itertools import chain
from ast import literal_eval


def api_call(api_endpoint,method, headers, params):
    api_endpoint = "{}/{}".format(api_endpoint, method)
    api_response = requests.get(api_endpoint, headers=headers, 
                                        params = params)
    print(api_endpoint)
    data = api_response.text
    try:
        data = json.loads(data)
    except:
        print("missing data")
        print(data)
        print(api_endpoint)
    return data

class PlaylistGenerator:
    SPOTIFY_API_BASE_URL = "https://api.spotify.com"
    API_VERSION = "v1"
    SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

    def __init__(self, playlists_number: int, dimension: int, new_songs_percent: int, access_token: str, user: str):
        self.n_pl = 6 # Number of playlist to generate
        self.plNum = playlists_number # Actual number of playlist to generate (specific user input overrides self.n_pl)
        self.newRatio = new_songs_percent/100
        self.newSongs = math.floor(self.newRatio*dimension)       
        self.userSongs = dimension - self.newSongs
        self.endpoint = f"{PlaylistGenerator.SPOTIFY_API_URL}"
        self.method = "recommendations"
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.params = {'limit': self.newSongs*2}
        self.df = pd.read_csv(r"C:\Users\nicos\spotify_sentiment_analysis\data\nico.sama.ns\tracks_data.csv",converters={"genres": literal_eval})
        # self.df = pd.read_csv(f"data/{user}/tracks_data.csv")
        self.playlists = []
        
        if self.plNum > 6:
            self.playlist_names = ["dance-like," "User-generated1"]
        else:
            self.playlist_names = ["dance-like"]
        
            
    def generate(self):
        # Plyalist generation
        for i in range(self.plNum):
            # Assign playlist name
            self.playlists.append({"pl_name": self.playlist_names[i], 
                                   "items": []})
            # Get dataframes of selected songs for the playlist
            selected_recommended_songs, selected_user_songs = self.get_tracks(self.playlists[i]["pl_name"])
            selected_playlist = selected_user_songs.append(selected_recommended_songs)
            print(selected_playlist)
            #Get playlists as dictionary
            for index, row in selected_playlist.iterrows():
                self.playlists[i]["items"].append({"name": row["track_name"], "artist": row["artist"], "id": row["id"]})
                
        return self.playlists

            
    def get_tracks(self, playlist_name):
        if playlist_name == "dance-like":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "danceability", "genres"])
            mean_dance = df["danceability"].mean()
            max_dance = df["danceability"].max()
            min_dance = df["danceability"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            print(df)
            df = df.nlargest(self.userSongs*2,"danceability")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["danceability", "genres"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            
            #select seed songs and artists for a particular api call
            seed_songs = df.nlargest(3, "danceability")
            seed_artists = df["artist_id"].value_counts()
            seed_genres = pd.Series(Counter(chain(*df.genres))).sort_index().rename_axis('genres').reset_index(name='f')
            
            #Sample from possible seeds to get the parameters for api call
            j = random.randint(1,3)
            k = random.randint(1,2)
            seed_genre = seed_genres.nlargest(2*j, "f").sample(j).genres.tolist()
            seed_artist = seed_artists.sample(k).index.tolist()
            try:
                seed_song = seed_songs.sample(5-k-j)["id"].tolist()
            except :
                seed_song = ""
        
        
            #Set the parameters for the api call
            self.params["min_danceability"] = mean_dance + 0.2*(max_dance - mean_dance)
            self.params["seed_artists"] = ",".join(seed_artist)
            self.params["seed_genres"] = ",".join(seed_genre)
            self.params["seed_tracks"] = ",".join(seed_song)
           
            print(self.params)
            
            # perform GET call and process response
            api_response = api_call(self.endpoint,self.method,self.headers,self.params)
            i = 0
            data = []
            # print(api_response)
            for item in api_response["tracks"]:
                # print(item)
                print(type(item))
                print(item["name"])
                temp = [item['name'], item['id'], item['artists'][0]['name'], item['artists'][0]['id']]
                data.append(temp)
                i += 1
                                
            df2 = pd.DataFrame(data=data,columns=["track_name", "id", "artist", "artist_id"])
            selected_recommended_songs = df2.sample(self.newSongs)
        
        # Other elif with same structure for other playlists
            
        return selected_recommended_songs, selected_user_songs



p = PlaylistGenerator(playlists_number=1, dimension=15, new_songs_percent=30,
                      access_token="BQB53EGyQmCW-3OcD5QgKcFC-YRw7-agN6l33uk3sWYoChKdB5PWVB5q4CE6oTWV8wd0BeLfofJl-w_ZuQACp3AB7gPSg8FxRTOSGP3tTburb1Jbojk1fAiZJJ_uksa0wEGVyXig9A3i2ibexjnnhw6iaH91zXmisBHx1doBHjIRXCpg1-I",
                      user="nico.sama.ns")
g = p.generate()
print(g)
print(type(g))