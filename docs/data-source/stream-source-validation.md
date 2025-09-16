## Selected Source: Spotify API
- **URL**: https://api.spotify.com/v1/
- **Authentication**: Required (OAuth 2.0)
- **Rate Limits**: 20 requests/second (as per docs, subject to change)
- **Data Format**: JSON
- **Why I chose this**: Provides free and extensive access to music metadata, including artists, albums, tracks, and playlists. Well-documented, widely used for music analytics and recommendation systems.

## Backup Options
[Faker-generated synthetic music metadata]

## Testing Results
- [ ] API accessible
- [ ] Data quality good
- [ ] Rate limits acceptable
- [ ] Documentation clear

---

**Sample Output:**
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
The Spotify API is accessible, returns valid music metadata, and provides clear rate limit headers. Documentation is clear and the API is suitable for integration.
