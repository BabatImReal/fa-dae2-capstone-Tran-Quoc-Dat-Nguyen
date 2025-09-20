## Selected Source: Last.fm API
- **URL**: https://www.last.fm/api
- **Authentication**: Not required for most methods (API key only, no OAuth)
- **Rate Limits**: 5 requests/sec (as per docs, subject to change)
- **Data Format**: JSON or XML
- **Why I chose this**: Provides free access to music metadata (artists, albums, tracks), user listening data, charts, and tags. No user authentication required for most endpoints. Well-documented and widely used for music analytics and recommendation systems.

**Can it generate new/different data every 5 minutes?**
- Last.fm API provides endpoints for real-time charts, recent tracks, and user listening data. These endpoints reflect new data as users interact with the platform, so querying every 5 minutes will return updated results (e.g., top tracks, trending artists, recent listens).

## Backup/Secondary Source: Spotify API
- **URL**: https://api.spotify.com/v1/
- **Authentication**: Required (OAuth 2.0)
- **Rate Limits**: 20 requests/second (as per docs, subject to change)
- **Data Format**: JSON
- **Why I chose this**: Extensive music metadata, playlists, and popularity metrics. Useful for cross-referencing and enriching Last.fm data.

**Can it generate new/different data every 5 minutes?**
- Spotify API endpoints (e.g., charts, playlists, new releases, user activity) are updated frequently. Querying every 5 minutes will return new or changed data, especially for trending tracks, playlists, and artist metrics.

## Backup Options
[Faker-generated synthetic music metadata]

## Testing Results
- [ ] Last.fm API accessible
- [ ] Data quality good
- [ ] Rate limits acceptable
- [ ] Documentation clear

---

**Sample Output (Last.fm API):**
```
{
  "artist": {
    "name": "The Weeknd",
    "mbid": "c8b03190-306c-4124-bb9c-2b6c4b6d7c50",
    "url": "https://www.last.fm/music/The+Weeknd",
    "image": [
      {
        "#text": "https://lastfm.freetls.fastly.net/i/u/300x300/ab6761610000e5eb9e528993a2820267b97f6aae.png",
        "size": "large"
      }
    ],
    "stats": {
      "listeners": "1234567",
      "playcount": "98765432"
    },
    "tags": {
      "tag": [
        { "name": "pop", "url": "https://www.last.fm/tag/pop" }
      ]
    },
    "bio": {
      "summary": "The Weeknd is a Canadian singer, songwriter, and record producer...",
      "content": "Full biography text..."
    }
  }
}
```

**Sample Output (Spotify API):**
```
[
  {
    "external_urls": {
      "spotify": "https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ"
    },
    "followers": {
      "href": null,
      "total": 110706263
    },
    "genres": [],
    "href": "https://api.spotify.com/v1/artists/1Xyo4u8uXC1ZmMpatF05PJ",
    "id": "1Xyo4u8uXC1ZmMpatF05PJ",
    "images": [
      {
        "url": "https://i.scdn.co/image/ab6761610000e5eb9e528993a2820267b97f6aae",
        "height": 640,
        "width": 640
      },
      {
        "url": "https://i.scdn.co/image/ab676161000051749e528993a2820267b97f6aae",
        "height": 320,
        "width": 320
      },
      {
        "url": "https://i.scdn.co/image/ab6761610000f1789e528993a2820267b97f6aae",
        "height": 160,
        "width": 160
      }
    ],
    "name": "The Weeknd",
    "popularity": 97,
    "type": "artist",
    "uri": "spotify:artist:1Xyo4u8uXC1ZmMpatF05PJ"
  },
  {
    "external_urls": {
      "spotify": "https://open.spotify.com/artist/3TVXtAsR1Inumwj472S9r4"
    },
    "followers": {
      "href": null,
      "total": 101580796
    },
    "genres": [
      "rap"
    ],
    "href": "https://api.spotify.com/v1/artists/3TVXtAsR1Inumwj472S9r4",
    "id": "3TVXtAsR1Inumwj472S9r4",
    "images": [
      {
        "url": "https://i.scdn.co/image/ab6761610000e5eb4293385d324db8558179afd9",
        "height": 640,
        "width": 640
      },
      {
        "url": "https://i.scdn.co/image/ab676161000051744293385d324db8558179afd9",
        "height": 320,
        "width": 320
      },
      {
        "url": "https://i.scdn.co/image/ab6761610000f1784293385d324db8558179afd9",
        "height": 160,
        "width": 160
      }
    ],
    "name": "Drake",
    "popularity": 99,
    "type": "artist",
    "uri": "spotify:artist:3TVXtAsR1Inumwj472S9r4"
  }
]
```

**Summary:**  
The Last.fm API is accessible, returns valid music and user data, and provides clear documentation. No user authentication is required for most endpoints, making it suitable as the main data source. Spotify API will be used as a secondary source for additional metadata and cross-referencing. Both APIs can provide new or updated data every 5 minutes, making them suitable for applications needing real-time or near-real-time data.
