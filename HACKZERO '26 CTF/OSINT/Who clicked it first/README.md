# Who clicked it first?

| Field    | Value |
| -------- | ----- |
| Category | OSINT |
| Points   | 250   |
| Solves   | 18    |

## Description

A single dish photo is your only lead. Trace its earliest appearance online, identify who clicked it first and determine the exact date it was taken.

Flag Format:
`hackzero{name_date}`

Date in `dd-mm-yyyy` format

## Files

- [IMG_6402.JPG](./IMG_6402.JPG)

## Writeup

the food in a picture is Schnitzel
I tried to identify the phone model for clues but led nowhere

I tried the following
google lens -> nothing
yandex -> nothing
tin eye -> results the exact image, earliest author was keith kendal on flicker, but date was wrong

links on tin eye were all broken

found keith's flicker
https://www.flickr.com/photos/keithkendall/

searched for "Schnitzel"

exact match
https://www.flickr.com/photos/keithkendall/15880154310/in/photolist-qcgWBY

it listed the date and author

Uploaded on December 21, 2014
Taken on December 20, 2014

### Executive Summary

A reverse-image investigation of `IMG_6402.JPG` identified the dish as a schnitzel and led to an exact match on Flickr. The image was uploaded by Keith Kendall on 21 December 2014 and the photo's taken date is listed as 20 December 2014. The earliest reliably referenced appearance online is Keith Kendall's Flickr upload. The final flag is provided below.

### Vulnerability Analysis

- Lack of embedded EXIF metadata (or EXIF stripped) reduced direct device/date attribution, requiring provenance tracing through public image indexes.
- Broken or dead links from third-party reverse-image results (e.g., older TinEye entries) can obscure earliest sources; therefore primary-host discovery (Flickr) is more reliable.

### Exploit Strategy

1. Use visual identification (recognize the food as schnitzel) to generate targeted search keywords.
2. Run reverse-image searches (TinEye, Google Lens, Yandex) to locate exact matches and candidate hosts.
3. Follow links to primary content hosts and inspect upload/taken dates and author profiles for earliest credible timestamp.
4. Cross-validate dates shown on the host page (Flickr) as the authoritative earliest appearance.

### Implementation

- Tools used: TinEye, Google Lens, Yandex Image Search, direct Flickr browsing.
- Steps performed:
  - Ran reverse-image searches; TinEye returned the exact image but many links were broken.
  - Located the image on Keith Kendall's Flickr profile: https://www.flickr.com/photos/keithkendall/15880154310/in/photolist-qcgWBY
  - Inspected the Flickr entry for both "Uploaded" and "Taken" dates and confirmed author.

### Execution & Results

- Result: Exact image match found on Flickr.
- Flickr entry details:
  - Author: Keith Kendall
  - Uploaded: 21 December 2014
  - Taken: 20 December 2014
- Conclusion: The earliest verifiable appearance of the image is the Flickr upload by Keith Kendall (uploaded 21-12-2014), with the photo taken on 20-12-2014.

### Flag

```
hackzero{keith_kendall_21-12-2014}
```
