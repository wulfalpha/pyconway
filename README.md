# pyconway

Conway's Game of Life as a terminal UI, built with [Textual](https://github.com/Textualize/textual).

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Installing

```sh
uv tool install .
```

This installs the `pyconway` command in uv's tool environment. Run it from any
directory:

```sh
pyconway
```

To run a checkout without installing it, use `uv run pyconway`.

`run_conway.sh` is an optional example of a personal shim around an installed
copy. It can be copied elsewhere and customized with machine-specific default
arguments; it is not needed for normal use.

## Controls

| Key           | Action                       |
| ------------- | ---------------------------- |
| `space`       | Pause / resume                |
| `l` / `→`     | Step forward one generation   |
| `h` / `←`     | Step back one generation      |
| `r`           | Randomize the board           |
| `w`           | Toggle wraparound boundaries  |
| `q`           | Quit                          |

Stepping forward or backward automatically pauses the simulation. Step-back
is backed by a bounded history buffer (200 generations by default), since
Life's rule isn't reversible on its own — most boards have more than one
possible predecessor, so the previous state has to be recorded, not computed.

## Options

```
usage: pyconway [-h] [--width WIDTH] [--height HEIGHT] [--wrap] [--seed SEED | -c] [--theme THEME]

  --width WIDTH    grid width in cells; defaults to half the terminal columns
  --height HEIGHT  grid height in cells; defaults to terminal rows minus the top bar
  --wrap           start with wraparound boundaries enabled
  --seed SEED      seed the PRNG for a reproducible initial board
  -c, --crypto     use a cryptographically secure, unseedable RNG for the initial board
  --theme THEME    Textual theme to start with (see below)
```

If `--width`/`--height` are omitted, the board is sized to fill the terminal
and stays in sync if the terminal is resized while running, preserving
whatever pattern is currently on the board (cropping or padding from the
top-left corner as needed).

`--seed` and `--crypto` are mutually exclusive: a cryptographically secure
RNG can't be seeded, so there's no meaningful way to combine reproducibility
with it.

## Theming

The app uses Textual's built-in themes (`nord`, `gruvbox`, `dracula`,
`catppuccin-mocha`, `textual-light`, etc.) — press `ctrl+p` at runtime to
open the command palette and preview them live.

To start with a specific theme, either pass `--theme`:

```sh
pyconway --theme nord
```

or set the `CONWAY_THEME` environment variable as a default (a `--theme`
flag on the command line always wins):

```bash
export CONWAY_THEME=gruvbox
```

```fish
set -x CONWAY_THEME gruvbox
```
