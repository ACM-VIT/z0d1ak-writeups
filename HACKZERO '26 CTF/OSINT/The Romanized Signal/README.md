# The Romanized Signal
 

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 150 |
| Solves     | 60 |

## Description

Description: In the world of intelligence, legal paperwork is often a shroud for the truth. You have been provided with a link to a 110-page legal bundle from the Prime Minister’s Office regarding a high-profile disappearance. While the first hundred pages are filled with modern affidavits and legal jargon, your mission is to locate the original intelligence folios buried at the end of the file. Find a specific report regarding a "strange broadcast" captured during the winter. To secure the flag, identify the physical city named in that historical log as the source of the transmission and the year it was intercepted. 

Flag Format:
`hackzero{cityname_year}`

**Access the Portal** : https://www.abhilekh-patal.in/Category/Search/QuerySearch?query=NSBDLF_00000051

### Flag

```
hackzero{peking-1949}
```

### Executive Summary

This challenge involved analyzing a large legal archive related to Subhash Chandra Bose and locating a hidden historical intelligence report. The goal was to identify the city and year of a strange radio broadcast mentioned in the records.


### Strategy

1. Navigate to the end of the document to find older records.
2. Search for mentions of broadcasts or intelligence notes.
3. Extract keywords and pivot to external sources.
4. Correlate findings with historical reports on Bose.

### Implementation

* Reviewed the archive and skipped irrelevant sections.
* Used keyword searching within the document.
* Pivoted to online research when direct data was unclear.
* Found references to Bose-related broadcasts in external articles.

https://www.business-standard.com/article/current-affairs/was-netaji-alive-even-after-1945-115091801243_1.html

### Execution and Results

Research confirmed a report of a broadcast from Peking in 1949. This matched the required format and produced the final flag:

hackzero{peking-1949}
