# Exit at 13,000 Feet

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 150 |
| Solves     | 126 |

## Description

A door hangs open at altitude. A specialized aircraft belonging to a skydiving company is captured mid-flight. Your mission: identify the airline operating this aircraft using only open-source intelligence techniques.

Flag Format:
`hackzero{}`
**Replace any space between the full name with underscore (if necessary)**

## Files

- [Exit_at_13000_Feet.png](./Exit_at_13000_Feet.png)

## Writeup

### Flag

```
hackzero{skydive_arizona}
```

### Executive Summary

This challenge required identifying an aircraft from an image and linking it to a specific organization. The goal was to recognize the plane model and trace its livery to find the correct name for the flag.

### Strategy

1. Identify the aircraft model from the image.
2. Search for matching aircraft images online.
3. Compare liveries and branding.
4. Match the correct organization associated with the aircraft.

### Implementation

* Observed the aircraft design and features in the image.
* Identified the plane as a Cessna Caravan using web search.
* Compared images of different airline and skydiving liveries.
* Found a match with Skydive Arizona branding.

### Execution and Results

The aircraft matched the Skydive Arizona livery. This confirmed the correct answer and produced the final flag:

hackzero{skydive_arizona}


