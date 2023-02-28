# setup
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import numpy as np
import pandas as pd
import datetime as dt
from sklearn.preprocessing import StandardScaler
import scipy.spatial.distance as dist
import random

os.environ['SPOTIPY_CLIENT_ID'] = '3191e7e8b04e46c1af64f49bcdd020be'
os.environ['SPOTIPY_CLIENT_SECRET'] = '88dc925eff0d4006bb6d0b9b2401ac59'

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

def print_tracks(uris):
    #recurse through all uris
    if len(uris) > 50:
        num_sets = int(len(uris)/50)
        for i in range(num_sets):
            print_tracks(uris[50*i:50*(i+1)])
        if len(uris)%50 != 0:
            print_tracks(uris[50*num_sets:])
        return

    # collect chosen tracks
    chosen_tracks = sp.tracks(uris)
    chosen_tracks_dict = pd.DataFrame(chosen_tracks['tracks'])
    chosen_tracks_names = chosen_tracks_dict['name']
    chosen_artists_dict = chosen_tracks_dict['artists']
    chosen_artists = []
    for song in chosen_artists_dict:
        a = []
        for artist in song:
            a.append(artist['name'])
        chosen_artists.append(a)

    # print chosen tracks
    for i in range(len(chosen_tracks_names)):
        chosen_artists_string = ''
        for j in range(len(chosen_artists[i])):
            chosen_artists_string += chosen_artists[i][j]
            if j < len(chosen_artists[i])-1:
                chosen_artists_string += ', '
        print(chosen_tracks_names[i] + ' by ' + chosen_artists_string)

# Scale features to range of [-1,1]
def scale_features(features, cols):
    scaler = StandardScaler()
    scaler.fit(features)
    scaled_features = pd.DataFrame(scaler.transform(features))
    scaled_features.columns = cols
    return scaled_features, scaler

# Get recommendations from Spotify API
def get_recommendations(uris):
    recommendations_uris = pd.DataFrame(sp.recommendations(seed_tracks=uris, limit=NUM_RECOMMENDATIONS)['tracks'])['uri']
    return sp.audio_features(recommendations_uris)

# Get artist, popularity, date
def get_track_values(uris):
    MS_IN_DAY = 86400
    # return values are messed up - gotta pass through the return values!!
    extra_uris = []
    if len(uris) > 50:
        extra_uris = uris[50:]
        uris = uris[:50]

    # collect chosen tracks
    tracks = sp.tracks(uris)
    tracks_dict = pd.DataFrame(tracks['tracks'])

    popularity = list(tracks_dict['popularity'])
    names = list(tracks_dict['name'])

    artists_dict = tracks_dict['artists']
    artists = []
    for song in artists_dict:
        a = []
        for artist in song:
            a.append(artist['name'])
        artists.append(a)

    # get genres
    # flatten artists list, make sure len < 50, get genres - prob separate method

    albums_dict = pd.DataFrame(tracks_dict['album'].to_list())
    unconverted_dates = albums_dict['release_date']
    dates = []
    # datetime conversion
    for date in unconverted_dates:
        while len(date) < 10:
            date += '-01'
        ms_date = dt.datetime.timestamp(dt.datetime.strptime(date,"%Y-%m-%d"))
        dates.append(ms_date / MS_IN_DAY)
    
    track_values = [artists, popularity, dates, names]
    
    if len(extra_uris) > 0:
        recur_values = get_track_values(extra_uris)
        for i in range(len(track_values)):
            track_values[i].extend(recur_values[i])
    return track_values

# Get audio features and recommended tracks URIs
def get_values(uris):
    assert(len(uris) <= 5)

    # Get audio features for user's chosen tracks from Spotify API
    chosen_features = sp.audio_features(uris)

    # Get audio features for user's recommended tracks from Spotify API
    recommendations_features = get_recommendations(uris)
    
    # Create unweighted list of all features
    unweighted_features = pd.DataFrame(chosen_features + recommendations_features)
    unweighted_features = unweighted_features.drop(['key', 'loudness', 'mode', 'type', 'id', 'uri', 'track_href', 'analysis_url', 'duration_ms', 'time_signature'], axis=1)

    # Create weighted list of all features favoring chosen features
    weighted_features = pd.DataFrame(chosen_features * CHOSEN_FEATURES_WEIGHT + recommendations_features)
    weighted_features = weighted_features.drop(['key', 'loudness', 'mode', 'type', 'id', 'uri', 'track_href', 'analysis_url', 'duration_ms', 'time_signature'], axis=1)

    recommendations_uris = pd.DataFrame(recommendations_features)['uri']

    return unweighted_features, weighted_features, recommendations_uris

