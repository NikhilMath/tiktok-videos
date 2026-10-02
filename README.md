# TikTok Videos

Satisfying, chaotic physics simulations made for TikTok. Each video is **one self-contained HTML page**: open it to watch it play, or run one command to record it as a ready-to-post **2-minute, 1080×1920 MP4 with sound**.

**Live site:** https://nikhilmath.github.io/tiktok-videos/ (GitHub Pages, serves the `main` branch)

---

## Quick start

| I want to… | Do this |
|---|---|
| Watch a video play live | Open the live site, or open `videos/<file>.html` in Chrome |
| Get the MP4 to post | `python3 tools/render.py naruto` (any part of a file name works) → file appears in `renders/` |
| Make a quick test video | `python3 tools/render.py naruto 8` (an 8-second round) |
| Change how a video plays | Edit the constants at the top of its HTML file, or use its ⚙️ settings panel |

Rendering needs only **Python 3** and **Google Chrome** on a Mac. Nothing to install.

---

## Folder layout

```
tiktok-videos/
├── README.md            ← this guide
├── CLAUDE.md            ← instructions for Claude Code (points here)
├── index.html           ← live-site home page, links to every video
├── videos/              ← one HTML file per TikTok video, numbered in order
│   ├── 01-pokemon-evolve.html
│   ├── 02-hunter-x-hunter.html
│   ├── 03-sonic.html
│   ├── 04-dragon-ball.html
│   ├── 05-naruto.html
│   └── 06-one-piece.html
├── tools/
│   └── render.py        ← records a video page to an MP4
└── renders/             ← finished MP4s (git-ignored, never committed)
```

---

## Rules for every video

1. **2 minutes long.** One round with a **2:00 countdown** on screen.
2. **Freeze at the end.** At 0:00 everything stops and stays frozen on the final state. A banner shows the answer, and the recording holds the frozen frame for about 3.5 seconds.
3. **Black bands at the top and bottom (new videos).** Every new video has **solid black bands** so TikTok's own UI never covers the action: the "Following | For You" bar at the top, and the caption and username at the bottom.
   - **Top:** 220px of the 1920px video (`TOP_SPACE = 110` logical units; the video is 2× that).
   - **Bottom:** about 285px (`BOTTOM_SPACE = 142`). Videos 04 and 05 used 380px (`190`), but the user said the bottom band can be about 25% shorter, so new videos use the smaller one.
   - **Old videos stay as they are.** 01–03 were made before this rule; don't go back and add bands to them.
4. **Hook at the top for retention.** A big question that tells people to comment, visible from the very first frame. Example: *"Comment below 👇 How many CLONES at the end?"* The video then answers it at 0:00.
5. **Something new every ~10 seconds.** New enemies, power-ups, transformations or K.O.s. Viewers scroll away from slow stretches, and the user called a slow version "very boring".
6. **The outcome must be hard to guess.** Tune it so different runs end differently; the comments are people guessing.
7. **Vertical 9:16, 1080×1920, 60fps.** Pre-render anything expensive (faces, sprites, backgrounds) so it never drops frames.
8. **Sound included, automatically.** Synthesized with Web Audio, with no audio files and no "tap for sound" prompt. Sound is always recorded into the video, even if muted on screen.
9. **Everything in the video is drawn on the canvas.** Only the canvas is recorded. HTML buttons and panels are for on-screen use only.
10. **Characters are drawn in code.** Don't download official art. Faces are built from shapes; see the face helpers in videos 03–05.
11. **A completely different style each time.** Check the table in "Styles used so far" below and don't repeat a look or a game mechanic. The user asked for this explicitly so viewers don't get bored.
12. **One file per video, improved in place.** Never make "v2" copies. Finish a video before starting the next.
13. **The deliverable is the MP4.** When a video is done, render it and hand over the file from `renders/`.
14. **Always push to `main`.** Commit and push every finished change, so the live site stays current.

---

## How to make a new video (step by step)

