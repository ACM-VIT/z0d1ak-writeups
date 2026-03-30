# The Roadway in the Capital

| Field      | Value                       |
| ---------- | --------------------------- |
| Category   | OSINT                       |
| Points     | 350                         |
| Solves     | 87                          |
| Connection | https://vantage.vitbctf.dev |

## Description

Select an active coordinate to commence geospatial analysis. Identify the location to secure the flag.

## Writeup

Roadway -> Rhode
in the capital -> washington DC (the location looks like USA)

search for shell gas stations
scour all, get the one which matches

Interpreted the clue as "Roadway in the Capital" → Washington, D.C. Focused on Shell gas stations visible in the scene and compared street-level imagery across candidate locations until finding a match.

### Flag

```
hackzero{g07_y0u_0n_7h3_p013}
```

### Executive Summary

Matched the image to a Shell station in Washington, D.C. via visual feature comparison in Street View and map/satellite cues.

### Vulnerability Analysis

### Exploit Strategy

1. Use textual clues to determine likely country/city ("capital" means Washington, D.C.).
2. Search for Shell stations in the area using maps and Street View.

### Implementation

- Tools: Google Maps (Street View), Google Search for brand locations.
- Process: enumerated Shell locations in D.C., inspected Street View images, and matched unique scene elements (signage, road markings, adjacent buildings).

### Execution & Results

- Exact visual match located and verified via Street View.
