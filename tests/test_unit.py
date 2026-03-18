"""
Unit tests for openscad_runner.

All tests in this file run without a real OpenSCAD installation; subprocess.Popen
and shutil.which are patched to avoid any real process execution or filesystem
dependency beyond the temporary scriptfile created by the scad_file fixture.
"""
from contextlib import contextmanager, ExitStack
from unittest.mock import patch, MagicMock

import pytest

from openscad_runner import OpenScadRunner, RenderMode, ColorScheme

FAKE_OPENSCAD = "/usr/bin/openscad"


@contextmanager
def make_runner(scriptfile, outfile, stderr="", stdout="", returncode=1,
                platform_name=None, **kwargs):
    """
    Context manager that constructs and runs an OpenScadRunner with mocked
    subprocess.Popen and shutil.which.

    returncode defaults to 1 (failure) so that no image post-processing is
    triggered for tests that only inspect runner.cmdline.
    """
    mock_proc = MagicMock()
    mock_proc.returncode = returncode
    mock_proc.communicate.return_value = (
        stdout.encode("utf-8"),
        stderr.encode("utf-8"),
    )

    with ExitStack() as stack:
        stack.enter_context(patch("shutil.which", return_value=FAKE_OPENSCAD))
        stack.enter_context(patch("subprocess.Popen", return_value=mock_proc))
        if platform_name is not None:
            stack.enter_context(patch("platform.system", return_value=platform_name))
        runner = OpenScadRunner(scriptfile, outfile, **kwargs)
        runner.run()
        yield runner


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------

class TestRenderMode:
    def test_has_five_members(self):
        assert len(RenderMode) == 5

    def test_values(self):
        assert RenderMode.test_only.value == "Test"
        assert RenderMode.render.value == "Render"
        assert RenderMode.preview.value == "Preview"
        assert RenderMode.thrown_together.value == "Thrown Together"
        assert RenderMode.wireframe.value == "Wireframe"


class TestColorScheme:
    def test_has_eleven_members(self):
        assert len(ColorScheme) == 11

    def test_values(self):
        assert ColorScheme.cornfield.value == "Cornfield"
        assert ColorScheme.metallic.value == "Metallic"
        assert ColorScheme.sunset.value == "Sunset"
        assert ColorScheme.starnight.value == "Starnight"
        assert ColorScheme.beforedawn.value == "BeforeDawn"
        assert ColorScheme.nature.value == "Nature"
        assert ColorScheme.deepocean.value == "DeepOcean"
        assert ColorScheme.solarized.value == "Solarized"
        assert ColorScheme.tomorrow.value == "Tomorrow"
        assert ColorScheme.tomorrow_night.value == "Tomorrow Night"
        assert ColorScheme.monotone.value == "Monotone"


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------

