import yt_dlp
import json

class YouTubeHandler:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

    def search(self, query, limit=5):
        """Search YouTube and return results."""
        search_query = f"ytsearch{limit}:{query}"
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(search_query, download=False)
                results = []
                for entry in info.get('entries', []):
                    results.append({
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'id': entry.get('id'),
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader')
                    })
                return results
            except Exception as e:
                print(f"YouTube Search Error: {e}")
                return []

    def get_stream_url(self, video_url):
        """Get the direct audio stream URL."""
        opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
                return info.get('url')
            except Exception as e:
                print(f"YouTube Stream Error: {e}")
                return None

if __name__ == "__main__":
    handler = YouTubeHandler()
    results = handler.search("lofi hip hop")
    for r in results:
        print(f"{r['title']} - {r['url']}")
