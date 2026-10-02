@README.md

## Working rules for Claude

- Follow the "Rules for every video" in README.md for every sim: 2:00 round, freeze at 0:00, blank space at the top, a question hook that asks people to comment, 1080×1920, auto sound, everything drawn on the canvas.
- After every finished and tested change, commit and push straight to `main` (no branches or PRs). GitHub Pages serves `main`.
- One file per video: edit it in place and never create copies or "v2" files. Don't start the next video until the user says the current one is finished.
- When a video is finished, render it with `python3 render.py <file>.html` and give the user the MP4 from `renders/`.
- Keep README.md up to date when features or rules change.
