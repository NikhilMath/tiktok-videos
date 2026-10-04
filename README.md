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
│   ├── 06-one-piece.html
│   ├── 07-brainrot-race.html
│   ├── 08-pokemon-go-team-war.html
│   └── 09-pokemon-go-ball-rain.html
├── tools/
│   └── render.py        ← records a video page to an MP4
├── ball-battle/         ← separate Python generator: two weapon balls fight (see ball-battle/README.md)
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
- **Anything applied every physics step must be tiny.** Physics runs 240 times a second, so a "small" rolling friction of 0.02 per step made every marble in 07 crawl at about 60 units/s. 0.0015 is right.
- **Marble tracks jam where a ramp drops onto the next one.** A column of marbles wedges between the wall and the end of the upper ramp. Keep the gap wide, leave headroom under each ramp end, and nudge a stuck marble *sideways along its ramp*, not straight up (kicking everything up just rebuilds the jam).
- **Moving obstacles need an escape window.** 07's swinging pizzas first blocked the track for the whole swing and trapped marbles in a loop. They now rise clear of the track at the ends of each swing and aren't bouncy.
- **In a territory game, a target inside one team's land can only be reached by that team.** 08's raid boss sat on a gym and was almost never beaten (2–11 hits against 14 HP). Clearing a neutral zone around it and pulling everyone in made raids contested and winnable (about 85%).
- **A schedule needs a lever on both sides.** 09's throw controller could only throw *less* when catches ran ahead, but un-aimed throws still caught Pokémon and the round was decided ~35s early. What fixed it: deliberate misses for the chaos, an adaptive aimed share, and a rubber band on the catch chance itself (`pace()`).
- **Don't give a method the same name as a property.** `Sound.out()` was silently replaced by the `Sound.out` gain node, so the first elimination threw.
- **Previewing in the Claude desktop app:** its preview server can't read `~/Documents` (a macOS permission). Start `python3 -m http.server 8765` in a terminal instead; `.claude/launch.json` has a "site" entry that attaches to it.

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
| 07 | `videos/07-brainrot-race.html` | Comment below 👇 Which BRAINROT WINS the RACE? | Any of the 12 can win (each about 7–11% over 300 simulated rounds); decided 2–8s before 0:00 |
| 08 | `videos/08-pokemon-go-team-war.html` | Comment below 👇 Which TEAM takes over the MAP? | Any of the 3 teams (19/21/20 wins over 60 simulated rounds); usually decided by 1–10%, and the lead changes in the last 25s in about 80% of rounds |
| 09 | `videos/09-pokemon-go-ball-rain.html` | Comment below 👇 Which POKÉMON NEVER gets CAUGHT? | Any of the 12 (each about 2–13% over 200 simulated rounds); decided about 0–20s before 0:00 (median ~9s); about 5% end with 2 escapees |

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

