# World News — 24 November 2026

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/robyaryansah42-art/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/robyaryansah42-art/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A one-page newspaper front page — **THE GLOBAL LEDGER** — summing up the
world news of Tuesday, 24 November 2026 in a single image.

Lead story: the EU unveils its 22nd sanctions package against Russia, with an
EU-flag panel. Also covered: Ukraine's claim of sinking a Russian warship off
Libya, Jensen Huang's return sending Nvidia up nearly $1tn, the Cikande
factory fire toll, the ICJ's genocide ruling against Myanmar over the
Rohingya, Trump's blame for the $1tn market rout, plus Alcaraz's ATP Finals
title, the chess title fight in Geneva, COP31, the Senegal boat capsizing and
Waymo's freeway halt.

## How it works

`main.py` is pure standard-library Python 3: it draws the whole front page
into an RGB buffer with a hand-built 5×7 bitmap font (no fonts, no network,
no third-party packages) and writes a deterministic PNG with a hand-rolled
encoder. Running it twice produces byte-identical output.

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024, < 1 MiB)
```

## Files

- `main.py` — the generator (entrypoint)
- `entry.png` — the rendered front page
- `LICENSE` — MIT

<sub>Entered on [make.fun](https://make.fun/?ref=sxjvzha4&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