1. **Pick the theme and a new concept.** Choose a look and a game that aren't in "Styles used so far". Decide the hook question first: it should have an answer the video reveals at 0:00.
2. **Start from the newest file.** Copy it to `videos/NN-name.html` (next number). Keep the shared engine (next section) and replace the theme parts: config, game rules, drawing, sound flavor and hook.
3. **Draw the characters in code.** Use the helper patterns already in the files: `spike()` for hair, quills, ears and horns, `head()`, `cap()`, `eyes()` and so on, with one small drawing function per character. Cache each one with `getSprite()` so it's drawn once, not every frame.
4. **Tune the pacing by simulation.** Open the page in Chrome and paste a sweep like this into the console. It runs whole rounds instantly without drawing:

   ```js
   Sound.setMuted(true);
   for (let trial = 0; trial < 10; trial++) {
     startRound();
     const curve = [];
     for (let i = 0; i < 7300 && !S.timeUp; i++) { update(1 / 60); if (i % 600 === 0) curve.push(/* the number you care about */); }
     console.log(trial, curve.join(','));
   }
   ```

   Change one knob at a time (put knobs in a `TUNING` object so you can change them from the console) until:
   - something happens every ~10s,
   - the last 30 seconds aren't dead,
   - different runs end differently.

5. **Stress-test the drawing.** One exception inside the draw loop stops the animation and makes renders hang. Run full rounds with drawing at video size:

   ```js
   Recorder.on = true; resize(); startRound();
   for (let i = 0; i < 7600; i++) { update(1 / 60); draw(); }   // must finish with no error
   Recorder.on = false; resize(); startRound();
   ```

6. **Check the 1080×1920 frame.** Look at the page with `Recorder.on = true; resize();` and check that nothing overlaps and that the black bands are clear.
7. **Update `index.html` and this README.** Add the video to the catalog and to "Styles used so far".
8. **Commit and push to `main`.**
9. **Render** with `python3 tools/render.py <name>`, look at a few frames, then deliver the MP4.

---

## The shared engine (what every video page contains)

Every page is one file with the same skeleton, top to bottom:

| Section | What it does |
|---|---|
| `CONFIG` | Round length (`ROUND_SECONDS = 120`), black bands (`TOP_SPACE`, `BOTTOM_SPACE`), `HOOK` lines, characters, `TUNING`/`Settings` |
| `layout()` / `resize()` | Logical canvas is 540 wide (×2 = 1080px video). Tall phones fill the screen. While recording, the canvas is locked to exactly 1080×1920. |
| `Sound` | Web Audio synth: `unlock()` (auto-starts where allowed, retries on any touch or key), `note()`, `burst()` (filtered noise), and `recordStream()`, which feeds the recorder even when muted |
| `S` + `startRound()` | All round state; `startRound()` resets everything and the clock |
| `step(dt)` | Fixed-step physics (240 steps a second) |
| `update(rdt)` | Real-time clock, effects, waves and spawns. At 0:00 it calls `endRound()` and freezes. |
| Drawing | Cached sprites and backgrounds, effects (rings, sparks, floating text, banners), the black bands drawn last |
| `Recorder` | Records the canvas and sound with `MediaRecorder` (MP4/H.264 when available), keeps filming the freeze for `TAIL_SECONDS`, then downloads or uploads it |
| UI / main loop | ⏺ record, 🔊 mute, ⚙️ settings, keys **M** (mute) and **R** (restart); the `requestAnimationFrame` loop |

**URL options:**

| Option | What it does |
|---|---|
| `?autorecord` | Start recording on load |
| `?seconds=8` | Shorter round, for tests |
| `?upload=/upload` | Send the finished video to the local render server instead of downloading it (used by `render.py`) |

---

## How rendering works (`tools/render.py`)

1. Starts a tiny local web server for the repo on a free port.
2. Opens the page in **headless Chrome** with `?autorecord&upload=/upload` and the flag that allows sound without a tap.
3. The page records one real-time round. When the freeze has been filmed, it POSTs the video to the server, which saves it to `renders/`.
4. macOS's built-in `avconvert` rewrites Chrome's streaming ("fragmented") MP4 into a normal MP4 with a proper duration, losslessly. Phones, Photos and TikTok handle it cleanly.
5. Chrome's console is logged. If no video arrives within the round plus 90 seconds, it stops and prints the page errors instead of hanging.

The output is about 2:05 long and about 245 MB. If the TikTok phone app rejects a file that size, upload it on tiktok.com instead.

---

## Gotchas (learned the hard way)

