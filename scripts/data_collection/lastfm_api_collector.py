# scripts/data_collection/lastfm_api_collector.py
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LastFMAPICollector:
    """Last.fm API data collector for music data."""
    
    def __init__(self):
        self.api_key = os.getenv("LASTFM_API_KEY")
        if not self.api_key:
            raise ValueError("LASTFM_API_KEY environment variable is not set. Please add your Last.fm API key to .env file.")
        
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))
        self.delay_between_requests = float(os.getenv("REQUEST_DELAY", 0.2))  # Rate limiting
        self.data_dir = Path("data/external")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, **params) -> Dict:
        """Make a request to Last.fm API with retry logic."""
        params.update({
            "api_key": self.api_key,
            "method": method,
            "format": "json"
        })
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for Last.fm API errors
                if "error" in data:
                    raise Exception(f"Last.fm API error: {data['message']}")
                
                # Rate limiting
                time.sleep(self.delay_between_requests)
                return data
                
            except Exception as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return {}

    def get_top_tracks(self, limit: int = 50) -> List[Dict]:
        """Get top tracks from Last.fm."""
        self.logger.info(f"Fetching top {limit} tracks from Last.fm")
        
        data = self._make_request(
            method="chart.gettoptracks",
            limit=limit
        )
        
        return data.get("tracks", {}).get("track", [])

    def get_top_artists(self, limit: int = 50) -> List[Dict]:
        """Get top artists from Last.fm."""
        self.logger.info(f"Fetching top {limit} artists from Last.fm")
        
        data = self._make_request(
            method="chart.gettopartists",
            limit=limit
        )
        
        return data.get("artists", {}).get("artist", [])

    def get_artist_info(self, artist_name: str) -> Dict:
        """Get detailed information about an artist."""
        self.logger.info(f"Fetching artist info for: {artist_name}")
        
        data = self._make_request(
            method="artist.getinfo",
            artist=artist_name
        )
        
        return data.get("artist", {})

    def get_artist_top_tracks(self, artist_name: str, limit: int = 10) -> List[Dict]:
        """Get top tracks for a specific artist."""
        self.logger.info(f"Fetching top {limit} tracks for artist: {artist_name}")
        
        data = self._make_request(
            method="artist.gettoptracks",
            artist=artist_name,
            limit=limit
        )
        
        return data.get("toptracks", {}).get("track", [])

    def get_track_info(self, artist_name: str, track_name: str) -> Dict:
        """Get detailed information about a specific track."""
        self.logger.info(f"Fetching track info for: {track_name} by {artist_name}")
        
        data = self._make_request(
            method="track.getinfo",
            artist=artist_name,
            track=track_name
        )
        
        return data.get("track", {})

    def search_tracks(self, query: str, limit: int = 30) -> List[Dict]:
        """Search for tracks matching a query."""
        self.logger.info(f"Searching tracks for query: {query}")
        
        data = self._make_request(
            method="track.search",
            track=query,
            limit=limit
        )
        
        return data.get("results", {}).get("trackmatches", {}).get("track", [])

    def search_artists(self, query: str, limit: int = 30) -> List[Dict]:
        """Search for artists matching a query."""
        self.logger.info(f"Searching artists for query: {query}")
        
        data = self._make_request(
            method="artist.search",
            artist=query,
            limit=limit
        )
        
        return data.get("results", {}).get("artistmatches", {}).get("artist", [])

    def get_tag_top_tracks(self, tag: str, limit: int = 50) -> List[Dict]:
        """Get top tracks for a specific genre/tag."""
        self.logger.info(f"Fetching top {limit} tracks for tag: {tag}")
        
        data = self._make_request(
            method="tag.gettoptracks",
            tag=tag,
            limit=limit
        )
        
        return data.get("tracks", {}).get("track", [])

    def get_user_recent_tracks(self, username: str, limit: int = 50, from_timestamp: Optional[int] = None, to_timestamp: Optional[int] = None) -> List[Dict]:
        """Get a user's recent tracks (scrobbles).
        
        Args:
            username: Last.fm username
            limit: Number of tracks to return (max 200)
            from_timestamp: Unix timestamp to start from (optional)
            to_timestamp: Unix timestamp to end at (optional)
        
        Returns:
            List of recent tracks with metadata
        """
        self.logger.info(f"Fetching recent {limit} tracks for user: {username}")
        
        params = {
            "method": "user.getrecenttracks",
            "user": username,
            "limit": min(limit, 200)  # Last.fm API limit
        }
        
        # Add optional timestamp filters
        if from_timestamp:
            params["from"] = from_timestamp
        if to_timestamp:
            params["to"] = to_timestamp
        
        data = self._make_request(**params)
        
        return data.get("recenttracks", {}).get("track", [])

    def get_user_top_tracks(self, username: str, period: str = "overall", limit: int = 50) -> List[Dict]:
        """Get a user's top tracks for a specific time period.
        
        Args:
            username: Last.fm username
            period: Time period - overall, 7day, 1month, 3month, 6month, 12month
            limit: Number of tracks to return
        
        Returns:
            List of user's top tracks
        """
        self.logger.info(f"Fetching top {limit} tracks for user {username} (period: {period})")
        
        valid_periods = ["overall", "7day", "1month", "3month", "6month", "12month"]
        if period not in valid_periods:
            raise ValueError(f"Invalid period. Must be one of: {valid_periods}")
        
        data = self._make_request(
            method="user.gettoptracks",
            user=username,
            period=period,
            limit=limit
        )
        
        return data.get("toptracks", {}).get("track", [])

    def get_user_top_artists(self, username: str, period: str = "overall", limit: int = 50) -> List[Dict]:
        """Get a user's top artists for a specific time period.
        
        Args:
            username: Last.fm username
            period: Time period - overall, 7day, 1month, 3month, 6month, 12month
            limit: Number of artists to return
        
        Returns:
            List of user's top artists
        """
        self.logger.info(f"Fetching top {limit} artists for user {username} (period: {period})")
        
        valid_periods = ["overall", "7day", "1month", "3month", "6month", "12month"]
        if period not in valid_periods:
            raise ValueError(f"Invalid period. Must be one of: {valid_periods}")
        
        data = self._make_request(
            method="user.gettopartists",
            user=username,
            period=period,
            limit=limit
        )
        
        return data.get("topartists", {}).get("artist", [])

    def save_data(self, data: List[Dict] | Dict, filename: str) -> Path:
        """Save data to timestamped JSON file in data/external directory."""
        timestamp = int(time.time())
        file_path = self.data_dir / f"lastfm_{filename}_{timestamp}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Data saved to: {file_path}")
        return file_path

    def collect_comprehensive_data(self, sample_username: str = None) -> Dict[str, Path]:
        """Collect comprehensive music data from Last.fm and save to separate files.
        
        Args:
            sample_username: Optional Last.fm username to collect user-specific data
        """
        saved_files = {}
        
        try:
            # Collect top tracks
            top_tracks = self.get_top_tracks(limit=100)
            if top_tracks:
                saved_files['top_tracks'] = self.save_data(top_tracks, "top_tracks")
            
            # Collect top artists
            top_artists = self.get_top_artists(limit=100)
            if top_artists:
                saved_files['top_artists'] = self.save_data(top_artists, "top_artists")
            
            # Collect data for popular genres
            popular_genres = ['rock', 'pop', 'electronic', 'hip-hop', 'jazz', 'classical']
            for genre in popular_genres:
                try:
                    genre_tracks = self.get_tag_top_tracks(genre, limit=50)
                    if genre_tracks:
                        saved_files[f'{genre}_tracks'] = self.save_data(genre_tracks, f"genre_{genre}_tracks")
                except Exception as e:
                    self.logger.warning(f"Failed to collect data for genre {genre}: {e}")
            
            # Get detailed info for top 10 artists
            artist_details = []
            for artist in top_artists[:10]:
                try:
                    artist_name = artist.get('name', '')
                    if artist_name:
                        artist_info = self.get_artist_info(artist_name)
                        if artist_info:
                            artist_details.append(artist_info)
                except Exception as e:
                    self.logger.warning(f"Failed to get info for artist {artist.get('name', 'Unknown')}: {e}")
            
            if artist_details:
                saved_files['artist_details'] = self.save_data(artist_details, "artist_details")
            
            # Collect user-specific data if username provided
            if sample_username:
                try:
                    # Get user's recent tracks
                    recent_tracks = self.get_user_recent_tracks(sample_username, limit=100)
                    if recent_tracks:
                        saved_files['user_recent_tracks'] = self.save_data(recent_tracks, f"user_{sample_username}_recent_tracks")
                    
                    # Get user's top tracks
                    user_top_tracks = self.get_user_top_tracks(sample_username, period="1month", limit=50)
                    if user_top_tracks:
                        saved_files['user_top_tracks'] = self.save_data(user_top_tracks, f"user_{sample_username}_top_tracks")
                    
                    # Get user's top artists
                    user_top_artists = self.get_user_top_artists(sample_username, period="1month", limit=50)
                    if user_top_artists:
                        saved_files['user_top_artists'] = self.save_data(user_top_artists, f"user_{sample_username}_top_artists")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to collect user data for {sample_username}: {e}")
            
            return saved_files
            
        except Exception as e:
            self.logger.error(f"Data collection failed: {e}")
            raise

