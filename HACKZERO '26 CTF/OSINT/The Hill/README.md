# The Hill

| Field      | Value                       |
| ---------- | --------------------------- |
| Category   | OSINT                       |
| Points     | 350                         |
| Solves     | 19                          |
| Connection | https://vantage.vitbctf.dev |

## Description

Select an active coordinate to commence geospatial analysis. Identify the location to secure the flag.

## Writeup

Water tank company on india mart based from orissa
Called the company, found out it's apparently a solar tank
looked at a lot of remote outskirt of village type locations in orissa on google maps

Found a water tank supplier listing on IndiaMART tied to Odisha (Orissa). After calling the company and checking Google Maps / Street View for likely rural locations, I used iterative visual matching and an LLM-assisted coordinate suggestion to identify Koraput. The submitted coordinates matched and yielded the flag.

Coordinates: `18.8135, 82.7123`

### Flag

```
hackzero{y0u_4r3_1n_r3m073_0dd1sh4}
```

### Executive Summary

Used vendor listing, phone verification, and satellite/street-view comparison to locate the target in Koraput, Odisha. An LLM-assisted coordinate refinement produced the final submitted coordinates.

### Vulnerability Analysis

- Image lacked reliable EXIF/location metadata; required OSINT and human verification.
- Public business listings (IndiaMART) and street-level imagery exposed contextual clues that enabled geolocation.

### Exploit Strategy

1. Search vendor/business names visible or inferred from the image on IndiaMART and similar directories.
2. Use phone/website info to narrow the state/region (Orissa/Odisha).
3. Scan likely rural areas in the region with Google Maps satellite and Street View.
4. Use targeted image/scene snippets and an LLM to consolidate leads into coordinates for verification.

### Implementation

- Tools: IndiaMART, Google Maps (satellite + Street View), phone contact, ChatGPT for coordinate consolidation.

### Execution & Results

- Candidate coordinates refined to `18.8135, 82.7123` (Koraput town) and accepted by the challenge interface.
- Retrieved flag: `hackzero{y0u_4r3_1n_r3m073_0dd1sh4}`.
