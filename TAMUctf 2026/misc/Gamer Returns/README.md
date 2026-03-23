# Gamer Returns

| Field      | Value |
|------------|-------|
| Category   | misc |
| Points     | 55 |
| Solves     | 184 |

## Description

<p>Author: <code>flocto</code></p><p>The gamer is back and returns with a vengeance.</p><p>Note: No <code>-</code> in the flag. Also the flag is case insensitive.</p>

## Files

- [gamer-returns.tar.gz](./gamer-returns.tar.gz)

## Writeup

### Flag

```
gigem{t1me_4_g4m1ng}
```

### Executive Summary

This was a really fun Minecraft-themed misc challenge. The attachment was a tarball, and after extracting it, I found just a single file: sus.txt. When I opened it, the whole file was one giant line starting with a Minecraft summon command for a bat with SNBT-style data. The banners themselves were the message—they needed to be parsed, rendered, and decoded to reveal the flag.

### Vulnerability Analysis

The file contained non-standard SNBT format (Stringified Named Binary Tag), not valid JSON. Keys were unquoted, numbers had suffixes like `1b`, and the structure was Minecraft-flavored game data.

The interesting part was a bat with a long `Passengers` array containing chest minecarts. Inside each minecart was an `Items` list full of banners (red and white), each with a `banner_patterns` list containing entries like:
- stripe_top
- stripe_center
- border
- creeper
- curly_border

The file contained:
- 10 chest minecart passengers
- 110 red banners
- 29 white banners
- 139 total banners encoding the message

### Exploit Strategy

**Step 1: Parse the SNBT**

The data was not valid JSON, so I wrote a quick recursive parser in Python that handled:
- Compounds: `{ ... }`
- Lists: `[ ... ]`
- Strings and tokens like `1b`, `69`, `true`, `false`

**Step 2: Extract the Banners**

Once parsed, I extracted all banner items from the chest minecarts and their pattern lists.

**Step 3: Render the Banners**

Instead of manually reasoning through the banner patterns, I decided to render them properly. I grabbed the vanilla banner pattern textures and the banner base texture, then layered them the same way Minecraft does:
- Start with the banner base texture
- Color it red or white depending on the base banner
- Overlay each pattern texture in order
- Crop the visible cloth area
- Scale it up so the glyphs were easy to read

**Step 4: Build the Glyph Alphabet**

Once I rendered everything, I deduplicated the pattern stacks. There were only 36 unique banner signatures, which made things much easier. I rendered all banners in sequence into rows.

![Rendered banner rows](./image.png)

Once I had the visual output, I could read the message. Most of the visible rows included obvious decoy text like `TRY-AGAIN`, `{FAKE-FLAG}`, `FLAG-NOT-FOUND}`, `KEEP-LOOKING`, `{REAL-FLAG}`, and `ENJOY-TAMUCTF`.

Most rows were made from the red-banner alphabet, but one row stood out because it used white-banner variants in a different way. Using the rows I had already decoded as an alphabet reference, I reused that mapping on the odd row, and it resolved into the real flag.

### Implementation

**SNBT Parser**
- Handles recursive compound and list parsing
- Maps unquoted keys, numeric suffixes, and game data types

**Banner Renderer**
- Used PIL/Pillow for image manipulation
- Layered vanilla textures matching Minecraft's banner rendering logic
- Scaled output for visibility

### Execution & Results

The solve flow was:
1. Parse the SNBT from sus.txt
2. Extract all minecart items
3. Render each banner from vanilla textures
4. Stitch banners into rows
5. Use the decoded rows as a glyph alphabet
6. Apply the mapping to the anomalous row

**Hidden Row Decoded to:**
```
gigem{t1me_4_g4m1ng}
```

The two most important ideas were recognizing the file as Minecraft SNBT instead of random text, and rendering the banner patterns instead of trying to decode them by hand. That second decision saved a lot of time.


