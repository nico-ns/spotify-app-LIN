# -*- coding: utf-8 -*-
import requests
import json
import pandas as pd
import math
from collections import Counter
from  itertools import chain
from ast import literal_eval
import random
from datetime import datetime

def get_now_string():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d_%m_%Y-%H_%M_%S")
    return timestampStr

def api_call(api_endpoint,method, headers, params):
    api_endpoint = "{}/{}".format(api_endpoint, method)
    api_response = requests.get(api_endpoint, headers=headers, 
                                        params = params)
    print(api_endpoint)
    data = api_response.text
    try:
        data = json.loads(data)
        if method == "playlists":
            with open(r"C:\Users\nicos\spotify_sentiment_analysis\data\nico.sama.ns\playlists.json","w") as file:
                json.dump(data, file, indent=4, sort_keys=False)
    except:
        print("missing data")
        print(data)
        print(api_endpoint)
    return data

def save_data(data_list, user_id, method):
    if method=="tracks":
        print("tracks")
        data_df = pd.DataFrame(data_list, columns=['date', 'track_name', 'artist', 'artist_id', 'cover_image', 'album_name', 'URL', 'track_id', 'pub_date'])
        data_df.to_csv(f"data/{user_id}/liked_songs.csv", encoding='utf-8')
        with open(f"data/{user_id}/tracks_data.csv","w") as file:
            data_df.to_csv(f"data/{user_id}/tracks_data.csv",encoding='utf-8',mode="w" ,header=data_df.columns, index=False)
        return data_df
    elif method=="playlists":
        playlists_df = pd.DataFrame(data_list, columns=['Name', 'playlist_id', 'track_num'])
        playlists_ids = playlists_df["playlist_id"].tolist()
        playlists_df.to_csv(f"data/{user_id}/playlists.csv",encoding='utf-8')
        return playlists_ids
    elif method == "tracks_p":
        print("track_p")
        playlist_track_df = pd.DataFrame(data_list, columns=['date', 'track_name', 'artist', 'artist_id', 'cover_image', 'album_name', 'URL', 'track_id', 'pub_date'])
        playlist_track_df.to_csv(f"data/{user_id}.csv", encoding='utf-8')
        user_id = user_id[:user_id.index("/")]
        with open(f"data/{user_id}/tracks_data.csv", "a", encoding='utf-8') as file:
            playlist_track_df.to_csv(file,header=False, index=False)
        return playlist_track_df
    
# def append_data(data_list):
#     data_df = pd.DataFrame(data_list, columns=['date', 'track_name', 'artist', 'artist_id', 'cover_image', 'album_name', 'URL', 'track_id', 'genres'])
#     data_df.to_csv(f"data/{user_id}/data.csv", mode='a', header=False)
#     data_df.to_csv(f"data/{user_id}/tracks_data.csv", columns=['date', 'track_name', 'artist', 'artist_id', 'cover_image', 'album_name', 'URL', 'track_id', 'genres'], index=False)

def playlist_to_json(playlist: dict, imported: bool, user_id: str):
    now = get_now_string()
    if imported == False:
        with open(f"data/{user_id}/pl_generated_{now}.json", "w") as file:
            json.dump(playlist, file)
    else:
        with open(f"data/{user_id}/pl_imported_{now}.json", "w") as file:
            json.dump(playlist, file)
            
    
def correct_func(method):
    if method=="tracks":
        return get_tracks_infos
    elif method=="playlists":
        return get_playlists_info

def process_response(data: json, limit: int, user_id: str, endpoint, method, headers):

    len_data = data['total']
    data = data['items']
    r_method = method
    if r_method=="tracks_p":
        method = "tracks"
        user_id = user_id+"/playlist_track_"+endpoint[endpoint.rindex("/")+1:]
    
    get_infos = correct_func(method)
    print(len_data)
    
    if len_data <= limit:
        data_list = get_infos(data)
        # if r_method=="tracks_p":
            # print(data_list, user_id, r_method)
        data_df = save_data(data_list, user_id, r_method)
        print("if")
        
    else:
        data_list = get_infos(data)
        print("else")
        
        for i in range(math.ceil(len_data/int(limit))):
            
            offset = limit*(i+1)+1
            params = {'limit': limit, 'offset': offset}
            data = api_call(endpoint, method, headers, params)
            
            data = data['items']
            
            data_list = data_list + get_infos(data)

            if i == math.ceil(len_data/int(limit))-1:   
                data_df = save_data(data_list, user_id, r_method)   
    return data_df


