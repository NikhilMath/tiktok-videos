# Ball Battle

Two balls with spinning weapons fight in a circular arena. One Python file renders the whole thing to a **1080×1920, 60 fps MP4 with sound**, faster than real time and with no window.

- **Weapons:** each weapon spins around its ball. A weapon hitting the other ball takes HP and makes it flash white.
- **Clashes:** when the two weapons hit each other, both balls bounce apart in a shower of sparks.
- **Wall bounces:** each one makes that ball 5% faster, up to a cap.
- **Ending:** the last ball standing wins, and the video freezes on a winner screen for 2 seconds.

## Setup (once)

From this folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`imageio-ffmpeg` comes with its own ffmpeg, so there's nothing else to install.

## Make a video

```bash
.venv/bin/python ball_battle.py
```

The MP4 is saved to `../renders/` (for example `ball-battle-sword-vs-spear-seed24.mp4`). A 35-second episode renders in about 10 seconds on an M-series Mac.

## Make a new episode

1. **Edit `CONFIG`** at the top of `ball_battle.py`:
   - `title`: for example `"AXE vs DAGGER — who wins?"`. The part after "—" goes on a smaller second line, and team names are colored automatically.
   - `teams`: each team's `name`, `color` and `weapon` (`sword`, `spear`, `axe`, `dagger`, `hammer` or `scythe`).
   - `image` (optional): a PNG path to use as that ball's face; it's cropped to a circle.
   - `weapon_overrides` (optional): to tweak one team's weapon, e.g. `{"damage": 12}`.
   - `weapons`: change length, thickness, spin (turns per second) or damage for any weapon.
2. **Find a good seed** (a fight that lasts 30–60 seconds with a close finish):

   ```bash
   .venv/bin/python ball_battle.py --find-seed
   ```

   It runs hundreds of fights in a few seconds without drawing, and prints matches like `seed 24: 32.9 s, SPEAR wins with 1 HP`. You can change the search limits in `CONFIG["find_seed"]`.
3. **Render it:**

   ```bash
   .venv/bin/python ball_battle.py --seed 24
   ```

   Or put the seed in `CONFIG["seed"]` and run it with no arguments.

The same seed always gives exactly the same fight, so you can preview with `--find-seed` and render later.

## Balance note

The sword and spear defaults were tuned so each wins about half the time over 160 seeds. Other matchups (axe, hammer and so on) haven't been balanced. If one weapon wins too often, nudge its `damage` or `spin` and check again. `--find-seed` prints who wins each match.

## TikTok-safe layout

- The title, HP bars and arena stay clear of the top bar, the right-side buttons (everything is kept left of x = 920), and the bottom 20%, where captions sit (the arena ends at y = 1510).
- Weapons and sparks are clipped to the arena, so nothing pokes into those areas.
