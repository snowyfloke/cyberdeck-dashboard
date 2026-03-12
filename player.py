def get_current_state(sp):
    return sp.current_playback()

def sp_play(sp):
    sp.start_playback()

def sp_pause(sp):
    sp.pause_playback()

def next_song(sp):
    sp.next_track()

def previous_song(sp):
    sp.previous_track()

def set_volume(sp, volume: int):
    if not 0 <= volume <= 100:
        raise ValueError("Volume must be between 0 and 100")
    sp.volume(volume)
