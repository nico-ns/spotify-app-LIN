#!/var/www/webApp/spot_venv/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 15:13:24 2021

@author: nicos
"""

from flask import Flask, redirect, render_template, request, url_for, session, flash
import base64
import requests
import numpy as np
import json
import math 
import timeit
import os
import codecs
from collections import Counter
from  itertools import chain
from ast import literal_eval
from num2words import num2words
import pandas as pd
from app.lastfm import lastfm_getinfo_v2 as lastfm
from app.charts import charts
from app.spotify import spotify_actions as sp
from app import app
import urllib
from urllib.parse import quote 

#  Client Keys
CLIENT_ID = os.environ["client_id"]
CLIENT_SECRET = os.environ["client_secret"]

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = os.environ["client_url"]
REDIRECT_URI = os.environ["redirect_url"]
SCOPE = os.environ["scopes"]
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}


os.chdir("/var/www/webApp")
# with open(log_path, "a") as file:
#     file.write(os.getcwd())

@app.route("/")
def home():
    return redirect(url_for("spotify"))

@app.route('/login_page')
def spotify():
    return render_template('login_page.html')

@app.route('/spotify_authentication')
def spotify_auth():
    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/lastfm_ok")
def last_fm():
    return render_template("lastfm_ok.html")
 
@app.route('/main_page')
def main_page():
    # print(session["user"])
    now = timeit.default_timer()
    
    if session.get("user") is None or now - session["start"] > session["expiration"]:
        # Authentication settings for spotify API
        auth_token = request.args['code']
        code_payload = {
            "grant_type": "authorization_code",
            "code": str(auth_token),
            "redirect_uri": REDIRECT_URI
        }
        
        base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET).encode())
        headers = {"Authorization": "Basic {}".format(base64encoded.decode())}
        post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)
    
        response_data = json.loads(post_request.text)
        access_token = response_data["access_token"]
        refresh_token = response_data["refresh_token"]
        token_type = response_data["token_type"]
        expires_in = response_data["expires_in"]
        print("access token =",access_token)
        
        session["token"] = access_token
    
        authorization_header = {"Authorization":"Bearer {}".format(access_token)}
    
        # Get profile data
        user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
        profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
        print(profile_response)
        profile_data = json.loads(profile_response.text)
        user_id = profile_data["id"]
        user_name = profile_data["display_name"] 
            
        session["user"] = user_id
        session["user_name"] = user_name
        session["profile_url"] = profile_data["external_urls"]["spotify"]
        try:
            session["user_image"] = profile_data["images"][0]["url"]
        except:
            pass
        session["expiration"] = expires_in
        session["start"] = timeit.default_timer()


        # Check if user already exist, if not creates a new folder for its data
        users = pd.read_csv("data/users.csv", encoding="latin1")
        if users[users["id"] == session["user"]].empty is True:
            os.mkdir(f"data/{user_id}")
            with codecs.open("data/users.csv", "a", "utf-8-sig") as file:
                user = f"\n{user_id},{user_name}"
                file.write(user)  
        
        LIMIT = 50
        
        
        # Get user liked songs playlist data
        liked_songs_data = sp.api_call(user_profile_api_endpoint, method='tracks', headers=authorization_header, params={'limit': LIMIT})
        sp.process_response(liked_songs_data, LIMIT, session["user"], endpoint=user_profile_api_endpoint, method='tracks', headers=authorization_header)                                                                                                
                
        #Get user playlist data
        playlists_data = sp.api_call(user_profile_api_endpoint, method='playlists', headers=authorization_header, params={'limit': LIMIT})
        print(playlists_data['total'])
        playlists_ids = sp.process_response(playlists_data,LIMIT, session["user"], endpoint=user_profile_api_endpoint, method='playlists', headers=authorization_header)
        print(playlists_ids)   
        
        #Get playlist tracks data
        k = 0
        print(len(playlists_ids))
        for _id in playlists_ids:
            k += 1
            # print(k)
            
            endpoint = "{}/playlists/{}".format(SPOTIFY_API_URL,_id)
            playlist_track_data = sp.api_call(endpoint, method='tracks', headers=authorization_header, params={'limit': LIMIT})
            # print(k)
            playlist_track_df = sp.process_response(playlist_track_data, LIMIT, session["user"], endpoint=endpoint, method='tracks_p', headers=authorization_header) 
            # print(k)
    
        # Get music stats from spotify
        all_tracks = pd.read_csv(f"data/{user_id}/tracks_data.csv")
    
        all_tracks = all_tracks.drop_duplicates()
        all_tracks = all_tracks.rename(columns={"track_id":"id"})
        all_tracks.to_csv(f"data/{user_id}/tracks_data.csv")
        track_ids = all_tracks["id"].to_list()
        
        # Get audio features from spotify
        songs_list = []
        for i in range(0,len(track_ids),100):
            print(len(track_ids))
            temp_id = track_ids[i:i+99]
            query = ",".join(map(str,temp_id))
            
            all_songs_api_endpoint = "{}/audio-features".format(SPOTIFY_API_URL)
            all_songs_response = requests.get(all_songs_api_endpoint, headers=authorization_header,
                                                params={'ids':query})        
            
            all_songs_data = all_songs_response.text
            all_songs_data = json.loads(all_songs_data)
            print(type(all_songs_data))
            for song in all_songs_data["audio_features"]:
                try:
                    tmp = [song["danceability"],song["energy"],song["key"],song["loudness"],
                            song["mode"],song["speechiness"],song["acousticness"],song["instrumentalness"],
                            song["liveness"],song["valence"],song["tempo"],song["type"],song["id"],
                            song["uri"],song["track_href"],song["analysis_url"],song["duration_ms"],
                            song["time_signature"]]
                    songs_list.append(tmp)
                except:
                    print("this object is none")
            all_songs_data = pd.DataFrame(songs_list, columns=["danceability","energy","key","loudness","mode","speechiness",
                                                                             "acousticness","instrumentalness","liveness","valence","tempo",
                                                                             "type","id","uri","track_href","analysis_url","duration_ms","time_signature"])
            #print(all_songs_data.head())
            all_songs_data = pd.merge(all_tracks, all_songs_data, on="id")
            all_songs_data = all_songs_data.drop_duplicates()
            
        artist_ids = all_songs_data["artist_id"].unique()
        
        #get genre for artists via spotify
        genres = []
        for i in range(0,len(artist_ids),50):
            api_string = ",".join(artist_ids[i:i+50])
            data = sp.api_call(SPOTIFY_API_URL,method="artists", headers=authorization_header, params={"limit":50,"ids": api_string})
            j = i
            for item  in data["artists"]:
                genres.append({"artist_id": item["id"], "genres": item["genres"]})
                j += 1
                
        #add genre data to complete dataframe
        genres_df = pd.DataFrame(data=genres, columns=["artist_id", "genres"])
        genres_df.to_csv(f"data/{user_id}/artist_genres.csv")
        all_songs_data = pd.merge(all_songs_data, genres_df, on="artist_id", how="left")
        all_songs_data.to_csv(f"data/{user_id}/tracks_data.csv")
        # all_songs_data.to_parquet(f"data/{user_id}/tracks_data.parquet")
        # all_songs_data.to_feather(f"data/{user_id}/tracks_data.feather")
    
        return render_template('main_page.html', session=session)
    
    elif now - session["start"] < session["expiration"]:
        return render_template('main_page.html', session=session)
    
    else:
        return redirect(url_for("spotify"))


@app.route("/music_stats")
def music_stats(): 
    # try:
    usr = session["user"]
    #lastfm.main_func(usr)
    print(usr)
    df = pd.read_csv(f"data/{usr}/tracks_data.csv")
    
    pos_neg = df["valence"].value_counts(bins=3, sort=True)
    pos_neg = pos_neg.values
    pos_neg = np.append(pos_neg, sum(pos_neg))
    tot_unique = len(df.index)
    
    liked_df = pd.read_csv(f"data/{usr}/tracks_data.csv")
    tot_liked = len(liked_df.index)
    
    playlists_df = pd.read_csv(f"data/{usr}/playlists.csv")
    tot_playlists = len(playlists_df.index)
    tot_in_playlists = sum(playlists_df["track_num"])
    
    top_3_artists = df["artist"].value_counts().nlargest(3, keep="first").index.tolist()
    
    top_3_genres = df["genres"].value_counts().nlargest(3, keep="first").index.tolist()
    
    data = pd.DataFrame(df.nlargest(3, columns= "loudness", keep="first"), columns=["artist", "track_name"]).to_dict()
    top_3_loudest = []
    for key in data["artist"]:
        top_3_loudest.append(f"{data['track_name'][key]} by {data['artist'][key]}") 
        
    df['pub_date'] = pd.to_datetime(df['pub_date'])
    df['pub_date'].apply(lambda x:x.toordinal())    
    data = pd.DataFrame(df.nsmallest(3, columns= "pub_date", keep="first"), columns=["artist", "track_name"]).to_dict()    
    top_3_oldest = []
    for key in data["artist"]:
        top_3_oldest.append(f"{data['track_name'][key]} by {data['artist'][key]}") 
        
    top_radar = []
    data = pd.DataFrame(df.nlargest(1, columns= "danceability", keep="first"), columns=["artist", "track_name"]).reset_index().to_dict()
    top_radar.append(f"Most danceable: {data['track_name'][0]} by {data['artist'][0]}")
    data = pd.DataFrame(df.nlargest(1, columns= "energy", keep="first"), columns=["artist", "track_name"]).reset_index().to_dict()
    top_radar.append(f"Least danceable: {data['track_name'][0]} by {data['artist'][0]}")
    data = pd.DataFrame(df.nsmallest(1, columns= "energy", keep="first"), columns=["artist", "track_name"]).reset_index().to_dict()
    top_radar.append(f"Most energetic: {data['track_name'][0]} by {data['artist'][0]}")
    data = pd.DataFrame(df.nsmallest(1, columns= "danceability", keep="first"), columns=["artist", "track_name"]).reset_index().to_dict()
    top_radar.append(f"Least energetic: {data['track_name'][0]} by {data['artist'][0]}")


   
            
    return render_template('music_stats.html', tot_unique=tot_unique, tot_liked=tot_liked, tot_playlists=tot_playlists, 
                           tot_in_playlists=tot_in_playlists, pos_neg=pos_neg, top_3_artists=top_3_artists,
                           top_3_genres=top_3_genres, top_3_loudest=top_3_loudest, top_3_oldest=top_3_oldest, top_radar=top_radar,
                           graphJSON=charts.bar_chart_artist(df), graphJSON3=charts.bar_chart_genre(df),
                           graphJSON4=charts.radar_chart(df), graphJSON2=charts.loudness_quantile(df),
                           graphJSON5=charts.age_chart(df))
    # except :
    #     return redirect(url_for("spotify"))

@app.route("/listening_stats")
def listening_stats():
    
    return render_template('listening_stats.html')

@app.route("/Seven7UpcomingupProductions")
def Seven7UpcomingupProductions():
    
    return render_template('Seven7UpcomingupProductions.html')

@app.route("/congrats")
def congrats():
    with open('data/congrats.log', 'r') as file:
        temp = file.read()
        temp = temp.strip()
        print("AAAAAAAAAAAAAAAAAAAAA", temp)
        temp = int(temp)
        n_th = temp + 1
    with open('data/congrats.log', 'w') as file:
        file.write(str(n_th))
        n_th = num2words(n_th, to="ordinal")

    return render_template("congrats.html", n_th=n_th)

@app.route("/music_curator", methods = ["POST", "GET"])
def music_curator():
    n_pl = 1   
    pl_dim = 15
    nsr = 0
    playlists = []
    
    # User input
    if request.method == "POST":
        pl_dim = int(request.form["tenda"])
        nsr = int(request.form["slider"])
        print(pl_dim,nsr)
        pl_gen = sp.PlaylistGenerator(playlists_number=n_pl, dimension=pl_dim, new_songs_percent=nsr,
                      access_token=session["token"],
                      user=session["user"])
        playlists = pl_gen.generate()
        # playlists = playlists*5
        print(playlists)

    
    
    return render_template('music_curator.html', playlists_dimension=pl_dim, new_songs_percent=nsr, playlists=playlists)

#POST call to apotify API to insert the new playlist in the user profile
@app.route("/import_playlist", methods=["POST","GET"])
def import_playlist():
    # Get the playlist information from the html form
    checked_items = request.form.getlist("check")
    checked_items = [literal_eval(item) for item in checked_items]
    print("check", checked_items)
    pl_name = request.form.getlist("pl_name")[0]
    pl_description = request.form.getlist("pl_description")[0]
    print("pl_name", pl_name)
    print("pl_descr", pl_description)
    request_body = json.dumps({
        "name": pl_name,
        "description": pl_description,
        "public": True
        })
    
    # Create playlist with user chosen name and description        
    url_create = SPOTIFY_API_URL+f"/users/{session['user']}/playlists"
    headers = {"Authorization":"Bearer {}".format(session["token"])}
    r = requests.post(url_create, data=request_body, headers=headers)
    print(r.status_code)
    
    #if create is successful add items
    if r.status_code == 201:
        playlist_id = r.json()["id"]
        
        uris = []
        for item in checked_items:
            uris.append(item["uri"])
        uris = {"uris": uris}
        url_add = SPOTIFY_API_URL+f"/playlists/{playlist_id}/tracks"
        request_body_add = json.dumps(uris)
        req = requests.post(url_add, headers=headers, data = request_body_add)
        print(req.status_code)
        
        if req.status_code == 201:
            temp = {"user_pl_name": pl_name, "pl_name": pl_description}
            data = {**temp, **uris} # This is dictionary merging (concatenation without repetition)
            sp.playlist_to_json(data, True, session["user"])
            return render_template('import_successful.html') # return (''), 204 if you want to do nothing
        elif r.status_code > 400:
            return render_template('import_unsuccessful.html')

    # else notify the user something went wrong
    elif r.status_code > 400:
        return render_template('import_unsuccessful.html')
    else:
        return render_template('import_unsuccessful.html')