class TestConstructor:
    def test_finds_openscad_on_path(self, scad_file, out_png):
        with patch("shutil.which", return_value=FAKE_OPENSCAD):
            runner = OpenScadRunner(scad_file, out_png)
        assert runner.OPENSCAD == FAKE_OPENSCAD

    def test_falls_back_to_mac_path(self, scad_file, out_png):
        mac_path = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"

        def which_side_effect(path):
            return mac_path if path == mac_path else None

        with patch("shutil.which", side_effect=which_side_effect), \
             patch("platform.system", return_value="Darwin"):
            runner = OpenScadRunner(scad_file, out_png)
        assert runner.OPENSCAD == mac_path

    def test_falls_back_to_windows_path(self, scad_file, out_png):
        win_path = "C:\\Program Files\\openSCAD\\openscad.com"

        def which_side_effect(path):
            return win_path if path == win_path else None

        with patch("shutil.which", side_effect=which_side_effect), \
             patch("platform.system", return_value="Windows"):
            runner = OpenScadRunner(scad_file, out_png)
        assert runner.OPENSCAD == win_path

    def test_raises_when_no_openscad_found(self, scad_file, out_png):
        with patch("shutil.which", return_value=None), \
             patch("platform.system", return_value="Linux"):
            with pytest.raises(Exception, match="Can't find OpenSCAD"):
                OpenScadRunner(scad_file, out_png)

    def test_stores_init_params(self, scad_file, out_png):
        with patch("shutil.which", return_value=FAKE_OPENSCAD):
            runner = OpenScadRunner(
                scad_file, out_png,
                imgsize=(320, 240),
                antialias=2.0,
                animate=5,
                animate_duration=500,
                render_mode=RenderMode.render,
                show_axes=False,
                show_scales=False,
                show_edges=True,
                show_crosshairs=True,
                camera=[0, 0, 0, 0, 0, 0, 100],
                orthographic=True,
                auto_center=True,
                view_all=True,
                color_scheme=ColorScheme.metallic,
                csg_limit=50,
                deps_file="deps.mk",
                make_file="Makefile",
                set_vars={"x": 1},
                customizer_file="params.json",
                customizer_params={"s": 2},
                hard_warnings=True,
                quiet=True,
                verbose=True,
                enabled=["fast-csg"],
            )
        assert runner.scriptfile == scad_file
        assert runner.outfile == out_png
        assert runner.imgsize == (320, 240)
        assert runner.antialias == 2.0
        assert runner.animate == 5
        assert runner.animate_duration == 500
        assert runner.render_mode == RenderMode.render
        assert runner.show_axes is False
        assert runner.show_scales is False
        assert runner.show_edges is True
        assert runner.show_crosshairs is True
        assert runner.camera == [0, 0, 0, 0, 0, 0, 100]
        assert runner.orthographic is True
        assert runner.auto_center is True
        assert runner.view_all is True
        assert runner.color_scheme == ColorScheme.metallic
        assert runner.csg_limit == 50
        assert runner.deps_file == "deps.mk"
        assert runner.make_file == "Makefile"
        assert runner.set_vars == {"x": 1}
        assert runner.customizer_file == "params.json"
        assert runner.customizer_params == {"s": 2}
        assert runner.hard_warnings is True
        assert runner.quiet is True
        assert runner.verbose is True
        assert runner.enabled == ["fast-csg"]

    def test_pre_run_state(self, scad_file, out_png):
        with patch("shutil.which", return_value=FAKE_OPENSCAD):
            runner = OpenScadRunner(scad_file, out_png)
        assert runner.complete is False
        assert runner.success is False
        assert runner.return_code is None
        assert runner.cmdline == []


# ---------------------------------------------------------------------------
# Command-line building tests
# ---------------------------------------------------------------------------

