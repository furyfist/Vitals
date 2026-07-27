# Project Demo Video — Design Brief (Landscape)

This is a format departure from the reel series (Harness, Context Window, MCP — all
1080×1920 portrait) but a **visual continuation** of it. Same design system, same motion
grammar, same never-crop rule — just re-laid-out for a 16:9 canvas, and re-weighted
toward **architectural precision over stylistic flourish**, since the actual goal here is
showing a real hackathon project's real system architecture correctly, not explaining a
general AI concept.

---

## Video Information

**Format**
Hackathon project demo video — face cam + heavy architecture/animation focus.

**Canvas**
1920×1080 (16:9), YouTube.

**Goal**
Unlike the portrait series (which simplifies concepts for a general audience), this
video's job is to **accurately show how the actual project is built** — real components,
real data flow, correct terminology. The animation isn't decorative here; it needs to
hold up to scrutiny from technical viewers (judges, other engineers).

**Audience**
- Hackathon judges
- Software engineers
- Technical reviewers evaluating the actual build

---

## Design System

**Reuse, unchanged:**
- Color tokens: `#FAFBFC` background, `#F3F5F7` surface, `#2563EB` accent, `#DC2626`
  error/strike, `#16A34A` success
- Typography: Space Grotesk / Inter / IBM Plex Mono
- Motion grammar: soft scale-in, no bouncing, progressive builds, one active path
  highlighted at a time, calm pacing (except deliberate fast-cut moments)
- Low-mix SFX philosophy: felt on the cut, not called out

**Changes for this video:**
- Canvas orientation: 16:9 landscape instead of 9:16 portrait
- Diagram complexity: landscape gives significantly more horizontal room —
  architecture diagrams can show more nodes/layers simultaneously without needing to
  compress or paginate, unlike the portrait reels
- Content precision: diagrams must represent the **actual** project architecture
  correctly — real component names, real data flow direction, no simplified stand-ins.
  This is the opposite bias from the portrait series, which favored simplicity over
  completeness.

---

## Canvas & Layout — Framing Modes (Dynamic, Not Static)

**The corner-anchored face cam is not a permanent fixture.** A talking head permanently
pinned in the same corner for the entire runtime, with only the diagram beside it
changing, reads as a static slideshow with a webcam bug — not an edited video. This
video must actively **switch between distinct framing modes** throughout, the way
Instagram-native educational edits cut between "creator talking" and "screen content,"
not the way a recorded PPT presentation with a webcam overlay looks.

### The three modes

**1. Full Face Cam** — face cam fills the frame (or the large majority of it). Used for:
direct-address lines, the hook, personal/narrative beats, transitions between technical
sections, and anywhere the point is "a person is telling you this," not "look at this
system."

```
┌────────────────────────────────────────────┐
│                                               │
│              [face cam — full frame]        │
│                                               │
│  [caption safe area]                         │
└────────────────────────────────────────────┘
```

**2. Full Diagram / Screen** — face cam disappears entirely. The diagram/animation owns
the entire canvas. Used for dense technical beats where the architecture itself needs
full attention and a corner-cam would be pure clutter.

```
┌────────────────────────────────────────────┐
│                                               │
│         [diagram / animation — full frame]  │
│                                               │
│  [caption safe area]                         │
└────────────────────────────────────────────┘
```

**3. Split / Corner** — the small ~480×270 top-left corner-cam beside a diagram, exactly
as originally defined. **This is now the exception, used deliberately, not the default
state.** Reserve it for moments where the face and the diagram genuinely need to be
visible together — e.g. a reaction beat, or a moment where the narration is pointing at
something on screen in real time.

```
┌────────────────────────────────────────────┐
│ [face cam]                                   │
│  ~480×270                                    │
│                                               │
│              [diagram canvas]                │
│                                               │
│  [caption safe area]                         │
└────────────────────────────────────────────┘
```

### Switching rule

Cut between modes at natural narration boundaries (sentence/phrase edges from the SRT),
not mid-sentence. As a pacing guide, don't hold any single mode for the entire video —
sections should feel like they're actively cutting between "now the person is talking to
you" and "now look at this," the way real edited content does. Split/Corner mode
specifically should be used sparingly enough that its appearance feels like a deliberate
choice each time, not the default resting state the video keeps falling back to.

