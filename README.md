# TikTok Videos

Neon physics simulations built as single HTML pages, each one recorded into a vertical video for TikTok.

**Live site:** https://nikhilmath.github.io/tiktok-videos/ (GitHub Pages, serves `main`)

---

## Rules for every video

These apply to every video in this repo, not just the current one.

1. **2 minutes long.** Every sim runs one round with a **2:00 countdown** at the top of the screen.
2. **Freeze at the end.** At 0:00 the simulation stops and stays frozen on the final state. Nothing moves or spawns, and nothing resets. A "TIME'S UP!" banner says how far it got.
3. **Leave blank space at the top.** Keep the top 180px of the video (`TOP_SPACE` = 90 units) empty so TikTok's top bar ("Following | For You") never covers the counter, timer or hook.
4. **Hook at the top for retention.** Show a big hook at the top from the very first frame, with the timer right above it. Make it a comment prompt or question that makes people stay to see the answer (e.g. *"Comment below 👇 What will the MAX evolution be?"*). Ask a question and tell people to comment.
5. **Vertical 9:16, 1080×1920.** Black background, neon glow style, and it must run smoothly at 60fps (pre-render anything expensive).
6. **Sound included, automatically.** Use synthesized Web Audio with no audio files. There's no "tap for sound" prompt; sound starts on its own and is always recorded into the video.
7. **Everything that should be in the video is drawn on the canvas.** Only the canvas is recorded. HTML overlays (buttons, settings) don't appear in the video.
8. **One file per video, improved in place.** Each video is one self-contained `.html` file (HTML + CSS + JS, no libraries). Edit and overwrite it; don't keep old versions or "v2" copies. Finish one video completely before starting the next.
9. **The final deliverable is a video file.** When a video is done, render it to an MP4 (see below) and post that to TikTok.
10. **Always push to `main`.** Every finished change is committed and pushed to `main` right away so the live site is always current.

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

## Current video: `hunter-x-hunter.html`

**Hook:** "Comment below 👇 Who will be the STRONGEST?" (the `HOOK` constant)

Same engine, physics, settings, sound, timer, freeze and recorder as the Pokémon video below, with Hunter x Hunter characters instead:

- **Every ball that drops is Gon.** Two of the same character merge into the next one up a fan power ladder (weakest → strongest):
  Gon → Killua → Kurapika → Knuckle → Biscuit → Feitan → Uvogin → Illumi → **Hisoka** → **Chrollo** → **Youpi** → **Pitou** → **Netero** → **Meruem**
- **Ball colors and labels** use Nen types: Enhancer, Transmuter, Emitter, Conjurer, Manipulator, Specialist. Each ball shows the character's level, e.g. "LV.9 TRANSMUTER".
- **Text:** "POWER UP!" the first time each character is reached. The bold names above are S-rank and get the golden **"S-RANK!"** burst instead.
- **On screen:** counter (power ups, S-ranks, highest, record), plus a **power ladder** strip under the ring.
- **Top space:** this is the first video with the blank band at the top (`TOP_SPACE`). It's laid out top-down: counter and timer, then the hook, then the ring. The ring is a bit smaller (radius 225) so everything still fits.
- **What it reaches in 2:00:** in 20 simulated rounds, 16 ended on **LV.9 Hisoka** and 4 on LV.8 Illumi, with no overflows.
- **To change the ladder:** edit `CHAIN` (order, Nen type, S-rank flag).

## Finished: `pokemon-evolve.html`

**Hook:** "Comment below 👇 What will the MAX evolution be?" (the `HOOK` constant)

### What it does
- A big glowing ring cycles through rainbow colors, fed by a narrow chute at the top.
- **Every ball that drops is a Bulbasaur**, one every 0.25 seconds. Video settings: gravity 1750, bounciness 0.80.
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
With the video settings, about 480 Bulbasaurs drop in 2:00. Each step needs twice as many as the step before, so the realistic ceiling is #008 Wartortle (128 Bulbasaurs) or #009 Blastoise (256). In 20 simulated rounds, 12 ended on **#009 Blastoise** and 8 on **#008 Wartortle**, with no overflows.

### Customizing
- **Round length:** `ROUND_SECONDS` (keep it at 120).
- **Ball sizes:** `radiusForTier`.
- **Defaults:** `Settings` (spawn rate, gravity, bounciness). These are the values the video uses.
- **Pictures instead of names:** set `SPRITE_URL` to show a sprite image inside every ball. There's an example in the code comment.

---

## Starting the next video

1. Create a new single `.html` file in this folder, using the newest video (`hunter-x-hunter.html`) as the template, since it has the top-space layout. Reuse its timer, freeze, recorder, sound setup, canvas sizing and neon look.
2. Write a new hook question for the top.
3. Keep the 2:00 round and the freeze at the end.
4. Add it to `index.html`.
5. Iterate in place until it looks right, pushing to `main` after each change.
6. Render the final MP4 with `render.py` and post it.

## Files

| File | Purpose |
|---|---|
| `hunter-x-hunter.html` | Current video: Hunter x Hunter power ladder |
| `pokemon-evolve.html` | Finished video: Pokédex evolution chain |
| `index.html` | Live-site home page that links to each video |
| `render.py` | Renders a page to a TikTok-ready MP4 in `renders/` |
| `CLAUDE.md` | Instructions for Claude Code (points here) |
