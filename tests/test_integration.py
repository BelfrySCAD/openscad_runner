"""
Integration tests for openscad_runner.

All tests require a real OpenSCAD installation reachable as "openscad" on PATH.
They are automatically skipped when OpenSCAD is not installed.
"""
import os

import pytest

from conftest import skip_if_no_openscad
from openscad_runner import OpenScadRunner, RenderMode


@skip_if_no_openscad
def test_render_cube_to_png(scad_file, out_png):
    runner = OpenScadRunner(scad_file, out_png)
    runner.run()
    assert runner.success is True
    assert runner.complete is True
    assert os.path.exists(out_png)


@skip_if_no_openscad
def test_render_cube_to_stl(scad_file, out_stl):
    runner = OpenScadRunner(scad_file, out_stl, render_mode=RenderMode.render)
    runner.run()
    assert runner.success is True
    assert os.path.exists(out_stl)


@skip_if_no_openscad
def test_invalid_scad_fails(tmp_path, out_png):
    invalid_scad = str(tmp_path / "invalid.scad")
    with open(invalid_scad, "w") as f:
        f.write("this is not valid openscad syntax ###;")
    runner = OpenScadRunner(invalid_scad, out_png)
    runner.run()
    assert runner.success is False
    assert len(runner.errors) > 0


@skip_if_no_openscad
def test_set_vars_injection(tmp_path, out_png):
    scad = str(tmp_path / "vars.scad")
    with open(scad, "w") as f:
        f.write("cube([SIZE, SIZE, SIZE]);")
    runner = OpenScadRunner(scad, out_png, set_vars={"SIZE": 5})
    runner.run()
    assert runner.success is True


@skip_if_no_openscad
def test_hard_warnings_with_warning_scad(tmp_path, out_png):
    # Passing undef as a dimension triggers a WARNING in OpenSCAD 2022+
    scad = str(tmp_path / "warn.scad")
    with open(scad, "w") as f:
        f.write("cube([undef, 1, 1]);")
    runner = OpenScadRunner(scad, out_png, hard_warnings=True)
    runner.run()
    assert runner.success is False
