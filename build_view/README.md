# build_view

A small Python program, [`build_view.py`](build_view.py), that generates VFX-family views for use with MAME's emulation of those keyboards.

It can generate either JavaScript code for inclusion with the enclosing `MameVfxRemoteView` web front-end, or [MAME Layout files](https://docs.mamedev.org/techspecs/layout_files.html) for inclusion within MAME itself.

In fact it was used to generate [`vfx.lay`](https://github.com/cbrunschen/mame/blob/vfx_panel/src/mame/layout/vfx.lay), [`vfxsd.lay`](https://github.com/cbrunschen/mame/blob/vfx_panel/src/mame/layout/vfxsd.lay) and [`sd1.lay`](https://github.com/cbrunschen/mame/blob/vfx_panel/src/mame/layout/sd1.lay) that are part of [#14131](https://github.com/mamedev/mame/pull/14131).

It uses the Visitor pattern to generate different outputs from a single panel description.

The code is organized as follows:

## Main bits

### [`build_view.py`](build_view.py)

Main function with argument processing, creates the panel data structure and passes it to the selected visitor.

### [`panel.py`](panel.py)

Describes the layout of the panel, including the conditions for the panel variant (sequencer or not, VFX or SD-1 coloring). Also defines the Visitor interface.

## Visitors

### [`js_html.py`](js_html.py)

The visitor that generates the JavaScript code for use in the enclosing the MameVfxRemoteView web front-end.

A single file is generated that conditionally shows the correct panel, depending on which keyboard is in use.

#### [`View.js`](View.js)

The JavaScript framework into which the specific panel layout code is inserted to generate the full JavaScript code.

### [`mame_layout.py`](mame_layout.py)

The visitor that generates the MAME layout files.

A different layout file is generated for each panel variant, as specified when generating the file.

#### [`mame_layout_script.lua`](mame_layout_script.lua)

The LUA code that is included with the generates MAME Layout files to enable the sliders to work.

## Supporting code

### [`xml.py`](xml.py)

XML helper classes used to generate the MAME Layout files.

### [`rect.py`](rect.py)

Rectangles, boolean operations, conversion to different formats.

### [`util.py`](util.py)

Other utility code, such as RGB conversion from hex values to individual floating-point components, removal of `None`-valued entries from dictionaries, printing to STDERR, etc.