# Evaluate using cosine distance
def evaluate(uri, user_avg, eval_artists, scale_mean, scale_var):
    # get audio features
    features = pd.DataFrame(sp.audio_features(uri))
    features = features.drop(['key', 'loudness', 'mode', 'type', 'id', 'uri', 'track_href', 'analysis_url', 'duration_ms', 'time_signature'], axis=1)
    artists, popularity, dates, _ = get_track_values([uri])
    features['popularity'] = popularity
    features['date'] = dates
    artists = artists[0]

    # scale the features array
    features = (features - scale_mean) / np.sqrt(scale_var)

    penalty = 1
    artist_included = any(a in eval_artists for a in artists)
    if not artist_included:
        penalty += ARTIST_PENALTY
        # print('Penalized')
    
    return dist.cosine(features, user_avg) * ARTIST_PENALTY

# get all features
def get_features(uris):
    n = len(uris)
    uf, wf, rec_uris = get_values(uris)
    artists, popularity, dates, names = get_track_values(uris + list(rec_uris))
    # rec_uris_list = rec_uris_list.append(rec_uris)

    # add to uf
    uf['popularity'] = popularity
    uf['date'] = dates

    # add to wf in a weighted way
    wf['popularity'] = (popularity[:n] * CHOSEN_FEATURES_WEIGHT) + popularity[n:]
    wf['date'] = (dates[:n] * CHOSEN_FEATURES_WEIGHT) + dates[n:]
    
    return uf, wf, rec_uris, artists, names

# set up utility function for each user
# take the average over all user's features then calculate distance to that
# get all features, scale, take average
def get_utilfuncs_and_allsongs(users_uris):
    all_unweighted_features = pd.DataFrame()
    all_weighted_features = pd.DataFrame()

    n = len(users_uris)

    all_uris_list = []
    artists_list = []
    names_list = []

    for i in range(n):
        uf, wf, rec_uris, artists, names = get_features(users_uris[i])

        all_unweighted_features = pd.concat([all_unweighted_features, uf])
        all_weighted_features = pd.concat([all_weighted_features, wf])
        all_uris_list.extend(users_uris[i])
        all_uris_list.extend(rec_uris)
        artists_list.append(artists)
        names_list.append(names[:len(users_uris[i])])

    all_unweighted_features, _ = scale_features(all_unweighted_features, all_unweighted_features.columns) 

    u_start_index = 0
    w_start_index = 0

    u_user_avgs = []
    w_user_avgs = []

    for i in range(n):
        # get user's features
        u_end_index = u_start_index + NUM_RECOMMENDATIONS + len(users_uris[i])
        w_end_index = w_start_index + NUM_RECOMMENDATIONS + (len(users_uris[i] * CHOSEN_FEATURES_WEIGHT))

        uf = all_unweighted_features.iloc[u_start_index:u_end_index]
        wf = all_weighted_features.iloc[w_start_index:w_end_index]
        
        u_start_index = u_end_index
        w_start_index = w_end_index

        # take the average of uf and wf, add to array of average vectors
        u_user_avgs.append(np.mean(uf, axis=0))
        w_user_avgs.append(np.mean(wf, axis=0))
    
    return u_user_avgs, w_user_avgs, all_unweighted_features, np.array(all_uris_list)

# Calculate the distance from every average to every song
def calculate_distances(avgs, songs):
    dists = pd.DataFrame()
    for i in range(len(avgs)):
        user_dists = []
        for j, song in songs.iterrows():
            d = dist.cosine(avgs[i], song)
            user_dists.append(d)
        dists[i] = user_dists
    return dists

# Sigmoid function with beta parameter weighting
def sigmoid(x, beta):
    x = max(x*beta, -709) # where does this come from?
    s = 1 / (1 + np.exp(-x))
    return s

# Sort selected tracks by energy
def sort_by_energy(features, uris, energy_curve):
    sorted_features = features.sort_values(by='energy')
    sorted_features['uri'] = uris

    songs_per_iter = int(len(uris) / len(energy_curve))
    remainder = len(uris) % len(energy_curve)

    argsort_energy = np.argsort(energy_curve)
    print(energy_curve)
    print(argsort_energy)

    chosen_ordered_features = pd.DataFrame()
    argsort_dict = {}

    len_energy = len(energy_curve)

    for i in range(len_energy):
        start = i * songs_per_iter
        end = start + songs_per_iter
        if i == len_energy-1:
            end += remainder
        argsort_dict[argsort_energy[i]] = sorted_features.iloc[start:end]

    for i in range(len_energy):
        if i < len_energy-1 and energy_curve[i] <= energy_curve[i+1]:
            chosen_ordered_features = pd.concat([chosen_ordered_features, argsort_dict[i]])
        elif i < len_energy-1:
            chosen_ordered_features = pd.concat([chosen_ordered_features, argsort_dict[i][::-1]])
        elif energy_curve[i] > energy_curve[i-1]:
            chosen_ordered_features = pd.concat([chosen_ordered_features, argsort_dict[i]])
        else:
            chosen_ordered_features = pd.concat([chosen_ordered_features, argsort_dict[i][::-1]])
    
    return chosen_ordered_features

