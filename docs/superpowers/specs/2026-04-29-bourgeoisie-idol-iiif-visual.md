# BourgeoisieIdol: IIIF Integration & Soviet Visual Transformation

**Date:** 2026-04-29
**Status:** Design Approved
**Context:** Historical Materialism Conference (Nov 5-8, 2026)

## Overview

Transform SpecIdol from text-based story evaluation to IIIF-based cultural object evaluation, with Soviet mosaic visual aesthetics. Convert existing "story" semantics to "item" semantics, where items can include IIIF manifest images + metadata or metadata-only records.

## Goals

1. **IIIF Integration:** Enable evaluation of cultural objects via IIIF manifests and catalogue metadata
2. **Visual Transformation:** Apply Soviet mosaic aesthetics (color palette, geometric framing)
3. **Semantic Conversion:** Repurpose existing story infrastructure for IIIF items
4. **Minimal Refactoring:** Preserve SpecIdol core functionality while adapting for new content type

## Non-Goals

- Advanced IIIF viewer features (zoom/pan) - use simple `<img>` initially
- Multiple item types - single unified model
- Structured metadata parsing - use free text for simplicity

## Data Model

### Current Structure (SpecIdol)

```javascript
{
  title: "Story One",
  text: "Once upon a time..."
}
```

### Converted Structure (BourgeoisieIdol)

```javascript
{
  title: "Round question/title",        // repurposed: frames evaluation context
  text: "Metadata text",                 // repurposed: free-form catalogue description
  manifest_url: "https://..." | null,    // new: IIIF manifest URL (optional)
  image_url: "https://..." | null        // new: extracted image URL (optional)
}
```

**Key Insight:** Text stories ARE IIIF items without images. No type field needed.

### Server-Side Changes (`relay.py`)

**Renames:**
- `session["stories"]` → `session["items"]`
- `story_index` → `item_index`
- `add_story` → `add_item`
- `remove_story` → `remove_item`
- Variables: `text_lines` → `text_paragraphs` (split on `\n\n`)

**New Fields:**
- `item.manifest_url` (nullable string)
- `item.image_url` (nullable string)

**Session State:**
```python
"items": [
  {
    "title": "Is this metadata complete?",
    "text": "Creator: Unknown\n\nDate: c. 1890\n\nMedium: Oil on canvas",
    "manifest_url": "https://example.org/manifest.json",
    "image_url": "https://example.org/iiif/img1/full/max/0/default.jpg"
  }
]
```

## Controller Interface

### Add Item Form (Hybrid)

```
┌─────────────────────────────────────┐
│ Add Item                            │
├─────────────────────────────────────┤
│ Round Question/Title:               │
│ [_____________________________]     │
│                                     │
│ IIIF Manifest URL (optional):      │
│ [_____________________________]     │
│ [Fetch Manifest] button             │
│                                     │
│ Metadata Text:                      │
│ [                              ]    │
│ [                              ]    │
│ [                              ]    │
│ (multi-line textarea)              │
│                                     │
│ [Add Item]                         │
└─────────────────────────────────────┘
```

**Workflow:**

1. Controller enters round question (required)
2. **With IIIF manifest:**
   - Paste manifest URL
   - Click "Fetch Manifest"
   - System fetches manifest, extracts image URL
   - Controller adds/edits metadata text
   - Add item
3. **Without IIIF manifest:**
   - Leave manifest URL blank
   - Enter metadata text
   - Add item (becomes metadata-only, like original stories)

### Import/Export JSON

Existing import/export extends naturally:

```json
{
  "items": [
    {
      "title": "Is this metadata complete?",
      "text": "Creator: Unknown\n\nDate: c. 1890\n\nMedium: Oil on canvas",
      "manifest_url": "https://example.org/manifest.json",
      "image_url": "https://example.org/iiif/img1/full/max/0/default.jpg"
    },
    {
      "title": "Does this record describe the object adequately?",
      "text": "Title: Untitled\n\nDimensions: Unknown\n\nProvenance: Gift of Anonymous Donor, 1923",
      "manifest_url": null,
      "image_url": null
    }
  ],
  "config": {
    "timer_duration": 120
  }
}
```

## Round Rendering

### Audience View (`audience.html`)

```
┌─────────────────────────────────────────────┐
│ Round Question: "Is this metadata complete?"│
├─────────────────────────────────────────────┤
│                                             │
│  ┌───────────────────────────────────┐     │
│  │                                   │     │
│  │      [IIIF Image Display]         │     │
│  │      (if image_url exists)        │     │
│  │                                   │     │
│  └───────────────────────────────────┘     │
│                                             │
│  Metadata:                                 │
│  ┌─────────────────────────────────────┐   │
│  │ Creator: Unknown                    │   │
│  │ (revealed paragraph 1)              │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ Date: c. 1890                       │   │
│  │ (revealed paragraph 2)              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Timer: 1:23.4]  [Judge panels]           │
└─────────────────────────────────────────────┘
```