### 07 · Italian Brainrot: marble race (elimination heats)
- **Why:** marble races are one of the biggest sim trends on TikTok, and the user picked Italian brainrot characters.
- **Look:** **claymation**. Pastel Tuscan diorama (sky, clay sun and clouds, rolling hills, cypress trees, a tiny leaning tower) with chunky rounded clay lettering (Arial Rounded), soft drop shadows, and marbles that squash and stretch on hard hits.
- **Racers (drawn in code, each marble *is* the character):** Tralalero Tralala, Tung Tung Tung Sahur, Bombardiro Crocodilo, Brr Brr Patapim, Lirilì Larilà, Ballerina Cappuccina, Cappuccino Assassino, Chimpanzini Bananini, Trippi Troppi, Boneca Ambalabu, Bombombini Gusini, La Vaca Saturno Saturnita.
- **Game:** every ~10s is a new **floor** (a heat). Survivors drop from a striped café starting box down a stack of ramps, and the finish door is always on the left. When all but one are through, the door slams and the last one gets squashed flat: **OUT!** (sad trombone). The final is a 1v1.
  - **Floors** are built from modules: Olive Plinko, Meatball Mountain, Trapdoor Trattoria, Spaghetti Stairs, Pizza Pendulums, Espresso Express (boost pads), Mamma Mia Mix, Olive Drop, and the Gran Finale.
  - **Special moves** every second or two (racers at the back use them more): sneaker sprint, TUNG TUNG TUNG bonk, Bombardiro's bomb, Patapim's stomp, Lirilì stops time, Bananini's banana peel, Saturnita pulls rivals back, and so on. Tap a marble to trigger its move.
  - **TRACK FLIP!** On some floors one ramp tilts the other way mid-race (the leader's, if it can).
- **Schedule:** `planHeat()` estimates how long the remaining races take (`raceBase + raceEach × racers`, times each floor's `pace`). Spare time becomes a longer wait in the starting box. If the clock runs short it picks quick floors, or makes the last 2 (or 3) go out at once ("DOUBLE OUT!", about once a round).
- **Physics:** unlike 01–06, marbles roll on capsule-shaped line segments (ramps, walls, trapdoors, a flipping ramp), with the segment's own motion passed on to the marble.
- **Sound:** a quiet tarantella (mandolin oom-pa-pa in A minor), clay thocks and plops, mandolin notes on olive pegs, boings, a sad trombone on every elimination, a goose honk, a bomb whistle.
- **Bands:** standard (top 110, bottom 142). The right wall sits at x = 476 so the action stays clear of TikTok's like/comment buttons.

### 08 · Pokémon GO: Team War (territory painting)
- **Why:** the first of three Pokémon GO videos (2026-10-04). Everyone who plays has a team, so the comments become a team war.
- **Look:** the **Pokémon GO map**: a pastel top-down city (grass, parks with trees, a river, white roads, pale buildings) under a blue sky with clouds, with a faint cell grid on top. The UI copies the game: white pill timer and weather widget, white notification cards that drop in, Avenir Next lettering. The hook's last line is in all three team colors.
- **Game:** a classic "color war". The map is 46×52 cells, split into three territories: **Mystic** (blue), **Valor** (red), **Instinct** (yellow). Each team's Pokémon roll at a steady speed; when one pushes into a rival's cell, that cell flips to its color and it bounces off. A score bar shows each team's share live, with a crown on the leader.
  - **Pokémon (balls with code-drawn faces):** Mystic: Squirtle, Marill, Poliwag, Spheal. Valor: Charmander, Torchic, Vulpix, Growlithe. Instinct: Pikachu, Pichu, Joltik, Voltorb. Three per team at the start, at most 7.
  - **Gyms** change color when the cell under them flips, and paint a small circle around them ("GYM TAKEN!"). PokéStops spin purple when someone passes.
- **Events every ~9s** (a shuffled deck, a bird first):
  - **Legendary birds:** Articuno, Moltres or Zapdos swoops across the map, painting a wide stripe through the biggest rival's land. The team that's furthest behind is the likeliest to get its bird.
  - **Weather:** rain, sun or a thunderstorm boosts one team's speed (×1.65) for 8s.
  - **Team GO Rocket:** the Meowth balloon floats over the leader, bombs patches of its land into neutral (dark) cells that anyone can take, and steals one of its Pokémon.
  - **Raid Battle:** an egg hatches a Snorlax on a gym and clears a neutral zone around it; every Pokémon is pulled in, and the team that hits it most wins 2 new Pokémon and a big paint burst (about 85% of raids are won; otherwise "SNORLAX FLED!").
  - **Wild Pokémon:** three Poké Balls land and hatch into whichever team owns that spot. **Lure Module:** everyone is pulled toward one PokéStop.
  - **Legendary finale** at 0:14: all three birds at once.
- **Ending:** at 0:00 the team with the most cells wins: "TEAM MYSTIC TAKES OVER THE MAP!" with the final percentages.
- **Sound:** a marimba "walking around the map" loop (C–Am–F–G), a different pop per team when cells flip (glassy, warm, zappy), notification dings, bird cries, villain motif and bombs, rain and thunder, raid hits and a fanfare in the winner's key.
- **Tap the map** to drop in a new Pokémon for whichever team owns that spot.

### 09 · Pokémon GO: Poké Ball Rain (survival)
- **Why:** the second Pokémon GO video. The 1-2-3 wobble and "broke free!" are the most suspenseful moment in the game.
- **Look:** an **AR camera at golden hour**: a city park seen through a phone viewfinder (corner brackets, "AR" badge, vignette, film grain, lens flare from a low sun). The sun sets over the 2 minutes: golden hour fades to dusk, the skyline's windows light up, stars come out and the lamp posts switch on. Lettering is bold italic, like the game's "Excellent!" text. The HUD is translucent camera-app pills.
- **Game:** 12 wild Pokémon (drawn in code, side view, with walking feet) live on the lawn, a bench, a playground deck and a rock. Poké Balls rain down; a ball that hits a Pokémon pulls it in, then **wobble, wobble, wobble → GOTCHA!**, or it **BROKE FREE!** at any wobble. The last Pokémon never caught wins.
  - **The cast and their moves:** Pikachu (Quick Attack dash), Bulbasaur (Vine Whip swats a ball away), Charmander (Ember burns a ball), Squirtle (Water Gun), Eevee (Dig), Jigglypuff (puffs up and floats), Snorlax (never moves; Thick Fat bounces balls off), Gengar (phases through balls), Magikarp (Splash… but nothing happened), Abra (Teleport), Ditto (transforms into a Poké Ball), Mew (flies; Psychic barrier).
  - **GO details:** the shrinking catch ring (green/yellow/orange/red by catch rate) shows on targeted Pokémon, and its size at impact gives Nice!/Great!/Excellent!. Catch chance = base rate × ball × throw × curveball × berry.
- **Events about every 10s:** Great Balls (0:09), Ultra Balls (0:39), Night Falls (Gengar gets stronger, 1:18), Master Ball (locks on and homes in, 1:38), Final Throws (last 12s), plus a shuffled set: Razz Berries, Golden Razz Berry, Curveballs, Team GO Rocket's balloon vacuuming up balls, Windy, Excellent Throws. Fireworks once a winner is decided.
- **Pacing (two controllers):** a rising "rain" of throws keeps it chaotic, and the share aimed at Pokémon adapts so catches follow a schedule (`throwPlan()`). On top of that, `pace()` makes Pokémon break free more often when catches run ahead of schedule (and less often when behind). The last free Pokémon can't be caught while another is still wobbling, so it never ends with zero.
- **Ending:** "LAST ONE LEFT!" with fireworks, then at 0:00 "NEVER CAUGHT!" with the winner in a spotlight (or "2 ESCAPED!"). A ball still wobbling at 0:00 is settled on the spot.
- **Sound:** an E-minor "wild encounter" groove (kick, claps, octave synth bass, stabs), throw whooshes, the capture zap, click-clack wobbles, a Gotcha chime, a breakout pop, a sound for each special move, and fireworks.
- **Tap** a Pokémon to throw a ball at it (or anywhere to throw one there).

### Ball Battle (Python generator, `ball-battle/`)
- **What it is:** a separate tool, made from the user's own spec, so its rules differ from the HTML videos.
- **Video:** 30–60 second fights, an end freeze of 2 seconds, and a layout that keeps clear of TikTok's bottom 20% and right edge.
- **How it works:** pygame draws frames off-screen and ffmpeg encodes them about 3.5× faster than real time. Sound effects are generated with numpy and mixed in at each event's exact time.
- **Commands:** `ball_battle.py --find-seed` searches for close fights in seconds, and `CONFIG` holds everything for a new episode.
- **Details:** setup, episodes and balancing are in `ball-battle/README.md`.

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
| 07 | Claymation: pastel clay diorama, squash & stretch | Vertical stack of ramps, rebuilt every floor | Marble race in elimination heats (last one out) + special moves, track flips | Tarantella mandolin, boings, plops, sad trombone |
| 08 | Pokémon GO map: pastel top-down city, white GO-style cards and pills | Grid of cells over the city, no gravity | Territory painting (color war: flip a rival's cell, bounce off) + legendary-bird swoops, weather, raids | Marimba map loop, per-team flip pops, bird cries |
| 09 | AR camera at golden hour: sunset park, lens flare, film grain, viewfinder; fades to night | Side view: lawn, bench, playground deck, rock, gravity | Survival: items fall from the sky (Poké Balls), 1-2-3 wobble catch or break free, last one uncaught wins | Encounter groove (claps, synth bass), wobble clicks, Gotcha chime |
| Ball Battle | Dark neon arena, glow and trails (Python) | Circle, no gravity, +5% speed per bounce | 1v1 spinning-weapon duel with HP | Generated blips, thuds, metal clangs |

**Not used yet:**
- **Looks:** pixel-art/retro 16-bit, chalkboard doodle, vaporwave, underwater, blueprint, stained glass, newspaper print.
- **Mechanics:** elimination bracket (head-to-head), king of the hill (stay in a shrinking zone), tug-of-war, gravity flips.

**Next up** (trending ideas the user liked, 2026-10-02; 07 was the first of them):
- **Escape the rings:** balls in ~50 spinning rings with gaps; each escape breaks a ring and adds balls. "How many rings will break?" Look: vaporwave.
- **Domain Expansion war** (Jujutsu Kaisen): Gojo, Sukuna, Megumi and Mahito paint territory; DOMAIN EXPANSION paints a big circle. "Who owns the most territory?" Look: stained glass. (08 has since used territory painting, so this one needs a different twist.)
- **Pokémon type war:** rock-paper-scissors swarms (fire > grass > water > fire). "Which starter takes over?" Look: Game Boy pixel art.
- **Horse Race Test:** horses bounce through a maze toward a carrot. "Which horse gets the carrot?" Look: blueprint or newspaper print.
