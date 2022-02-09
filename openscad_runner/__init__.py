import os
import sys
import math
import filecmp
import os.path
import platform
import subprocess

from enum import Enum
from PIL import Image, ImageChops
import pygifsicle


class RenderMode(Enum):
    """
    RenderMode Enum class.
    - test_only
    - render
    - preview
    - thrown_together
    - wireframe
    """
    test_only = "Test"
    render = "Render"
    preview = "Preview"
    thrown_together = "Thrown Together"
    wireframe = "Wireframe"


class ColorScheme(Enum):
    """
    ColorScheme Enum class.
    - cornfield
    - metallic
    - sunset
    - starnight
    - beforedawn
    - nature
    - deepocean
    - solarized
    - tomorrow
    - tomorrow_night
    - monotone
    """
    cornfield      = "Cornfield"
    metallic       = "Metallic"
    sunset         = "Sunset"
    starnight      = "Starnight"
    beforedawn     = "BeforeDawn"
    nature         = "Nature"
    deepocean      = "DeepOcean"
    solarized      = "Solarized"
    tomorrow       = "Tomorrow"
    tomorrow_night = "Tomorrow Night"
    monotone       = "Monotone"


class OpenScadRunner(object):
    def __init__(
        self, scriptfile, outfile,
        imgsize=(640,480),
        antialias=1.0,
        animate=None,
        animate_duration=250,
        render_mode=RenderMode.preview,
        show_axes=True,
        show_scales=True,
        show_edges=False,
        show_crosshairs=False,
        camera=None,
        orthographic=False,
        auto_center=False,
        view_all=False,
        color_scheme=ColorScheme.cornfield,
        csg_limit=None,
        deps_file=None,
        make_file=None,
        set_vars={},
        customizer_file=None,
        customizer_params={},
        hard_warnings=False,
        quiet=False,
        verbose=False
    ):
        """
        Initializer method.  Arguments are:
        - scriptfile = The name of the script file to process.
        - outfile = The name of the file to output to.
        - imgsize = The size of the imagefile to output to, if outputting to a PNG or GIF.  Default: (640,480)
        - antialias = The antialiasing scaling factor.  If greater than 1.0, images are generated at a larger size, then scaled down to the target size with anti-aliasing.  Default: 1.0  (no anti-aliasing)
        - animate = If given an integer number of frames, creates that many frames of animation, and collates them into an animated GIF.  Default: None
        - animate_duration = Number of milliseconds per frame for an animated GIF.  Default: 250
        - render_mode = The rendering mode to use when generating an image.  See RenderMode Enum.  Default: RenderMode.preview
        - show_axes = If True, show axes in the rendering.  Default: True
        - show_scales = If True, show the scales along the axes.  Default: True
        - show_edges = If True, shows the edges of all the faces.  Default: False
        - show_crosshairs = If True, shows the crosshairs for the center of the camera translation.  Default: False
        - camera = Gives the camera position as either [translate_x,y,z,rot_x,y,z,dist] or [eye_x,y,z,center_x,y,z]
        - orthographic = If True, render orthographic.  If False, render with perspective.  Default: False
        - auto_center = If True, and script does not set $vpt, $vpr, or $vpd, then centers the shape in the rendered image.  Default: False
        - view_all = If True, and script does not set $vpd, then the field of view is scaled to show the complete rendered shape.  Default: False
        - color_scheme = The color scheme to render an image with.  See ColorScheme Enum.  Default: ColorScheme.cornfield,
        - csg_limit = If given, the maximum number of CSG elements to render.
        - deps_file = If given, the file to write Makefile dependancies out to.
        - make_file = If given, the Makefile script to run when missing a dependency.
        - set_vars = An optional dictionary of script variables and values to set.
        - customizer_file = If given, specifies the file containing Customizer Parameters.
        - customizer_params = An optional dictionary of customizer parameter names and values to set.
        - hard_warnings = Stop at first WARNING, as if it were an ERROR.  Default: False
        - quiet = Suppresses non-error, non-warning messages.  Default: False
        - verbose = Print the command-line to stdout on each execution.  Default: False
        """
        if platform.system() == "Darwin":
            self.OPENSCAD = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
        else:
            self.OPENSCAD = "openscad"
        self.scriptfile = scriptfile
        self.outfile = outfile
        self.imgsize = imgsize
        self.antialias = antialias
        self.show_axes = show_axes
        self.show_edges = show_edges
        self.show_scales = show_scales
        self.show_crosshairs = show_crosshairs
        self.camera = camera
        self.color_scheme = color_scheme
        self.auto_center = auto_center
        self.view_all = view_all
        self.orthographic = orthographic
        self.animate = animate
        self.animate_duration = animate_duration
        self.render_mode = render_mode
        self.csg_limit = csg_limit
        self.deps_file = deps_file
        self.make_file = make_file
        self.set_vars = set_vars
        self.customizer_file = customizer_file
        self.customizer_params = customizer_params
        self.hard_warnings = hard_warnings
        self.quiet = quiet
        self.verbose = verbose

        self.cmdline = []
        self.script = []
        self.return_code = None
        self.stderr = []
        self.stdout = []
        self.echos = []
        self.warnings = []
        self.errors = []
        self.success = False
        self.complete = False

    def __bool__(self):
        """
        Returns True if the run() method has been called, and the processing is complete, whether or not it was successful.
        """
        return self.complete

    def good(self):
        """
        Returns True if the run() method has been called, and the result was successful.
        """
        return self.success

    def run(self):
        """
        Runs the OpenSCAD application with the current paramaters.
        """
        outfile = self.outfile
        basename, fileext = os.path.splitext(outfile)
        fileext = fileext.lower()
        if self.animate is not None:
            assert (fileext == ".gif"), "Can only animate to a gif file."
            basename = basename.replace(".", "_")
            outfile = basename + ".png"
        if self.render_mode == RenderMode.test_only:
            scadcmd = [self.OPENSCAD, "-o", "foo.term"]
        else:
            scadcmd = [self.OPENSCAD, "-o", outfile]
            if fileext in [".png", ".gif"]:
                scadcmd.append("--imgsize={},{}".format(int(self.imgsize[0]*self.antialias), int(self.imgsize[1]*self.antialias)))
            if self.show_axes or self.show_scales or self.show_edges or self.show_crosshairs or self.render_mode==RenderMode.wireframe:
                showparts = []
                if self.show_axes:
                    showparts.append("axes")
                if self.show_scales:
                    showparts.append("scales")
                if self.show_edges:
                    showparts.append("edges")
                if self.show_crosshairs:
                    showparts.append("crosshairs")
                if self.render_mode == RenderMode.wireframe:
                    showparts.append("wireframe")
                scadcmd.append("--view=" + ",".join(showparts))
            if self.camera is not None:
                while len(self.camera) < 6:
                    self.camera.append(0)
                scadcmd.extend(["--camera", ",".join(str(x) for x in self.camera)])
            if self.color_scheme != ColorScheme.cornfield:
                scadcmd.extend(["--colorscheme", self.color_scheme])
            scadcmd.append("--projection=o" if self.orthographic else "--projection=p")
            if self.auto_center:
                scadcmd.append("--autocenter")
            if self.view_all:
                scadcmd.append("--viewall")
            if self.animate is not None:
                scadcmd.extend(["--animate", "{}".format(self.animate)])
            if self.render_mode == RenderMode.render:
                scadcmd.extend(["--render", ""])
            elif self.render_mode == RenderMode.preview:
                scadcmd.extend(["--preview", ""])
            elif self.render_mode == RenderMode.thrown_together:
                scadcmd.extend(["--preview", "throwntogether"])
            elif self.render_mode == RenderMode.wireframe:
                scadcmd.extend(["--render", ""])
            if self.csg_limit is not None:
                scadcmd.extend(["--csglimit", self.csg_limit])
        if self.deps_file != None:
            scadcmd.extend(["-d", self.deps_file])
        if self.make_file != None:
            scadcmd.extend(["-m", self.make_file])
        for var, val in self.set_vars.items():
            scadcmd.extend(["-D", "{}={}".format(var,val)])
        if self.customizer_file is not None:
            scadcmd.extend(["-p", self.customizer_file])
        for var, val in self.customizer_params.items():
            scadcmd.extend(["-P", "{}={}".format(var,val)])
        if self.hard_warnings:
            scadcmd.append("--hardwarnings")
        if self.quiet:
            scadcmd.append("--quiet")
        scadcmd.append(self.scriptfile)
        if self.verbose:
            line = " ".join([
                "'{}'".format(arg) if ' ' in arg or arg=='' else arg
                for arg in scadcmd
            ])
            print(line)
        p = subprocess.Popen(scadcmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        (stdoutdata, stderrdata) = p.communicate(None)
        stdoutdata = stdoutdata.decode('utf-8')
        stderrdata = stderrdata.decode('utf-8')
        self.return_code = p.returncode
        self.cmdline = scadcmd
        self.stderr = stderrdata.split("\n")
        self.stdout = stdoutdata.split("\n")
        self.echos    = [x for x in self.stderr if x.startswith("ECHO:")]
        self.warnings = [x for x in self.stderr if x.startswith("WARNING:")]
        self.errors   = [x for x in self.stderr if x.startswith("ERROR:") or x.startswith("TRACE:")]
        if self.return_code==0 and self.errors==[] and (not self.hard_warnings or self.warnings==[]):
            self.success = True
        if self.render_mode==RenderMode.test_only and os.path.isfile("foo.term"):
            os.unlink("foo.term")
        with open(self.scriptfile, "r") as f:
            self.script = f.readlines();
        if self.success and self.render_mode != RenderMode.test_only:
            if self.animate:
                imgs = []
                imgfiles = ["{}{:05d}.png".format(basename,i) for i in range(self.animate)]
                for imgfile in imgfiles:
                    img = Image.open(imgfile)
                    if self.antialias != 1.0:
                        img.thumbnail(self.imgsize, Image.ANTIALIAS)
                    imgs.append(img)
                for imgfile in imgfiles:
                    os.unlink(imgfile)
                imgs[0].save(
                    self.outfile,
                    save_all=True,
                    append_images=imgs[1:],
                    duration=self.animate_duration,
                    loop=0
                )
                pygifsicle.optimize(self.outfile, colors=64)
            elif float(self.antialias) != 1.0:
                im = Image.open(self.outfile)
                im.thumbnail(self.imgsize, Image.ANTIALIAS)
                os.unlink(self.outfile)
                im.save(self.outfile)
        self.complete = True
        return self.success


# vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
