@README.md

## Working rules for Claude

- Follow "Rules for every video" and "How to make a new video" in README.md exactly:
  - 2:00 round, freeze at 0:00
  - black bands at the top (TOP_SPACE 110) and bottom (BOTTOM_SPACE 142, about 25% shorter than the 190 used in 04–05); new videos only, never retrofit 01–03
  - a question hook that says "Comment below 👇"
  - something new every ~10s and an unpredictable outcome
  - 1080×1920, auto sound, everything drawn on the canvas, characters drawn in code
- Every new video must use a look and a game mechanic that aren't in README → "Styles used so far". Add the new one to that table.
- Videos live in `videos/NN-name.html` (next number); start from the newest one. One file per video, edited in place: never make copies or "v2" files.
- Before rendering, always:
  1. tune the pacing by simulating rounds in the browser console
  2. stress-test full rounds with `update(); draw();` at video size (an exception in the draw loop makes renders hang)
  3. look at the 1080×1920 frame
- After every finished and tested change, commit and push straight to `main` (no branches or PRs). GitHub Pages serves `main`.
- When a video is done, render it with `python3 tools/render.py <name>`, check a few frames, and give the user the MP4 from `renders/`.
- Keep README.md up to date (catalog, styles table, gotchas) whenever something changes.
