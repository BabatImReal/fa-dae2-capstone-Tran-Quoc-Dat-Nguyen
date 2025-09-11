## Selected Source: OpenAQ API
- **URL**: https://api.openaq.org/v2/
- **Authentication**: Not required (API key optional for higher rate limits)
- **Rate Limits**: 60 requests/minute, 2,000 requests/hour (as per docs, subject to change)
- **Data Format**: JSON
- **Why I chose this**: Provides free, open, real-time and historical air quality data from thousands of locations worldwide. No API key required for basic usage, but can use API key for higher limits. Well-documented, and suitable for environmental analytics and public health research.

## Backup Options
1. [World Air Quality Index (WAQI) API](https://aqicn.org/api/)
2. [Spotify API](https://developer.spotify.com/documentation/web-api/)
3. [Faker-generated synthetic air quality data]

## Testing Results
- [ ] API accessible
- [ ] Data quality good
- [ ] Rate limits acceptable
- [ ] Documentation clear

---

**Sample Output:**
```
Status code: 200
Response: {'meta': {'name': 'openaq-api', 'website': '/', 'page': 1, 'limit': 100, 'found': 1}, 'results': [{'id': 2, 'name': 'Government Monitor', 'isMonitor': True, 'manufacturer': {'id': 4, 'name': 'Unknown Governmental Organization'}}]}
Rate limit used: 1
Rate limit reset: 60
Rate limit limit: 60
Rate limit remaining: 59
```

**Summary:**  
The OpenAQ API is accessible, returns valid data, and provides clear rate limit headers. Documentation is clear and the API is suitable for integration.
