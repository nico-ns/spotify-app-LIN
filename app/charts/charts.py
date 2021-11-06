# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 14:55:32 2021

function for plot generation after the data_fetching in the main_page 
has been successful.
They are mainly for music_stats page and listening_stats page

@author: nicos
"""
import pandas as pd
import plotly
import plotly.express as px
import json
import numpy as np

def bar_chart_artist( music_df):
    
    bar_data = music_df.groupby("artist").filter(lambda x: len(x)>4)
    fig = px.bar(bar_data, x="artist", title="most frequent artist", hover_data=["track_name"])

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def bar_chart_genre( music_df):
    
    bar_data = music_df.groupby("genres").filter(lambda x: len(x)>10)
    fig = px.bar(bar_data, x="genres", title="most frequent genres")

    graphJSON3 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON3

def loudness_quantile( music_df):
    
    bar_data = music_df.groupby(pd.cut(music_df["loudness"], np.percentile(music_df["loudness"], [0, 25, 75, 90, 100]), include_lowest=True)).count()
    bar_data = bar_data.astype({"loudness":str})
    bar_data.at[0,"loudness"] = "0-25 loudness"
    bar_data.at[1,"loudness"] = "25-75 loudness"
    bar_data.at[2,"loudness"] = "75-90 loudness"
    bar_data.at[3,"loudness"] = "90-100 loudness"
    print(bar_data.head())
    print(bar_data.columns)
    print(bar_data["loudness"])
    fig = px.bar(bar_data, x="loudness", y="track_name", title="How loud is your music?", labels={"track_name":"count"})

    graphJSON2 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON2

def radar_chart( music_df):

    fields = ["danceability", "energy", "speechiness", "liveness", "instrumentalness", "acousticness"]
    fields2 = ["key", "mode", "tempo", "loudness"]
    chart_data = pd.DataFrame(dict(x=[music_df[k].mean() for k in fields ], theta=fields))
    fig = px.line_polar(chart_data, r="x", theta="theta",line_close=True,title="Average attributes")
    
    graphJSON4 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON4

def age_chart( music_df):
    
    line_data = pd.DataFrame(music_df, columns=["pub_date", "track_name", "artist", "id"])
    fig = px.histogram(line_data, x="pub_date", title='How old is your music?')

    graphJSON5 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON5