### Judge View (`judge.html`)

Same layout as audience:
- Round question at top
- Image display (if image_url exists)
- Revealed metadata paragraphs
- Big red buzzer button below

### Controller View (`control.html`)

- Current item's image + metadata
- "Reveal Next Paragraph" button (sends existing `text_advance` message)
- Pause/resume, speed controls (for future auto-scroll)
- Manual paragraph stepping takes priority

### Rendering Logic

**Round start:**
1. Display round question (`item.title`)
2. If `item.image_url` exists: display image from IIIF Image API using `<img src="...">`
3. If `item.image_url` is null/empty: skip image display
4. Metadata text initially hidden

**Paragraph reveal:**
1. Controller clicks "Reveal Next Paragraph"
2. Sends existing `text_advance` WebSocket message
3. Server broadcasts `text_advanced` with current paragraph
4. All clients append paragraph to metadata display
5. Repeat until all paragraphs revealed

**Text splitting:**
- Metadata text split on `\n\n` (double newline = paragraph break)
- Current implementation splits on `\n` (lines) → change to `\n\n` (paragraphs)

**Victory condition:**
- When all paragraphs revealed and timer hasn't expired = victory (same as current)

## IIIF Technical Implementation

### Manifest Fetching

**Server-side (`relay.py`):**

```python
import urllib.request
import json

def fetch_manifest(manifest_url):
    """Fetch IIIF manifest and extract image URL"""
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            manifest = json.loads(response.read())

        image_url = extract_image_url(manifest)
        return image_url, None
    except Exception as e:
        return None, str(e)

def extract_image_url(manifest):
    """Extract first image URL from IIIF manifest (v2 or v3)"""
    # IIIF Presentation API 3.0
    try:
        return manifest['items'][0]['items'][0]['items'][0]['body']['id']
    except (KeyError, IndexError, TypeError):
        pass

    # IIIF Presentation API 2.1
    try:
        return manifest['sequences'][0]['canvases'][0]['images'][0]['resource']['@id']
    except (KeyError, IndexError, TypeError):
        pass

    return None
```

### WebSocket Protocol

**New message type:**

Controller → Server:
```javascript
{
  type: "fetch_manifest",
  data: {
    manifest_url: "https://example.org/manifest.json"
  }
}
```

Server → Controller:
```javascript
{
  type: "manifest_fetched",
  data: {
    image_url: "https://..." | null,
    error: null | "error message"
  }
}
```

### Paragraph Reveal (Reuse Existing)

**Current mechanism:**
- `text_advance` message type (controller-only)
- Splits text by lines (`\n`), tracks position
- Broadcasts `text_advanced` with current line

**Adaptation:**
- Change split delimiter: `\n` → `\n\n` (paragraphs)
- Rename variables: `text_lines` → `text_paragraphs`
- No new message types needed
- Controller "Reveal Next Paragraph" button sends existing `text_advance`

## Visual Transformation

### Color Palette

**Current (SpecIdol):**
```css
--neon-green: #0f0;
--neon-yellow: #ff0;
--neon-magenta: #f0f;
--neon-red: #f00;
--black: #000;
```

**Soviet Mosaic Palette (BourgeoisieIdol):**
```css
--soviet-ochre: #d4a574;      /* earth tone primary */
--soviet-red: #8b1a1a;        /* deep workers' red */
--soviet-blue: #2b4c7e;       /* industrial blue */
--soviet-gold: #c9a961;       /* mosaic gold accent */
--soviet-concrete: #1a1a1a;   /* darker black, concrete feel */
```

**Application:**
- Headers: ochre text on concrete background
- Buttons: red or blue with gold highlights
- Active states: gold glow (instead of neon green)
- Backgrounds: concrete with subtle texture

### Geometric Framing

**Image containers:**
- Angular CSS borders with subtle transforms
- Example: `border: 4px solid var(--soviet-ochre); transform: skewY(-2deg);`
- Diagonal clip-paths for emphasis

**Background patterns:**
- Tessellated patterns using `repeating-linear-gradient()`
- Create mosaic tile effect behind UI elements

**Judge panels:**
- Angular/diagonal shapes instead of rectangular
- Geometric arrangement

### Image Viewer

