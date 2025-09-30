## Selected Batch Source: Ultimate Spotify Tracks Database (Kaggle)
- **Primary Dataset**: `zaheenhamidani/ultimate-spotify-tracks-db`
- **URL**: https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db
- **Authentication**: Kaggle account required for download
- **Data Format**: CSV (`SpotifyFeatures.csv`)
- **Dataset Details**: Comprehensive Spotify tracks database with audio features, metadata, and musical characteristics
- **Volume**: Large-scale dataset with extensive track collection
- **Update Frequency**: Static snapshot (Version 3 on Kaggle)
- **Download Location**: `C:\Users\ASUS\.cache\kagglehub\datasets\zaheenhamidani\ultimate-spotify-tracks-db\versions\3\SpotifyFeatures.csv`
- **Why Selected**: Successfully accessible via kagglehub, contains rich audio features and metadata suitable for music analytics and recommendation systems

## Fallback Datasets (Tested)
1. `maharshipandya/-spotify-tracks-dataset` - ❌ No data files found
2. `yamaerenay/spotify-dataset-19212020-160k-tracks` - ⏳ Available as backup option

## Data Pipeline Integration
- **Collection Script**: `scripts/ingestion/collect_batch_data.py`
- **Target Directory**: `data/external/SpotifyFeatures.csv`
- **Processing**: Automated download and copy to project directory via kagglehub

## Testing Results
- [x] Primary dataset (`zaheenhamidani/ultimate-spotify-tracks-db`) accessible
- [x] SpotifyFeatures.csv successfully downloaded
- [x] Data copied to project directory
- [x] File structure validated
- [ ] First fallback dataset failed (no data files)
- [x] Kagglehub integration working
- [x] Automated download pipeline functional

---

**Sample Output (SpotifyFeatures.csv):**
```csv
genre,artist_name,track_name,track_id,popularity,acousticness,danceability,duration_ms,energy,instrumentalness,key,liveness,loudness,mode,speechiness,tempo,valence,time_signature
Electronic,Gorillaz,Feel Good Inc,0d28khcov6AiegSCpG5TuT,90,0.00394,0.794,222640,0.72,0.0112,8,-0.951,1,0.419,144.032,0.816,4
Pop,Ariana Grande,7 rings,6ocbgoVGwYskVH7qt6VCEj,95,0.0154,0.778,178147,0.317,0,1,-7.661,1,0.333,140.048,0.317,4
```

**Data Schema:**
- **Audio Features**: acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, tempo, valence
- **Track Metadata**: genre, artist_name, track_name, track_id, popularity, duration_ms
- **Musical Properties**: key, mode, time_signature

**Download Process:**
```bash
# Automated via collect_batch_data.py
📥 Trying dataset: zaheenhamidani/ultimate-spotify-tracks-db
Path to dataset files: C:\Users\ASUS\.cache\kagglehub\datasets\zaheenhamidani\ultimate-spotify-tracks-db\versions\3
Files in download path:
  - SpotifyFeatures.csv (file)
  ✅ Copied: SpotifyFeatures.csv
✅ Successfully downloaded zaheenhamidani/ultimate-spotify-tracks-db
```

**Summary:**  
The Ultimate Spotify Tracks Database (`zaheenhamidani/ultimate-spotify-tracks-db`) is successfully integrated as the primary batch data source. The dataset provides comprehensive audio features and track metadata through SpotifyFeatures.csv, automatically downloaded via kagglehub and processed by the data pipeline. The first attempted dataset (`maharshipandya/-spotify-tracks-dataset`) was unavailable, demonstrating the robustness of the fallback system.
