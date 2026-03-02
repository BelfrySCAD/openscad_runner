import shutil
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires OpenSCAD to be installed")


@pytest.fixture
def scad_file(tmp_path):
    """Minimal valid .scad file."""
    f = tmp_path / "test.scad"
    f.write_text("cube([1,1,1]);")
    return str(f)


@pytest.fixture
def out_png(tmp_path):
    return str(tmp_path / "out.png")


@pytest.fixture
def out_stl(tmp_path):
    return str(tmp_path / "out.stl")


openscad_available = shutil.which("openscad") is not None
skip_if_no_openscad = pytest.mark.skipif(
    not openscad_available,
    reason="OpenSCAD not installed",
)
