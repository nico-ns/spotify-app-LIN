from app import app
import math

@app.template_filter()
def username(session):
    try:
        return session["user_name"]
    except:
        return session["user"]
    
@app.template_filter()
def rows(playlists):
    x = len(playlists)
    y = math.ceil(x/3)
    return y

@app.template_filter()
def appr(x):
    print("x: ", x)
    fl = math.floor(x)
    print("floor: ", fl)
    if x - fl >= 0.5:
        print("return: ", math.ceil(x))
        return math.ceil(x)
    else:
        print("return: ", fl)
        return math.floor(x)


@app.template_filter()
def modulo(playlists):
    x = len(playlists)
    y = x % 3
    return y

@app.template_filter()
def debug(x):
    print(x)
    return ''