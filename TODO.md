To do:
- environment variables
- sort needs to end quicker
- num_songs_to_select needs to adjust dynamically based on length
- how heavily am i weighting selected songs? is entropy two parameters?

- set up parameters in backend.py


must play & do not play:
1. after avgs are calculated, find their rows by uri and remove them from consideration for being added to the playlist
    - save the must play rows to be added back after songs are selected, before sort
2. after selection, add must plays to the list before sort


keep the uris in the all_unweighted_features array if i can

Error handling:
- ordered_tracks[col] /= max(ordered_tracks[col]) # divide by zero error??