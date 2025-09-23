## Selected Streaming Source: Faker-generated Synthetic Music Metadata
- **Source:** Python scripts using the Faker library
- **Authentication:** Not required
- **Rate Limits:** Configurable (no external limits)
- **Data Format:** JSON (custom schema)
- **Rationale:** Enables development and testing of real-time pipeline features without relying on external APIs. Data can be generated on demand and customized for various scenarios.

**Real-time Data Capability:**  
Faker scripts can generate new, randomized music metadata every 5 minutes (or any interval), simulating real-time data ingestion for tracks, artists, albums, and user activity.

---

## Backup Options
- [Planned] Last.fm API
- [Planned] Spotify API

---

## Testing Results
- [x] Faker data generation accessible
- [x] Data quality configurable
- [x] No rate limits
- [x] Documentation: [Faker library](https://faker.readthedocs.io/)

---

**Sample Output (Faker-generated):**
```json
{
  "artist": {
    "name": "Fake Artist",
    "id": "artist_12345",
    "url": "https://music.example.com/artist/artist_12345",
    "image": "https://picsum.photos/300",
    "stats": {
      "listeners": 12345,
      "playcount": 67890
    },
    "tags": [
      { "name": "pop", "url": "https://music.example.com/tag/pop" }
    ],
    "bio": {
      "summary": "Fake Artist is a synthetic musician generated for testing.",
      "content": "Full biography text..."
    }
  },
  "track": {
    "name": "Fake Song",
    "id": "track_67890",
    "album": "Fake Album",
    "duration": 210,
    "popularity": 75
  }
}
```

**Sample Streaming Events (Faker-generated test data):**
```json
{
  "event_id": "929a87cb-28dc-428b-a9ad-2b83d670ac21",
  "user_id": "ae370446-0949-47d8-ae83-951fdfdecf77",
  "session_id": "58d396c6-e2f9-4309-ae12-493c7d4e4ce5",
  "song_id": "1d6e7781-813b-4135-8383-d3cea156fad6",
  "song_title": "Base course here",
  "artist": "Morgan Butler",
  "album": "Card Album",
  "genre": "Blues",
  "duration_seconds": 174,
  "position_seconds": 149,
  "event_action": "shuffle",
  "device_type": "tablet",
  "platform": "apple_music",
  "timestamp": "2025-09-23T10:49:48",
  "user_premium": true,
  "ingested_at": "2025-09-23T03:49:48.554998"
}
{
  "event_id": "4b57adb0-3eb1-4f91-95ba-a368d873fe62",
  "user_id": "57e5996d-a687-4533-940f-01a5e81ab351",
  "session_id": "f1b43a6c-0bb7-49e8-84a6-9505ee02b3df",
  "song_id": "0a98e092-7cf8-4085-95f9-82766e659ed4",
  "song_title": "Decade particular",
  "artist": "James Stevens",
  "album": "Check Album",
  "genre": "Electronic",
  "duration_seconds": 202,
  "position_seconds": 45,
  "event_action": "repeat",
  "device_type": "desktop",
  "platform": "spotify",
  "timestamp": "2025-09-23T10:54:48",
  "user_premium": false,
  "ingested_at": "2025-09-23T03:49:48.554998"
}
{
  "event_id": "e632fbae-bc95-4206-840c-e0b04deb8662",
  "user_id": "b6cd4197-f8a5-43ce-b1b4-291a9f04b328",
  "session_id": "2d4546e3-6233-4897-9c32-f1262835e4ad",
  "song_id": "f4b36d03-0088-4e30-819f-b218609dd5af",
  "song_title": "Business my",
  "artist": "Noah Holland",
  "album": "Voice Album",
  "genre": "Rock",
  "duration_seconds": 174,
  "position_seconds": 0,
  "event_action": "play",
  "device_type": "desktop",
  "platform": "spotify",
  "timestamp": "2025-09-23T10:59:48",
  "user_premium": false,
  "ingested_at": "2025-09-23T03:49:48.554998"
}
{
  "event_id": "ac227cce-a032-491e-aedd-17466885dd9d",
  "user_id": "38b3e1ec-f966-4a09-a67d-049f5f0ddcaa",
  "session_id": "a05e5655-6fb8-4119-b142-3d5c8d5534dc",
  "song_id": "fb3d5360-6c5c-4d59-a03f-bbb95479f517",
  "song_title": "Rule design position",
  "artist": "Jessica Cruz",
  "album": "Sing Album",
  "genre": "Hip-Hop",
  "duration_seconds": 233,
  "position_seconds": 38,
  "event_action": "dislike",
  "device_type": "smart_speaker",
  "platform": "youtube_music",
  "timestamp": "2025-09-23T11:04:48",
  "user_premium": false,
  "ingested_at": "2025-09-23T03:49:48.554998"
}
{
  "event_id": "0eabe120-c286-4a4e-86f3-ce6780bae829",
  "user_id": "b0e749e6-7816-4e10-a1f5-40f8cff55ae7",
  "session_id": "fabb7ceb-1683-4bf7-b000-8313fbd451ac",
  "song_id": "851d8cc5-b134-4edd-93e7-7c53d0dc20e5",
  "song_title": "Board",
  "artist": "Kathleen Solomon",
  "album": "Newspaper Album",
  "genre": "Country",
  "duration_seconds": 395,
  "position_seconds": 279,
  "event_action": "like",
  "device_type": "mobile",
  "platform": "youtube_music",
  "timestamp": "2025-09-23T11:09:48",
  "user_premium": false,
  "ingested_at": "2025-09-23T03:49:48.554998"
}
{
  "event_id": "b3b431c0-7145-48c9-be06-d20dcccc2951",
  "user_id": "6903b948-9b41-48d5-b201-2c85a392a138",
  "session_id": "73d8b831-e18d-4781-bb0d-9113d13d2fe8",
  "song_id": "b5288036-3228-4019-aeb8-0d370ee14557",
  "song_title": "Off no popular",
  "artist": "Matthew West",
  "album": "Purpose Album",
  "genre": "Blues",
  "duration_seconds": 196,
  "position_seconds": 71,
  "event_action": "resume",
  "device_type": "mobile",
  "platform": "youtube_music",
  "timestamp": "2025-09-23T11:14:48",
  "user_premium": false,
  "ingested_at": "2025-09-23T03:49:48.554998"
}
```

---

**Summary:**  
Faker-generated synthetic music metadata is currently used as the main streaming source for development and testing. It provides flexible, on-demand data generation for real-time pipeline validation. External APIs (Last.fm, Spotify) are planned as future options for production or enrichment.
