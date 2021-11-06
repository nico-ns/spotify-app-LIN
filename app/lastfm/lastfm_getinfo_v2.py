# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 01:00:34 2021

@author: nicos
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 20:18:41 2021

@author: nicos
"""

import requests
import pandas as pd
import json
import numpy as np

def lastfm_get(payload):
    # define headers and URL
    
    API_ROOT = "http://ws.audioscrobbler.com/2.0/"
    USER_AGENT = 'nicos'
    
    headers = {
        'user-agent': USER_AGENT
        }

    response = requests.get(API_ROOT, headers=headers, params=payload)
    response_data = response.text
    try:
        response_data = json.loads(response_data)
    except:
        print(response_data)
        print(payload)
    return response_data

def main_func(user_id):
    
    API_KEY = '3369184f1ba7b4155820c8785efdae83'
    
    csv = pd.read_csv(f"data/{user_id}/tracks_data2.csv")
    data=[csv["track_name"], csv["id"], csv["artist"]]
    music_df = pd.concat(data, axis=1, keys=["track_name","id","artist"])
    music_df = music_df.drop_duplicates()
    
    music_genre = []
    music_tags = []
    # pub_date = []
    
    for index,row in music_df.iterrows():
        if row["track_name"].lower().find("remaster")>0 or row["track_name"].lower().find("live")>0:
            try:
                row["track_name"] = row["track_name"][:row["track_name"].index("-")-1]
            except:
                print(row["track_name"])
        payload = {    'api_key': API_KEY,
        'method': 'track.getTopTags',
        'format': 'json',
        'artist': f'{row["artist"]}',
        'track': f'{row["track_name"]}'}
        
        music_data = lastfm_get(payload)
        
        try:
            music_genre.append(music_data["toptags"]["tag"][0]["name"])
        except:
            music_genre.append(None)
            
        temp = []
        try:
            for i in range(len(music_data["toptags"]["tag"])):
                try:
                    temp.append(music_data["toptags"]["tag"][i]["name"])
                except:
                    if i == 0:
                        temp.append([None])
                    else:
                        pass
            music_tags.append(temp)
        except:
            music_tags.append([None])
    
    music_genre = pd.Series(music_genre)
    music_tags = pd.Series(music_tags)
    
    music_df["genre"] = music_genre
    music_df["tags"] = music_tags
    
    music_df = music_df.drop(columns=["track_name","artist"])
    
    music_df = pd.merge(csv,music_df, on="id")
    
    music_df.to_csv(f"data/{user_id}/tracks_data5.csv")
    
     



    