from __future__ import division
from flask import Flask, render_template, send_file, make_response, request, redirect, url_for
import spotipy
import spotipy.util as util
import numpy as np
import pandas as pd
import pickle

from cStringIO import StringIO
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(rc={'axes.facecolor':'black', 'figure.facecolor':'black', 'axes.grid' : False})

app = Flask(__name__)

# Setting up spotify tokens and authorization - hidden for github, use own tokens
token = util.prompt_for_user_token(<INSERT SPOTIFY USERNAME>,
                                   client_id=<INSERT SPOTIFY CLIENT ID>,
                                   client_secret=<INSERT SPOTIFY CLIENT SECRET>,
                                   redirect_uri=<INSERT REDIRECT URI>)

spotify = spotipy.Spotify(auth=token)

master_df = pd.read_pickle('../data/master_df.pkl')

mood_map = {'Peaceful': (-2,2), 'Easygoing': (-1,2), 'Tender': (-2,1), 'Romantic': (-1,1), 
        'Upbeat': (0,2), 'Empowering': (0,1),
        'Lively': (1,2), 'Excited': (2,2), 'Stirring': (1,1), 'Rowdy': (2,1),
        'Sentimental': (-2,0), 'Sophisticated': (-1,0),
        'Sensual': (0,0), 
        'Fiery': (1,0), 'Energizing': (2,0),
        'Melancholy': (-2,-1), 'Cool': (-1,-1), 'Somber': (-2,-2), 'Gritty': (-1,-2),
        'Yearning': (0,-1), 'Serious': (0,-2),
        'Urgent': (1,-1), 'Defiant': (2,-1), 'Brooding': (1,-2), 'Aggressive': (2,-2)}

reverse_mood_map = {v: k for k, v in mood_map.items()}

def get_reverse_mood_map(x): 
    return reverse_mood_map[x]
    
def get_mood_map(x):
    return mood_map[x]

# get song ids from list of playlist ids
def get_songs(playlists):
    song_ids = []
    for i in playlists:
        try:
            for j in spotify.user_playlist('spotify', i)['tracks']['items']:
                song_ids.append(j['track']['id'])
        except:
            pass
    return song_ids

@app.route('/')
def my_form():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def my_form_post():
    playlist = request.form['text']
    return redirect(url_for('mood_maker', a=playlist), code=302)

@app.route('/<a>/')
def mood_maker(a):
    name = spotify.user_playlist('spotify', a)['name']
    songs = get_songs([a]) 
    songs_df = master_df[master_df['id'].isin(songs)]

    n = songs_df['mood_predict_map'].value_counts()
    nplus = pd.DataFrame(n).reset_index()
    nplus['mood'] = nplus['index'].apply(get_reverse_mood_map)
    nplus.columns = ['coord', 'value', 'mood']

    plus = len(songs_df)

    colors = iter(cm.rainbow(np.linspace(0, 1, len(n))))
    fig = plt.figure(dpi = 300, figsize=(8,5))
    axes = fig.add_subplot(1, 1, 1)

    for index, items in nplus.iterrows():
        axes.plot(items[0][0], items[0][1], marker='h', markersize = items[1]/plus*600, alpha=0.65, label=items[2],
                 color=next(colors)) 
   
    axes.set_title(name)
    axes.set_xlim(-3, 3)
    axes.set_ylim(-3, 3)
    axes.set_xticklabels([]) 
    axes.set_yticklabels([])
    
    for k, v in reverse_mood_map.iteritems():
        plt.annotate(v, k, ha='center', size=10, alpha=1, color='white')
    
    f = StringIO()
    plt.savefig(f, format='png')

    # Serve up the data
    header = {'Content-type': 'image/png'}
    f.seek(0)
    data = f.read()

    return data, 200, header

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8890, debug=True)
