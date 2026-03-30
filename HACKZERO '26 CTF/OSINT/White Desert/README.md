# White Desert

| Field      | Value                       |
| ---------- | --------------------------- |
| Category   | OSINT                       |
| Points     | 200                         |
| Solves     | 91                          |
| Connection | https://vantage.vitbctf.dev |

## Description

Select an active coordinate to commence geospatial analysis. Identify the location to secure the flag.

## Writeup

The people in the photo seem Indian.
"White Desert" leads me to Rajasthan
White Desert probably implies the famous marble deposit (simple google search: "white desert rajasthan"), and after a bit of looking on google maps and trying coordinates, got exact location.

### Flag

```
hackzero{wh173_dump1ng_y4rd_0f_k15h4ng4rh}
```

### Executive Summary

Used visual cues and targeted geosearch to identify the location as the White Desert area near Kishangarh, Rajasthan. The flag corresponds to that location.

### Vulnerability Analysis

- No usable EXIF metadata in the image; required open-source geolocation techniques.

### Exploit Strategy

1. Identify cultural/visual cues (people, landscape).
2. Search for "White Desert Rajasthan" and related landmarks.
3. Probe coordinates in Google Maps / satellite view until features match the photo.

### Implementation

- Tools: Google Search, Google Maps (satellite), manual coordinate probing.
- Performed targeted searches, then iteratively adjusted coordinates to match terrain and landmarks.

### Execution & Results

- Exact match found via Google Maps imagery; verified by local landmarks and terrain.
- Retrieved flag from identified location: `hackzero{wh173_dump1ng_y4rd_0f_k15h4ng4rh}`.
