OpenSCAD Runner
===============

A Python library to interface with and run the OpenSCAD interpreter.

ColorScheme Enum Class
----------------------
``ColorScheme`` defines the following enums:
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

RenderMode Enum Class
----------------------
``RenderMode`` defines the following enums::
    - test_only
    - render
    - preview
    - thrown_together
    - wireframe

OpenScadRunner Class
---------------------
The ``OpenScadRunner`` class provides the following methods:

- ``__init__()`` The initializer method, which has the following arguments:
    - scriptfile = The name of the script file to process.
    - outfile = The name of the file to output to.
    - imgsize = The size of the imagefile to output to, if outputting to a PNG or GIF.  Default: (640,480)
    - antialias = The antialiasing scaling factor.  If greater than 1.0, images are generated at a larger size, then scaled down to the target size with anti-aliasing.  Default: 1.0  (no anti-aliasing)
    - animate = If given an integer number of frames, creates that many frames of animation, and collates them into an animated GIF or APNG.  Default: None
    - animate_duration = Number of milliseconds per frame for an animated GIF or APNG.  Default: 250
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
- ``good()`` Returns True if the ``run()`` method was called, and processing completed successfully.
- ``__bool__()`` Returns True if the ``run()`` method was called, and processing completed, whether or not it was successful.
- ``run()`` Run the OpenSCAD app with the current settings.  This sets some instance variables:
    - .complete = A boolean value indicating if the processing has completed yet.
    - .success = A boolean value indicating if the processing completed sucessfully.
    - .script = The script that was evaluated, as a list of line strings.
    - .cmdline = The commandline arguments used to launch the OpenSCAD app.
    - .return_code = The return code from OpenSCAD.  Generally 0 if successful.
    - .echos = A list of ECHO: output line strings.
    - .warnings = A list of WARNING: output line strings.
    - .errors = A list of ERROR: or TRACE: output line strings.


Creating an STL file::

    from openscad_runner import OpenScadRunner
    osr = OpenScadRunner("example.scad", "example.stl")
    osr.run()
    for line in osr.echos:
        print(line)
    for line in osr.warnings:
        print(line)
    for line in osr.errors:
        print(line)
    if osr.good():
        print("Successfully created example.stl")

Creating a Preview PNG::

    from openscad_runner import RenderMode, OpenScadRunner
    osr = OpenScadRunner("example.scad", "example.png", render_mode=RenderMode.preview, imgsize=(800,600), antialias=2.0)
    osr.run()
    for line in osr.echos:
        print(line)
    for line in osr.warnings:
        print(line)
    for line in osr.errors:
        print(line)
    if osr.good():
        print("Successfully created example.png")

Creating a Fully Rendered PNG::

    from openscad_runner import RenderMode, OpenScadRunner
    osr = OpenScadRunner("example.scad", "example.png", render_mode=RenderMode.render, imgsize=(800,600), antialias=2.0)
    osr.run()
    for line in osr.echos:
        print(line)
    for line in osr.warnings:
        print(line)
    for line in osr.errors:
        print(line)
    if osr.good():
        print("Successfully created example.png")

Rendering an animated GIF::

    from openscad_runner import OpenScadRunner
    osr = OpenScadRunner("example.scad", "example.gif", imgsize=(320,200), animate=36, animate_duration=200)
    osr.run()
    for line in osr.echos:
        print(line)
    for line in osr.warnings:
        print(line)
    for line in osr.errors:
        print(line)
    if osr.good():
        print("Successfully created example.gif")

Rendering an animated PNG::

    from openscad_runner import OpenScadRunner
    osr = OpenScadRunner("example.scad", "example.png", imgsize=(320,200), animate=36, animate_duration=200)
    osr.run()
    for line in osr.echos:
        print(line)
    for line in osr.warnings:
        print(line)
    for line in osr.errors:
        print(line)
    if osr.good():
        print("Successfully created example.png")