- **Never let the frame time go negative.** The first `requestAnimationFrame` timestamp can be *earlier* than the page's start time. Use `clamp((now - lastT) / 1000, 0, 1 / 20)`.
- **Never pass a negative radius** to `arc()` or `createRadialGradient()`. It throws, which kills the animation loop, so renders hang. This happened because `easeOutBack(0)` rounded to `-2e-16`; it now returns exactly 0 at the start.
- **`shadowBlur` ignores the canvas transform.** Multiply it by `scale` (the `blur()` helper).
- **Browsers block sound until the first tap.** Pages try to start sound on load anyway, and the render uses a Chrome flag to allow it. Phones still need one tap.
- **`localStorage` can be blocked** (private mode, `file://`/`data:` previews), so always wrap it in `try/catch`.
- **Balancing:** fixed enemy strength tends to tip into "enemies always win" or "the swarm always wins". Scaling with the game state fixed it in 05-naruto, where villain HP grows with the clone count.

---

## Video catalog

| # | File | Hook | Typical outcome |
|---|---|---|---|
| 01 | `videos/01-pokemon-evolve.html` | Comment below 👇 What will the MAX evolution be? | #009 Blastoise (60%) or #008 Wartortle |
| 02 | `videos/02-hunter-x-hunter.html` | Comment below 👇 Who will be the STRONGEST? | LV.9 Hisoka (80%) or LV.8 Illumi |
| 03 | `videos/03-sonic.html` | Comment below 👇 Who will be the STRONGEST? | LV.9 Super Sonic (75%) or LV.8 Sonic |
| 04 | `videos/04-dragon-ball.html` | Comment below 👇 Who will win the TOURNAMENT? | Any of the 12 can win; about 40% end in a decision with 2 left |
| 05 | `videos/05-naruto.html` | Comment below 👇 How many CLONES at the end? | Anywhere from about 5 to 220 clones |
| 06 | `videos/06-one-piece.html` | Comment below 👇 What will the MAX BOUNTY be? | Luffy ฿3B (about 58%) or Zoro ฿1.111B, often decided in the last 20 seconds |

### 01 · Pokémon: Pokédex evolution chain
- **Look:** neon on black, a glowing ring that cycles through rainbow colors, a chute at the top.
- **Spawning:** every ball is **Bulbasaur**, one every 0.25s.
- **Merging:** two of the same merge into the next Pokémon in **Pokédex order** (Bulbasaur → … → Mew, all 151 from Gen 1).
- **Text:** "EVOLVED!" and "FINAL FORM!" only appear the first time each Pokémon is reached.
- **Records:** "NEW RECORD!" gives slow motion and a rainbow banner.
- **Settings:** gravity 1750, bounciness 0.80.
- **Predates the band rules:** made before the top/bottom black bands existed (left as is, on purpose).

### 02 · Hunter x Hunter: power ladder
- **Engine:** same as 01.
- **Spawning:** every ball is **Gon**; merges climb a fan power ranking: Gon → Killua → … → Netero → Meruem.
- **Colors and labels:** by Nen type, with "LV.n" labels. The top tier gets "S-RANK!".
- **Layout:** the first video with blank top space (no bottom band).

### 03 · Sonic: power ladder with drawn faces
- **Engine:** same as 02.
- **Spawning:** every ball is **Tails**; merges climb to Super Sonic, Super Shadow and Hyper Sonic.
- **Faces:** drawn in code, as 3/4-view cartoon heads (`FACE_STYLES`: quills, ears, twin tails, dreadlocks, bat ears, metal jaw).

### 04 · Dragon Ball: tournament battle royale
- **Look:** completely different from 01–03. Manga/comic style: cream paper with halftone, speed lines, thick ink outlines, logo-style hook text, comic "POW!/BAM!/K.O.!" bursts and screen shake.
- **Game:** 12 fighters with code-drawn manga faces fight top-down (no gravity) on a tournament stage.
  - Every clash does damage, and fighters steer toward the nearest opponent.
  - A K.O. powers up the winner.
  - **Dragon Balls** (1–7 stars) trigger transformations: Super Saiyan, Super Saiyan Blue, Golden Frieza, Orange Piccolo…
  - "IT'S OVER 9000!" fires the first time someone passes it.
- **Ending:** last fighter standing, or a decision by HP at 0:00. The winner gets a crown.
- **Tuning:** `BASE_DAMAGE = 0.95` makes the last K.O. land between about 1:15 and 2:00.
- **Layout:** the first video with **black bands top and bottom** (380px bottom band; new videos use ~285px).