def get_tracks_infos(df):
    song_list = []
    for i in df:
        song = [None]*9
        try:
            song[0] = i['added_at'][:-10]
        except:
            pass
        try:
            song[1] = i['track']['name']
        except:
            pass
        try:
            song[2] = i['track']['artists'][0]['name']
        except:
            pass
        try:
            song[3] = i['track']['artists'][0]['id']
        except:
            pass
        try:
            song[4] = i['track']['album']['images'][0]['url']
        except:
            pass
        try:
            song[5] = i['track']['album']['name']
        except:
            pass
        try:
            song[6] = i['track']['external_urls']['spotify']
        except:
            pass
        try:
            song[7] = i['track']['id']
        except:
            pass
        try:
            song[8] = i['track']['album']['release_date']
        except:
            pass
        song_list.append(song)
    
    return song_list

def get_playlists_info(df):
    playlists_list = []
        
    for i in df:
        tmp = [i['name'], i['id'], i['tracks']['total']]
        playlists_list.append(tmp)
        
    return playlists_list


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
        self.user = user
        self.endpoint = f"{PlaylistGenerator.SPOTIFY_API_URL}"
        self.method = "recommendations"
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.params = {'limit': self.newSongs*2}
        # self.df = pd.read_csv(r"C:\Users\nicos\spotify_sentiment_analysis\data\nico.sama.ns\tracks_data.csv",converters={"genres": literal_eval})
        self.df = pd.read_csv(f"data/{user}/tracks_data.csv", converters={"genres": literal_eval})
        self.playlists = []
        
        # if self.plNum > 6:
        #     self.playlist_names = ["Very danceable", "Lots of energy", "Positive message", "Negative message", "Before sleeping",
        #                            "Relaxing/Meditation", "focus_like", "Tempo crescendo", "User-generated1"]
        # else:
        #     self.playlist_names = ["Very danceable", "Lots of energy", "Positive message", "Negative message","Before sleeping",
        #                            "Relaxing/Meditation", "focus_like", "Tempo crescendo"]
        self.playlist_names = ["Very danceable", "Lots of energy", "Positive message", "Negative message","Before sleeping",
                                   "Relaxing/Meditation", "Focusing", "Tempo crescendo"]
        self.plNum = len(self.playlist_names)

        
            
    def generate(self):
        # Plyalist generation
        for i in range(self.plNum):
            # Assign playlist name
            self.playlists.append({"pl_name": self.playlist_names[i], 
                                   "items": []})
            # Get dataframes of selected songs for the playlist
            print("GENERATING......")
            print(i)
            print(self.playlists[i]["pl_name"])
            selected_recommended_songs, selected_user_songs = self.get_tracks(self.playlists[i]["pl_name"])
            selected_playlist = selected_user_songs.append(selected_recommended_songs)
            print(selected_playlist)
            #Get playlists as dictionary
            for index, row in selected_playlist.iterrows():
                self.playlists[i]["items"].append({"name": row["track_name"], "artist": row["artist"], "id": row["id"], "uri": row["uri"],})
            
            playlist_to_json(self.playlists, False, self.user)
        return self.playlists
    
    def get_recommended_songs(self, df, parameter: str, largest: bool):
        #select seed songs and artists for a particular api call
        if largest == True:
            seed_songs = df.nlargest(3, parameter)
        elif largest == False:
            seed_songs = df.nsmallest(3, parameter)
        elif largest == None:
            seed_songs = df.sample(3)
        seed_artists = df["artist_id"].value_counts()
        seed_genres = pd.Series(Counter(chain(*df.genres))).sort_index().rename_axis('genres').reset_index(name='f')
        
        #Sample from possible seeds to get the parameters for api call
        j = random.randint(1,2)
        k = random.randint(1,2)
        seed_genre = seed_genres.nlargest(2*j, "f").sample(j).genres.tolist()
        seed_artist = seed_artists.sample(k).index.tolist()
        try:
            seed_song = seed_songs.sample(5-k-j)["id"].tolist()
        except :
            seed_song = ""
    
    
        #Set the parameters for the api call
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
            temp = [item['name'], item['id'], item['artists'][0]['name'], item['artists'][0]['id'], item['uri']]
            data.append(temp)
            i += 1
                            
        df2 = pd.DataFrame(data=data,columns=["track_name", "id", "artist", "artist_id", "uri"])
        selected_recommended_songs = df2.sample(self.newSongs)
        
        self.reset_params()
    
        return selected_recommended_songs
    
    def reset_params(self):
        del self.params["seed_artists"]
        del self.params["seed_genres"]
        del self.params["seed_tracks"]

            
    def get_tracks(self, playlist_name):
        if playlist_name == "Very danceable":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "danceability", "genres"])
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
            
            if self.newSongs > 0:
                self.params["min_danceability"] = mean_dance + 0.2*(max_dance - mean_dance)
                selected_recommended_songs = self.get_recommended_songs(df, "danceability", largest=True)
                del self.params["min_danceability"]
            else:
                selected_recommended_songs = []
        
            
        
        # Other elif with same structure for other playlists
        elif playlist_name == "Lots of energy":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "energy", "genres"])
            mean_energy = df["energy"].mean()
            max_energy = df["energy"].max()
            min_energy = df["energy"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            print(df)
            df = df.nlargest(self.userSongs*2,"energy")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["energy", "genres"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            
            if self.newSongs > 0:
                self.params["min_energy"] = mean_energy + 0.2*(max_energy - mean_energy)
                selected_recommended_songs = self.get_recommended_songs(df, "energy", largest=True)
                del self.params["min_energy"]
            else:
                selected_recommended_songs = []
            
        
        
        elif playlist_name == "Positive message":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "valence", "genres"])
            mean_valence = df["valence"].mean()
            max_valence = df["valence"].max()
            min_valence = df["valence"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            print(df)
            df = df.nlargest(self.userSongs*2,"valence")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["valence", "genres"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")

            if self.newSongs > 0:
                self.params["min_valence"] = mean_valence + 0.2*(max_valence - mean_valence)
                selected_recommended_songs = self.get_recommended_songs(df, "valence", largest=True)
                del self.params["min_valence"]
            else:
                selected_recommended_songs = []
        
        
        
        elif playlist_name == "Negative message":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "valence", "genres"])
            mean_valence = df["valence"].mean()
            max_valence = df["valence"].max()
            min_valence = df["valence"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            print(df)
            df = df.nsmallest(self.userSongs*2,"valence")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["valence", "genres"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            
            if self.newSongs > 0:
                self.params["max_valence"] = mean_valence
                selected_recommended_songs = self.get_recommended_songs(df, "valence", largest=False)
                del self.params["max_valence"]
            else:
                selected_recommended_songs = []
            
            
            
        elif playlist_name == "Before sleeping":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "energy", "genres", "instrumentalness"])
            mean_instrumentalness = df["instrumentalness"].mean()
            max_instrumentalness = df["instrumentalness"].max()
            min_instrumentalness = df["instrumentalness"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            df = df.nlargest(self.userSongs*3, "instrumentalness")
            max_energy = df["energy"].max()
            print(df)
            df = df.nsmallest(self.userSongs*2,"energy")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["energy", "genres", "instrumentalness"], axis=1)
            
            if self.newSongs > 0:
                self.params["max_instrumentalness"] = mean_instrumentalness + 0.1*(max_instrumentalness - mean_instrumentalness)
                self.params["max_energy"] = max_energy
                selected_recommended_songs = self.get_recommended_songs(df, "energy", largest=False)
                del self.params["max_instrumentalness"] 
                del self.params["max_energy"]
            else:
                selected_recommended_songs = []
            
        
        elif playlist_name == "Relaxing/Meditation":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "energy", "genres"])
            mean_energy = df["energy"].mean()
            max_energy = df["energy"].max()
            min_energy = df["energy"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            print(df)
            df = df.nsmallest(self.userSongs*2,"energy")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["energy", "genres"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            
            if self.newSongs > 0:
                self.params["max_energy"] = mean_energy + 0.1*(max_energy - mean_energy)
                selected_recommended_songs = self.get_recommended_songs(df, "energy", largest=False)
                del self.params["max_energy"]
            else:
                selected_recommended_songs = []
            
        elif playlist_name == "Focusing":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "energy", "genres"])
            mean_energy = df["energy"].mean()
            max_energy = df["energy"].max()
            min_energy = df["energy"].min()
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            print(df)
            df = df.nsmallest(self.userSongs*2,"energy")
            print(df)
            selected_user_songs = df.sample(self.userSongs)
            # selected_user_songss = selected_user_songs.to_dict()
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            selected_user_songs = selected_user_songs.drop(["energy", "genres"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            
            if self.newSongs > 0:
                self.params["max_energy"] = mean_energy + 0.1*(max_energy - mean_energy)
                selected_recommended_songs = self.get_recommended_songs(df, "energy", largest=False)
                del self.params["max_energy"]
            else:
                selected_recommended_songs = []
            
        
        elif playlist_name == "Tempo crescendo":
            #First you get the possible tracks from the user data and extract some features
            
            #↨select relevant columns from df
            df = pd.DataFrame(self.df, columns=["track_name", "id", "artist", "artist_id", "uri", "energy", "genres", "tempo"])
            mean_tempo = df["tempo"].mean()
            max_tempo = df["tempo"].max()
            min_tempo = df["tempo"].min()
            user_songs = self.userSongs
            bins = [min_tempo + ((max_tempo - min_tempo)/4)*i  for i in range(5)]
            average_songs_per_b = math.floor(user_songs/4)
            songs_per_bin = [average_songs_per_b - math.floor(0.6*average_songs_per_b),
                             average_songs_per_b + math.floor(0.2*average_songs_per_b),
                             average_songs_per_b + math.floor(0.9*average_songs_per_b)]
            
            songs_per_bin.append(user_songs - sum(songs_per_bin))
            for i in range(len(bins)-1):
                df2 = df.loc[(df["tempo"]>= bins[i]) & (df["tempo"]<=bins[i+1])]
                if i == 0:
                    selected_user_songs = df2.sample(songs_per_bin[i])
                elif i == 1:
                    temp = df2.sample(songs_per_bin[i])
                    selected_user_songs = pd.concat([selected_user_songs, temp], ignore_index=True)
                elif i == 2:
                    temp = df2.sample(songs_per_bin[i])
                    selected_user_songs = pd.concat([selected_user_songs, temp], ignore_index=True)
                elif i == 3:
                    temp = df2.sample(songs_per_bin[i])
                    selected_user_songs = pd.concat([selected_user_songs, temp], ignore_index=True)            
            
            #randomly selects n songs to insert in the playlist from 2n of the most danceble stuff in df
            selected_user_songs = selected_user_songs.drop(["energy", "genres", "tempo"], axis=1)
            print("AAAAAAAAAA \n",selected_user_songs, "\n AAAAAAAAAAAAAAA")
            
            # if self.newSongs > 0:
            #     self.params["min_tempo"] = mean_tempo - 0.2*(mean_tempo - min_tempo)
            #     self.params["max_tempo"] = mean_tempo + 0.2*(max_tempo - mean_tempo)
            #     selected_recommended_songs = self.get_recommended_songs(selected_user_songs, "energy", largest=None)
            #     del self.params["min_energy"]
            # else:
            #     selected_recommended_songs = []
            selected_recommended_songs = []

            
        return selected_recommended_songs, selected_user_songs


# In order to add new playlists, this is the list of operations on the code you need to perform
# - add the new playlist name to self.playlist_names in the __ini__ of PlaylistGenerator
# - Copy-paste the content in the first of the generate() function in a new elif
# - change the condition into if playlist_name == "new name"
# - change danceability everywhere with the new parameter (e.g. valence)
# - for more complicated playlists (more than one parameter)................