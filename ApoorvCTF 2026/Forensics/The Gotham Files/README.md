# The Gotham Files

| Field      | Value |
|------------|-------|
| Category   | Forensics |
| Points     | 50 |
| Solves     | 341 |

## Description

A mysterious panel surfaced at this year's ComiCon. The artist left something behind.

> Author : n3twraith

## Files

- [challenge.png](./challenge.png)

## Writeup

### Flag

```text
apoorvctf{th3_c0m1cs_l13_1n_th3_PLTE}
```

### Executive Summary

The image is an indexed-color PNG (`mode P`) with a palette (`PLTE`) and explicit hint text about color channels. The visible pixels use indices `0..199`, while unused palette entries `200..255` store hidden ASCII in their red channel values. Reading those bytes reveals the flag.

### Vulnerability Analysis

The hiding method abuses palette metadata, not pixel LSBs:

- Challenge hint: "only the red light tells the truth".
- Indexed PNG contains many palette entries not referenced by image pixels.
- Unused palette slots act as covert storage.
- Red bytes from those unused entries encode text directly.

### Exploit Strategy

1. Confirm PNG is palette-based.
2. Determine which palette indices are used by actual pixels.
3. Enumerate remaining unused palette entries.
4. Read only red channel values from unused entries.
5. Convert bytes to ASCII and trim after closing brace.

### Implementation

Minimal extraction script:

```python
from PIL import Image

img = Image.open("challenge.png")
palette = img.getpalette()
palette_rgb = [palette[i:i+3] for i in range(0, len(palette), 3)]

used = set(img.getdata())
start = max(used) + 1
hidden = ''.join(chr(rgb[0]) for rgb in palette_rgb[start:])
flag = hidden.split('}')[0] + '}'

print(flag)
```

### Execution & Results

The script recovers `apoorvctf{th3_c0m1cs_l13_1n_th3_PLTE}` from the red channel of unused palette entries.