### 05 · Naruto: Shadow Clone Chaos (deliberately weird)
- **Look:** an *Infinite Tsukuyomi* red-moon world: crimson sky, drifting ash, kanji columns. The arena is a giant red moon with turning Rinne-Sharingan rings, and the screen does an inverted-color glitch flash at big moments. Characters are **floating heads**.
- **Game:**
  - The **real Naruto** (can't be popped) keeps splitting into shadow clones that swirl inside the moon.
  - **Villain waves every ~10–12s:** Gaara, Orochimaru, Kisame, Itachi, Deidara and Obito, Pain, Madara, doubles, then Kaguya.
  - Villains pop clones on contact and use jutsu (Amaterasu, Shinra Tensei, Kamui…).
  - Mobbing a villain defeats it ("RASENGAN!") and starts a Sage Mode clone frenzy.
  - Beating the final villain triggers a clone explosion until the end.
- **Balance:** villain HP scales with the current clone count (`TUNING.hpPerClone`), so every wave bites and the count rises and crashes in waves.
- **Sound:** taiko drum loop, smoke-poof crackles, villain drones, gong.

### 06 · One Piece: bounty ladder (the merge game from 01, restyled)
- **Why the same game as 01:** the user asked for the merge mechanic again, with a One Piece look instead of neon.
- **Look:**
  - The page is a treasure-map parchment with burnt edges, a map grid and a compass rose.
  - The arena is a wooden **ship's wheel** with brass rivets and turning handles, and **open sea** inside (waves, bubbles).
  - Lettering is wanted-poster style (Rockwell); the timer is a wooden sign.
- **Badges:** each ball is a round **WANTED badge** with a code-drawn face and its bounty.
- **The ladder:** every drop is **Chopper** (฿1,000). Two of the same merge up a real-bounty ladder: Nami → Brook → Franky → Usopp → Robin → Sanji → Jinbe → Zoro → **Luffy** (฿3B) → Buggy → Mihawk → Blackbeard → Shanks → Big Mom → Kaido → Whitebeard → **Roger**. The left edge shows a vertical bounty ladder.
- **Sea events every ~12s:**
  - **Rough Seas:** gravity swings side to side and it rains.
  - **Devil Fruit:** whoever touches it goes up one pirate.
  - **Buster Call:** three cannonballs that explode.
  - **Sea King:** a serpent swims under the pile and launches it.
- **Tuning:** `TUNING.attract = 2000` makes two identical badges close together pull toward each other. Without it, big pairs rarely met and Luffy was never reached.
- **Sound:** coin clinks on merges, wooden knocks on walls, shanty fanfares, wind and thunder, cannon booms, ocean swells, ship's bell.
- **Bands:** the first video with the shorter ~285px bottom band.

---

## Styles used so far (pick something different next time)

| # | Look | Arena | Game mechanic | Sound |
|---|---|---|---|---|
| 01 | Neon on black, rainbow ring | Circle and chute, gravity | Merge two of the same → next in a chain | Pentatonic blips, chimes |
| 02 | Neon on black | Circle and chute, gravity | Merge chain (power ladder) | Same as 01 |
| 03 | Neon on black, cartoon faces | Circle and chute, gravity | Merge chain (power ladder) | Same as 01 |
| 04 | Manga/comic paper, ink, halftone | Square stage, top-down | Battle royale with HP, K.O.s, power-up pickups | Punchy hits, booms, risers |
| 05 | Red-moon horror-fantasy, glitch flashes | The moon, swirling vortex | Swarm growth vs. enemy waves (guess the number) | Taiko loop, poofs, drones |
| 06 | Treasure map, wooden ship's wheel, wanted posters | Wheel and chute, gravity, sea inside | Merge chain (the user asked for 01's game) + sea events | Coins, wood knocks, shanty, ocean |

**Not used yet:**
- **Looks:** pixel-art/retro 16-bit, chalkboard doodle, vaporwave, underwater, blueprint, stained glass, claymation-like soft shapes, newspaper print.
- **Mechanics:** marble race to a finish line, elimination bracket, king of the hill (stay in a shrinking zone), tug-of-war, gravity flips, a survival countdown where items fall from the sky, territory painting (who covers the most area).
