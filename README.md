# TikTok Videos

Neon physics simulations built as single HTML pages, each one recorded into a vertical video for TikTok.

**Live site:** https://nikhilmath.github.io/tiktok-videos/ (GitHub Pages, serves `main`)

---

## Rules for every video

These apply to every video in this repo, not just the current one.

1. **2 minutes long.** Every sim runs one round with a **2:00 countdown** at the top of the screen.
2. **Freeze at the end.** At 0:00 the simulation stops and stays frozen on the final state. Nothing moves or spawns, and nothing resets. A "TIME'S UP!" banner says how far it got.
3. **Hook at the top for retention.** Show a big hook at the top from the very first frame, with the timer right above it. Make it a comment prompt or question that makes people stay to see the answer (e.g. *"Write in the comments what the MAX evolution will be!"*).
4. **Vertical 9:16, 1080×1920.** Black background, neon glow style, and it must run smoothly at 60fps (pre-render anything expensive).
5. **Sound included, automatically.** Use synthesized Web Audio with no audio files. There's no "tap for sound" prompt; sound starts on its own and is always recorded into the video.
6. **Everything that should be in the video is drawn on the canvas.** Only the canvas is recorded. HTML overlays (buttons, settings) don't appear in the video.
7. **One file per video, improved in place.** Each video is one self-contained `.html` file (HTML + CSS + JS, no libraries). Edit and overwrite it; don't keep old versions or "v2" copies. Finish one video completely before starting the next.
8. **The final deliverable is a video file.** When a video is done, render it to an MP4 (see below) and post that to TikTok.
9. **Always push to `main`.** Every finished change is committed and pushed to `main` right away so the live site is always current.

---

## Making the video

### Option A: one command (recommended)

```bash
python3 render.py pokemon-evolve.html
```

This opens the page in headless Chrome, records one full round (2:00 plus about 3.5 seconds of the frozen end screen) with sound, and saves a standard **1080×1920 MP4** in `renders/`. AirDrop or upload that file to TikTok.

- Quick test render: `python3 render.py pokemon-evolve.html 8` records an 8-second round.
- Needs only Python 3 and Google Chrome. macOS's built-in `avconvert` converts Chrome's streaming-format recording into a normal MP4 losslessly.
- `renders/` is git-ignored, so videos are never committed.

### Option B: the ⏺ button

Open the page (locally or on the live site) and press **⏺** in the top-right corner. It starts a fresh round, records it, and saves the MP4 when the end screen has been held for a few seconds. Press **⏹** to stop early. Keep the tab visible while recording.

### Page URL options

| Option | What it does |
|---|---|
| `?autorecord` | Start recording as soon as the page loads |
| `?seconds=10` | Make the round shorter (for testing) |
| `?upload=/path` | Send the finished video to that same-site path instead of downloading it (used by `render.py`) |

---

## Current video: `pokemon-evolve.html`

**Hook:** "Write in the comments what the MAX evolution will be!" (the `HOOK` constant)

### What it does
- A big glowing ring cycles through rainbow colors, fed by a narrow chute at the top.
- **Every ball that drops is a Bulbasaur**, one every 0.8 seconds.
- **Two of the same Pokémon merge into the next one in Pokédex order.** It's one straight line with no branching: Bulbasaur → Ivysaur → Venusaur → Charmander → … → Mewtwo → Mew (all 151 from Gen 1).
- Each ball shows the Pokémon's name, Pokédex number and type, in its type's color. Balls get bigger the further along the chain they are.
- **Effects:**
  - **Every merge:** small ring burst, sparks and a chime, with no text.
  - **First time a Pokémon is reached in the round:** a floating "EVOLVED!" with its name. If it's fully evolved (like Venusaur or Charizard), you get **"FINAL FORM!"** with a golden burst, screen flash and a chord instead.
  - **"NEW RECORD!"** (when it beats the all-time best, from #006 on): rainbow banner and 30% slow motion for 2 seconds.
- **Physics:** gravity, bouncy walls, mass-based ball collisions, and a random sideways kick as each ball leaves the chute.
- **Sound:** musical blips on wall hits (pitch depends on where the ball hits), rising chimes, chords, ticks in the last 5 seconds, and a bell at time's up.
- **On screen:** counter (evolutions, Final Forms, highest this round, all-time record), 2:00 timer (red and pulsing for the last 10 seconds), and a Pokédex progress strip under the ring.
- **Overflow:** if balls back up into the chute for 3 seconds, "OVERFLOW!" shows and the ring clears. The clock and round stats keep going.
- **Controls (not in the video):**
  - Tap inside the ring to drop a Bulbasaur.
  - ⚙️ settings: spawn rate, gravity, bounciness, Reset, Clear Record.
  - 🔊 mute (only mutes your speakers; recordings still have sound).
  - Keys: **M** mutes, **R** restarts the round.

### What it reaches in 2 minutes
About 150 Bulbasaurs drop in 2:00. Each step needs twice as many as the step before, so #007 Squirtle (64 Bulbasaurs) is the realistic ceiling. In 40 simulated rounds, 38 ended on **#007 Squirtle** and 2 on #006 Charizard, with no overflows.

To change that, lower **Spawn every** in settings. About 0.45s gets to #009 Blastoise (256 Bulbasaurs) within 2:00.

### Customizing
- **Round length:** `ROUND_SECONDS` (keep it at 120).
- **Ball sizes:** `radiusForTier`.
- **Defaults:** `Settings` (spawn rate, gravity, bounciness).
- **Pictures instead of names:** set `SPRITE_URL` to show a sprite image inside every ball. There's an example in the code comment.

---

## Starting the next video

1. Create a new single `.html` file in this folder, using `pokemon-evolve.html` as the template. Reuse its timer, freeze, recorder, sound setup, canvas sizing and neon look.
2. Write a new hook question for the top.
3. Keep the 2:00 round and the freeze at the end.
4. Add it to `index.html`.
5. Iterate in place until it looks right, pushing to `main` after each change.
6. Render the final MP4 with `render.py` and post it.

## Files

| File | Purpose |
|---|---|
| `pokemon-evolve.html` | Current video: Pokédex evolution chain |
| `index.html` | Live-site home page that links to each video |
| `render.py` | Renders a page to a TikTok-ready MP4 in `renders/` |
| `CLAUDE.md` | Instructions for Claude Code (points here) |