# SORT! min dist indices
# currently using weighted as default
def select_songs_sort(users_uris, energy_curve, weighted=True):
    u_user_avgs, w_user_avgs, all_features, all_uris_list = get_utilfuncs_and_allsongs(users_uris)
    all_features = all_features.drop_duplicates()
    all_uris_list = np.array(list(dict.fromkeys(all_uris_list)))

    if weighted:
        avgs = w_user_avgs
    else:
        avgs = u_user_avgs

    all_dists = calculate_distances(avgs, all_features)
    indices_sorted_by_min_dist = np.argsort(all_dists, axis=0)
    # use these sorted indices to choose songs (both add and remove)
    # use all_dists to sum distances so i don't have to recalculate them

    n = len(all_features)
    # needs to adjust dynamically to length
    # NUM_SONGS_TO_SELECT = 10

    # start with random set of songs - selected array is indices of selected songs
    selected_ind = random.sample(range(n), NUM_SONGS_TO_SELECT)

    # loop until done
    done = False
    t = 0
    selected_changed = True
    new_song_ind = 0
    maximin_user_dict = {}
    for i in range(len(users_uris)):
        maximin_user_dict[i] = 0
    maximin_dist_list = []

    while not done:
        # print('t =', t)
        # calculate sum of user utilities for every song in the set
        if selected_changed:
            # for every user, their current dist is the sum of all_dists[user][selected_ind]
            current_selected_song_dists = all_dists.iloc[selected_ind]
            current_user_dist_sums = np.sum(current_selected_song_dists, axis=0)
            current_maximin = max(current_user_dist_sums)
            # print('current maximin =', current_maximin)
            current_maximin_user = np.argmax(current_user_dist_sums)
            selected_changed = False
            maximin_user_dict[current_maximin_user] += 1
        
        # print('current max dist user:', current_maximin_user)
        maximin_dist_list.append(current_maximin)
        
        if new_song_ind == n:
            print('sort solved')
            break
        while indices_sorted_by_min_dist[current_maximin_user].iloc[new_song_ind] in selected_ind and new_song_ind < n-1:
            new_song_ind += 1
        new_selected_song = indices_sorted_by_min_dist[current_maximin_user].iloc[new_song_ind]

        # pick removed song: loop through all selected songs, try removing all until one improves the set
        for i in range(NUM_SONGS_TO_SELECT):
            removed_selected = i

            # update new selected indices
            new_selected_ind = selected_ind.copy()
            new_selected_ind[removed_selected] = new_selected_song

            # recalculate sum of user utilities
            new_selected_song_dists = all_dists.iloc[new_selected_ind]
            new_user_dist_sums = np.sum(new_selected_song_dists, axis=0)
            new_maximin = max(new_user_dist_sums)
            new_maximin_user = np.argmax(new_user_dist_sums)

            # determine whether to edit selected_ind list
            if new_maximin < current_maximin:
                selected_ind[removed_selected] = new_selected_song
                selected_changed = True
                new_song_ind = 0
                break
            elif random.random() < sigmoid(current_maximin-new_maximin, t):
                selected_ind[removed_selected] = new_selected_song
                selected_changed = True
                new_song_ind = 0
                break

        if not selected_changed:
            new_song_ind += 1


        # check if done
        # if np.sum(iter_dist_sums) < 0:
        if t > 10000:
            done = True
        t += 1

    ordered_tracks = sort_by_energy(all_features.iloc[selected_ind], all_uris_list[selected_ind], energy_curve)
    # scale these columns back to [0, 1]
    columns_to_scale = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence']
    for col in columns_to_scale:
        ordered_tracks[col] += abs(min(ordered_tracks[col]))
        ordered_tracks[col] /= max(ordered_tracks[col])

    return ordered_tracks

NUM_RECOMMENDATIONS = 100
ARTIST_PENALTY = 0.05
CHOSEN_FEATURES_WEIGHT = 100
NUM_SONGS_TO_SELECT = 30

def get_playlist(users):
    energy_curve = [0.3, 0.6, 0.8, 0.5]

    # parameters
    NUM_RECOMMENDATIONS = 100
    ARTIST_PENALTY = 0.05
    CHOSEN_FEATURES_WEIGHT = 100
    NUM_SONGS_TO_SELECT = 30

    tracks = select_songs_sort(users, energy_curve, weighted=True)
    print(tracks['energy'])
    print_tracks(tracks['uri'])
    return tracks
    # return jsonify({'tracks': tracks})