class TestCmdlineBuilding:
    def test_base_command_structure(self, scad_file, out_png):
        with make_runner(scad_file, out_png) as runner:
            assert runner.cmdline[0] == FAKE_OPENSCAD
            assert runner.cmdline[1] == "-o"
            assert runner.cmdline[2] == out_png
            assert runner.cmdline[-1] == scad_file

    def test_imgsize(self, scad_file, out_png):
        with make_runner(scad_file, out_png, imgsize=(320, 240)) as runner:
            assert "--imgsize=320,240" in runner.cmdline

    def test_antialias_scales_imgsize(self, scad_file, out_png):
        with make_runner(scad_file, out_png, imgsize=(640, 480), antialias=2.0) as runner:
            assert "--imgsize=1280,960" in runner.cmdline

    def test_show_edges(self, scad_file, out_png):
        with make_runner(scad_file, out_png, show_edges=True) as runner:
            assert "--view=axes,scales,edges" in runner.cmdline

    def test_show_crosshairs(self, scad_file, out_png):
        with make_runner(scad_file, out_png, show_crosshairs=True) as runner:
            assert "--view=axes,scales,crosshairs" in runner.cmdline

    def test_no_view_arg_when_all_view_options_off(self, scad_file, out_png):
        with make_runner(scad_file, out_png, show_axes=False, show_scales=False) as runner:
            assert not any(
                isinstance(a, str) and a.startswith("--view")
                for a in runner.cmdline
            )

    def test_camera(self, scad_file, out_png):
        with make_runner(scad_file, out_png, camera=[0, 0, 0, 0, 0, 0, 100]) as runner:
            assert "--camera" in runner.cmdline
            idx = runner.cmdline.index("--camera")
            assert runner.cmdline[idx + 1] == "0,0,0,0,0,0,100"

    def test_orthographic(self, scad_file, out_png):
        with make_runner(scad_file, out_png, orthographic=True) as runner:
            assert "--projection=o" in runner.cmdline

    def test_perspective(self, scad_file, out_png):
        with make_runner(scad_file, out_png, orthographic=False) as runner:
            assert "--projection=p" in runner.cmdline

    def test_auto_center(self, scad_file, out_png):
        with make_runner(scad_file, out_png, auto_center=True) as runner:
            assert "--autocenter" in runner.cmdline

    def test_view_all(self, scad_file, out_png):
        with make_runner(scad_file, out_png, view_all=True) as runner:
            assert "--viewall" in runner.cmdline

    def test_animate(self, scad_file, out_png):
        with make_runner(scad_file, out_png, animate=5) as runner:
            assert "--animate" in runner.cmdline
            idx = runner.cmdline.index("--animate")
            assert runner.cmdline[idx + 1] == "5"

    def test_render_mode_render(self, scad_file, out_png):
        with make_runner(scad_file, out_png, render_mode=RenderMode.render) as runner:
            assert "--render" in runner.cmdline

    def test_render_mode_preview(self, scad_file, out_png):
        with make_runner(scad_file, out_png, render_mode=RenderMode.preview) as runner:
            assert "--preview" in runner.cmdline

    def test_render_mode_thrown_together(self, scad_file, out_png):
        with make_runner(scad_file, out_png, render_mode=RenderMode.thrown_together) as runner:
            assert "--preview" in runner.cmdline
            idx = runner.cmdline.index("--preview")
            assert runner.cmdline[idx + 1] == "throwntogether"

    def test_render_mode_wireframe(self, scad_file, out_png):
        with make_runner(scad_file, out_png, render_mode=RenderMode.wireframe) as runner:
            assert "--render" in runner.cmdline
            assert "--view=axes,scales,wireframe" in runner.cmdline

    def test_render_mode_test_only(self, scad_file, out_png):
        with make_runner(scad_file, out_png, render_mode=RenderMode.test_only) as runner:
            assert any(arg.endswith(".term") for arg in runner.cmdline)

    def test_color_scheme_metallic(self, scad_file, out_png):
        with make_runner(scad_file, out_png, color_scheme=ColorScheme.metallic) as runner:
            assert "--colorscheme" in runner.cmdline
            idx = runner.cmdline.index("--colorscheme")
            assert runner.cmdline[idx + 1] == ColorScheme.metallic

    def test_default_color_scheme_no_colorscheme_arg(self, scad_file, out_png):
        with make_runner(scad_file, out_png, color_scheme=ColorScheme.cornfield) as runner:
            assert "--colorscheme" not in runner.cmdline

    def test_csg_limit(self, scad_file, out_png):
        with make_runner(scad_file, out_png, csg_limit=100) as runner:
            assert "--csglimit" in runner.cmdline
            idx = runner.cmdline.index("--csglimit")
            assert runner.cmdline[idx + 1] == 100

    def test_deps_file(self, scad_file, out_png):
        with make_runner(scad_file, out_png, deps_file="deps.mk") as runner:
            assert "-d" in runner.cmdline
            idx = runner.cmdline.index("-d")
            assert runner.cmdline[idx + 1] == "deps.mk"

    def test_make_file(self, scad_file, out_png):
        with make_runner(scad_file, out_png, make_file="Makefile") as runner:
            assert "-m" in runner.cmdline
            idx = runner.cmdline.index("-m")
            assert runner.cmdline[idx + 1] == "Makefile"

    def test_set_vars(self, scad_file, out_png):
        with make_runner(scad_file, out_png, set_vars={"x": 5, "y": 10}) as runner:
            assert "-D" in runner.cmdline
            assert "x=5" in runner.cmdline
            assert "y=10" in runner.cmdline

    def test_customizer_file(self, scad_file, out_png):
        with make_runner(scad_file, out_png, customizer_file="params.json") as runner:
            assert "-p" in runner.cmdline
            idx = runner.cmdline.index("-p")
            assert runner.cmdline[idx + 1] == "params.json"

    def test_customizer_params(self, scad_file, out_png):
        with make_runner(scad_file, out_png, customizer_params={"size": 3}) as runner:
            assert "-P" in runner.cmdline
            assert "size=3" in runner.cmdline

    def test_enabled_features_skip_blank(self, scad_file, out_png):
        with make_runner(scad_file, out_png, enabled=["fast-csg", "", "manifold"]) as runner:
            assert "fast-csg" in runner.cmdline
            assert "manifold" in runner.cmdline
            # verify blank entry was not passed as a feature value
            enable_indices = [i for i, a in enumerate(runner.cmdline) if a == "--enable"]
            enabled_features = [runner.cmdline[i + 1] for i in enable_indices]
            assert "" not in enabled_features

    def test_hard_warnings(self, scad_file, out_png):
        with make_runner(scad_file, out_png, hard_warnings=True) as runner:
            assert "--hardwarnings" in runner.cmdline

    def test_quiet(self, scad_file, out_png):
        with make_runner(scad_file, out_png, quiet=True) as runner:
            assert "--quiet" in runner.cmdline

    def test_windows_strips_empty_args(self, scad_file, out_png):
        with make_runner(scad_file, out_png, platform_name="Windows") as runner:
            assert "" not in runner.cmdline