**Clean display area:**
- No visual effects applied inside image viewer
- Simple `<img>` tag with IIIF Image API URL
- Geometric frame around image container
- Tessellated pattern background behind image
- Image itself displays cleanly

## Error Handling

### Manifest Fetch Failures

**Controller form behavior:**
- "Fetch Manifest" button shows loading state
- On failure: display error message ("Could not fetch manifest")
- Allow controller to proceed anyway
- Item can be added with `image_url: null` (becomes metadata-only)
- No blocking errors

**Failure scenarios:**
- Invalid URL format
- Network timeout (10 seconds)
- Server returns non-200 status
- Invalid JSON response
- Unrecognized manifest structure

### Graceful Degradation

**Missing images:**
- If `item.image_url` is `null` or empty: skip image display, show only metadata
- Metadata-only items work identically to original text stories
- No special error state needed

**Import validation:**
- `manifest_url` and `image_url` are optional fields
- Invalid URLs logged but don't block import
- Malformed items logged with warning, import continues

## Implementation Scope

### Files Modified

**`server/relay.py`:**
- Semantic renames: `stories` → `items`, `story_index` → `item_index`, etc.
- Add: `fetch_manifest()`, `extract_image_url()` functions
- Add: `fetch_manifest` message handler
- Modify: `add_item` handler to accept `manifest_url`, `image_url` fields
- Modify: `round_start` to split text by `\n\n` (paragraphs)
- Modify: session state schema

**`www/style.css`:**
- Update CSS custom properties to Soviet mosaic palette
- Add geometric framing styles (borders, transforms, clip-paths)
- Add tessellated background patterns
- Update component styles to use new palette

**`www/app.js`:**
- Semantic renames: `addStory()` → `addItem()`, etc.
- Add: `fetchManifest()` method to SpecIdolClient class
- Modify: message handlers for new fields

**`www/control.html`:**
- Add: hybrid "Add Item" form (manifest URL field, fetch button)
- Modify: item queue display (show round question + metadata preview)
- Modify: round controls ("Reveal Next Paragraph" button)
- Semantic renames: "Story" → "Item" throughout

**`www/audience.html`:**
- Add: image display area (conditional on `image_url`)
- Modify: metadata text container for paragraph reveal
- Add: round question display at top
- Update: styling for Soviet aesthetic

**`www/judge.html`:**
- Same changes as audience view
- Buzzer button unchanged

### Unchanged Components

**Preserved functionality:**
- Timer logic and display
- Buzzer mechanism (judges buzz when done evaluating)
- Session management (codes, multiple sessions)
- Judge assignment (auto-sequential IDs)
- WebSocket infrastructure
- Victory/buzzed-out conditions
- Import/export core mechanism

## Testing Approach

**Manual browser testing** (per BOOTSTRAP.md):

1. **Item creation:**
   - Add item with IIIF manifest URL → verify image displays
   - Add item without manifest → verify metadata-only display
   - Test manifest fetch failures → verify graceful degradation

2. **Round flow:**
   - Start round with IIIF item → verify image + question display
   - Controller reveals paragraphs → verify sequential reveal
   - Judges buzz → verify buzzed-out behavior
   - All paragraphs revealed → verify victory condition

3. **Visual transformation:**
   - Verify Soviet color palette applied across all views
   - Verify geometric framing on images and panels
   - Verify tessellated backgrounds

4. **Import/export:**
   - Export session with IIIF items → verify JSON structure
   - Import session → verify items load correctly

5. **Multi-device:**
   - Test controller, judge, audience views simultaneously
   - Verify paragraph reveal synchronization
   - Verify image display across devices

## Future Enhancements

**Out of scope for initial implementation:**

- Advanced IIIF viewer (zoom, pan, multi-page)
- Structured metadata field parsing (Dublin Core)
- Configurable metadata fields per item
- Auto-scroll for metadata (currently manual paragraph reveal)
- IIIF Search API integration
- Manifest validation and preview

## Conference Context

**Historical Materialism Conference (Nov 5-8, 2026):**

This implementation serves the conference's **Marxism, Culture and the Arts** and **New Technologies and Capital Accumulation** streams by:

1. **Cultural objects as evaluation subjects:** Shifts from creative writing to cultural heritage materials
2. **IIIF as infrastructure critique:** Open standards vs platform capitalism
3. **Soviet aesthetics:** Visual language of socialist public art
4. **Catalogue metadata:** Interrogates what gets measured/valued in cultural records
5. **Round questions:** Frame evaluation criteria ("Is this metadata complete?", "Does this object deserve conservation funding?")

The format becomes a site for examining cultural gatekeeping, collective vs competitive evaluation, and alternatives to winner/loser dynamics in cultural production.