def main():
    """Main function to demonstrate Last.fm API data collection."""
    try:
        collector = LastFMAPICollector()
        
        print("Starting Last.fm data collection...")
        
        # Example of collecting user recent tracks
        print("\n=== Demo: User Recent Tracks ===")
        sample_username = "rj"  # Famous Last.fm user for testing
        
        try:
            recent_tracks = collector.get_user_recent_tracks(sample_username, limit=10)
            if recent_tracks:
                print(f"\nRecent tracks for user '{sample_username}':")
                for i, track in enumerate(recent_tracks[:5], 1):
                    artist = track.get('artist', {}).get('#text', 'Unknown Artist')
                    song = track.get('name', 'Unknown Track')
                    album = track.get('album', {}).get('#text', 'Unknown Album')
                    date = track.get('date', {}).get('#text', 'Unknown Date')
                    print(f"  {i}. {artist} - {song} (Album: {album}) [Played: {date}]")
                
                # Save user recent tracks
                saved_file = collector.save_data(recent_tracks, f"demo_user_{sample_username}_recent_tracks")
                print(f"\nUser recent tracks saved to: {saved_file}")
            else:
                print(f"No recent tracks found for user '{sample_username}'")
                
        except Exception as e:
            print(f"Failed to get recent tracks for user '{sample_username}': {e}")
        
        # Collect comprehensive data
        print("\n=== Comprehensive Data Collection ===")
        saved_files = collector.collect_comprehensive_data(sample_username=sample_username)
        
        print("\nData collection completed successfully!")
        print("Files saved:")
        for data_type, file_path in saved_files.items():
            print(f"  - {data_type}: {file_path}")
            
    except Exception as e:
        print(f"Data collection failed: {e}")
        print("\nPlease ensure:")
        print("1. Your LASTFM_API_KEY is set in the .env file")
        print("2. You have internet connectivity")
        print("3. Your Last.fm API key is valid")
        print("4. The username exists on Last.fm (for user-specific data)")
        raise

if __name__ == "__main__":
    main()