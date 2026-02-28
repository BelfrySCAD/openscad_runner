# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`openscad_runner` is a Python library that wraps the OpenSCAD CLI to render `.scad` files into images (PNG, GIF, APNG) or 3D model files (STL, etc.). The entire library lives in a single file: `openscad_runner/__init__.py`.

## Development Setup

Install in editable mode with dependencies:
```bash
pip install -e ".[dev]"
# or simply
pip install -e .
```

Dependencies: `Pillow`, `pygifsicle`, `apng`

The library requires OpenSCAD to be installed on the system. It searches `PATH`, then platform-specific default locations (macOS: `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD`; Windows: `C:\Program Files\openSCAD\`).

## Building and Publishing

```bash
python -m build          # Creates dist/ with .whl and .tar.gz
twine upload dist/*      # Publish to PyPI
```

## Architecture

Everything is in `openscad_runner/__init__.py`:

- **`RenderMode` enum** — maps to OpenSCAD CLI flags: `test_only`, `render`, `preview`, `thrown_together`, `wireframe`
- **`ColorScheme` enum** — maps color scheme names to OpenSCAD's display strings
- **`OpenScadRunner` class** — the main interface:
  - `__init__()`: Stores all render parameters; locates the OpenSCAD executable via `shutil.which()`
  - `run()`: Builds the CLI command, invokes OpenSCAD via `subprocess.Popen`, parses stdout/stderr into `.echos`, `.warnings`, `.errors`, then post-processes images (antialiasing via Pillow thumbnailing, GIF optimization via pygifsicle, APNG assembly via apng)
  - `good()` / `__bool__()`: Check `.success` / `.complete` state

### Animation flow
When `animate=N` is set, OpenSCAD generates `N` numbered PNG frames. The runner then:
- For `.gif` output: assembles frames with Pillow, saves, then optimizes with `pygifsicle`
- For `.png` output: assembles frames into an APNG with the `apng` library

### Anti-aliasing
When `antialias > 1.0`, OpenSCAD renders at `imgsize * antialias` resolution, then Pillow downscales to `imgsize` using `LANCZOS` resampling.

### `test_only` mode
Outputs to a temporary `foo.term` file (deleted after run) to validate the script without producing real output.

## Key Behaviors to Know

- Success requires: `return_code == 0`, no `ERROR:`/`TRACE:` lines in stderr, and (if `hard_warnings=True`) no `WARNING:` lines
- `set_vars` injects `-D key=value` args; `customizer_params` injects `-P key=value` args
- Blank entries in `enabled` are skipped (guarded by `if feature:`)
- On Windows, empty string args are stripped from the command list before passing to OpenSCAD
