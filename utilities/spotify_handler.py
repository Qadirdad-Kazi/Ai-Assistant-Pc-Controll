import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

class SpotifyHandler:
    def __init__(self, client_id=None, client_secret=None, redirect_uri="http://localhost:8888/callback"):
        self.client_id = client_id or os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIPY_CLIENT_SECRET")
        self.redirect_uri = redirect_uri
        self.sp = None

    def authenticate(self):
        """Authenticate with Spotify."""
        if not self.client_id or not self.client_secret:
            return False, "Missing Client ID or Secret. Mission parameters incomplete."
        
        try:
            scope = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing"
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                open_browser=True
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            # Test connection
            self.sp.current_user()
            return True, "Holographic Link Established with Spotify."
        except Exception as e:
            return False, f"Spectral Link Failed: {e}"

    def get_current_track(self):
        """Get currently playing track info."""
        if not self.sp:
            return None
        try:
            track = self.sp.current_user_playing_track()
            if track and track['is_playing']:
                item = track['item']
                return {
                    'title': item['name'],
                    'artist': item['artists'][0]['name'],
                    'id': item['id'],
                    'is_playing': True,
                    'progress_ms': track['progress_ms'],
                    'duration_ms': item['duration_ms']
                }
            return None
        except:
            return None

    def search_and_play(self, query):
        """Search and start playback."""
        if not self.sp:
            return False
        try:
            results = self.sp.search(q=query, limit=1, type='track')
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                self.sp.start_playback(uris=[track_uri])
                return True
            return False
        except:
            return False