### Text-over-background rule

Kinetic typography (key phrases, technical terms, callouts) can appear directly on the
open canvas — not only inside boxed diagram cards. **Never place text over the face.** If
face cam is present in a shot (Full Face or Split mode), text goes in the open background
area, positioned away from the subject — same logic as the caption safe area, just
applied to in-frame typography too.

### What to avoid

The specific failure mode this section exists to prevent: a face cam that stays fixed in
the same position and size for the entire video while only the content beside it
changes. If a cut in the edit doesn't change *something* about the framing (mode, face
cam size/position, or a genuine full-frame swap) it isn't doing enough work.

- **Caption safe area**: bottom strip, full width, same 2-line-max rule as the series,
  present in all three modes. Margins scaled proportionally for 1080p (don't reuse
  pixel-exact portrait margins — recalculate as a percentage of canvas height).

---

## Visual Language

**Primary visual elements:**
- Full system architecture diagrams (multi-component, correctly labeled)
- Data/request flow arrows, directionally accurate
- Component blocks representing actual services/modules (not generic placeholder boxes)
- Code-style labels where the real project uses specific terminology
- Layered/grouped diagrams (e.g. frontend / backend / storage as visually distinct
  bands) — landscape width makes this legible in a way portrait couldn't support

**Avoid:**
- Simplifying real architecture into a "for beginners" version — this isn't an
  explainer, it's a demo
- Generic AI stock footage, cartoon illustrations, neon effects (same as the rest of the
  series)
- Overcrowding the frame just because there's more room — more space means room to
  breathe, not an excuse to cram in more nodes than the narration is actually covering
  at that moment

---

## Motion Language

Same core principles as the portrait series, applied to a bigger canvas — plus the new
mode-switching behavior above:

- Diagrams build progressively — node by node, layer by layer — never appear fully
  formed
- Only one active path/component highlighted at a time; everything else dims
- Soft scale-in on new elements, no bouncing
- Calm pacing as the default; fast-cut sections only where the narration genuinely calls
  for urgency (same exception pattern as the hook sections in the reel series)
- Arrows animate to show direction of data/control flow, not just static connectors
- **Mode transitions are themselves a motion beat** — a cut from Full Face Cam to Full
  Diagram (or vice versa) should feel like an intentional edit (a clean cut or a quick
  swipe/wipe consistent with the design system's existing motion grammar), not a hard
  jump that breaks continuity. Split mode entries/exits should use the same soft
  scale-in the rest of the system uses for other elements.

---

## Caption Rules

- Maximum 2 lines, bottom safe area, full width
- Highlight one technical keyword per caption card where relevant
- Never cover diagram elements — with the extra horizontal room, this should be easier
  to guarantee than it was in portrait, so treat any overlap as an error to fix, not an
  acceptable tradeoff

---

## Note on Cropping / Framing

Same standing rule as the rest of the series: **never crop the face cam.** In landscape
this is a lower-risk scenario than portrait (more native width to work with), but the
rule still applies exactly as before — zoom out and anchor top-left rather than cropping
the subject if the source framing doesn't match cleanly.

---

## Consistency Checklist (vs. portrait series)

| Element              | Portrait Series           | This Video (Landscape)      |
| ---------------------- | ---------------------------- | ------------------------------- |
| Canvas                 | 1080×1920                    | 1920×1080                       |
| Color tokens            | v2.0, unchanged               | Same, unchanged                 |
| Typography               | Space Grotesk/Inter/IBM Plex Mono | Same, unchanged             |
| Face cam                 | Top-left corner, small        | Dynamic — switches between Full Face, Full Diagram, and Split/Corner (corner style reused from portrait series, but no longer the default state) |
| Diagram content bias      | Simplified, beginner-friendly | Technically accurate, real architecture |
| Motion grammar             | Progressive build, no bounce  | Same                            |
| Never-crop rule             | Enforced                      | Enforced                        |
| SFX philosophy                | Low-mix, felt not heard        | Same                            |