# ---------------------------------------------------------------------------
# Output parsing tests
# ---------------------------------------------------------------------------

class TestOutputParsing:
    def test_echo_lines(self, scad_file, out_png):
        stderr = "ECHO: hello\nECHO: world\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0) as runner:
            assert "ECHO: hello" in runner.echos
            assert "ECHO: world" in runner.echos

    def test_warning_lines(self, scad_file, out_png):
        stderr = "WARNING: something deprecated\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0) as runner:
            assert "WARNING: something deprecated" in runner.warnings

    def test_error_lines(self, scad_file, out_png):
        stderr = "ERROR: syntax error\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0) as runner:
            assert "ERROR: syntax error" in runner.errors

    def test_trace_lines_go_to_errors(self, scad_file, out_png):
        stderr = "TRACE: stack trace here\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0) as runner:
            assert "TRACE: stack trace here" in runner.errors

    def test_success_on_zero_returncode_no_errors(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=0) as runner:
            assert runner.success is True

    def test_failure_on_nonzero_returncode(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=1) as runner:
            assert runner.success is False

    def test_failure_when_error_in_stderr(self, scad_file, out_png):
        stderr = "ERROR: something went wrong\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0) as runner:
            assert runner.success is False

    def test_success_with_warning_and_hard_warnings_false(self, scad_file, out_png):
        stderr = "WARNING: deprecated usage\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0,
                         hard_warnings=False) as runner:
            assert runner.success is True

    def test_failure_with_warning_and_hard_warnings_true(self, scad_file, out_png):
        stderr = "WARNING: deprecated usage\n"
        with make_runner(scad_file, out_png, stderr=stderr, returncode=0,
                         hard_warnings=True) as runner:
            assert runner.success is False

    def test_complete_after_run(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=0) as runner:
            assert runner.complete is True


# ---------------------------------------------------------------------------
# State flag tests
# ---------------------------------------------------------------------------

class TestStateFlags:
    def test_bool_false_before_run(self, scad_file, out_png):
        with patch("shutil.which", return_value=FAKE_OPENSCAD):
            runner = OpenScadRunner(scad_file, out_png)
        assert bool(runner) is False

    def test_good_false_before_run(self, scad_file, out_png):
        with patch("shutil.which", return_value=FAKE_OPENSCAD):
            runner = OpenScadRunner(scad_file, out_png)
        assert runner.good() is False

    def test_bool_true_after_successful_run(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=0) as runner:
            assert bool(runner) is True

    def test_good_true_after_successful_run(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=0) as runner:
            assert runner.good() is True

    def test_bool_true_after_failed_run(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=1) as runner:
            assert bool(runner) is True

    def test_good_false_after_failed_run(self, scad_file, out_png):
        with make_runner(scad_file, out_png, returncode=1) as runner:
            assert runner.good() is False
