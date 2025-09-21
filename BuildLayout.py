#!/usr/bin/env python3

from textwrap import indent, dedent, wrap
from dataclasses import dataclass, field
import re
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

slider_library = r'''
-----------------------------------------------------------------------
-- Simplified Slider library starts.
-- Can be copied as-is to other layouts.
-- It is simplified from its source:
-- * This one never reads from the port, only writes to it.
-- * Only when clickling on the knob itself does it start to drag the knob.
-- * The value is calculated based on the position of the knob within the click area.
-----------------------------------------------------------------------
local sliders = {}   -- Stores slider information.
local pointers = {}  -- Tracks pointer state.

function clamp(x)
  if x < 0 then return 0 elseif x > 100 then return 100 else return x end
end

-- The knob's Y position must be animated using <animate inputtag="{port_name}">.
-- The click area's vertical size must exactly span the range of the
-- knob's movement.
function add_vertical_slider(view, clickarea_id, knob_id, port_name)
  local slider = {}

  slider.clickarea = view.items[clickarea_id]
  if slider.clickarea == nil then
    emu.print_error("Slider element: '" .. clickarea_id .. "' not found.")
    return
  end

  slider.knob = view.items[knob_id]
  if slider.knob == nil then
    emu.print_error("Slider knob element: '" .. knob_id .. "' not found.")
    return
  end

  local port = file.device:ioport(port_name)
  if port == nil then
    emu.print_error("Port: '" .. port_name .. "' not found.")
    return
  end

  slider.field = nil
  for k, val in pairs(port.fields) do
    slider.field = val
    break
  end
  if slider.field == nil then
    emu.print_error("Port: '" .. port_name .."' does not seem to be an IPT_ADJUSTER.")
    return
  end

  table.insert(sliders, slider)
end

local function pointer_updated(type, id, dev, x, y, btn, dn, up, cnt)
  -- If a button is not pressed, reset the state of the current pointer.
  if btn & 1 == 0 then
    pointers[id] = nil
    return
  end

  -- If a button was just pressed, find the affected slider, if any.
  if dn & 1 ~= 0 then
    for i = 1, #sliders do
      if sliders[i].knob.bounds:includes(x, y) then
        pointers[id] = {
          selected_slider = i,
          dy = y - sliders[i].knob.bounds.y0 -- position within the knob where it was clicked
        }
        break
      end
    end
  end

  -- If there is no slider selected by the current pointer, we are done.
  if pointers[id] == nil then
    return
  end

  -- A slider is selected. Update state and, indirectly, slider knob position,
  -- based on the pointer's Y position. It is assumed the attached IO field is
  -- an IPT_ADJUSTER with a range of 0-100 (the default).

  local pointer = pointers[id]
  local slider = sliders[pointer.selected_slider]
  local knob = slider.knob
  local clickarea = slider.clickarea

  local new_value = 0
  -- User clicked on the knob. The new value will depend on how much the
  -- knob was dragged.
  local yy = y - pointer.dy
  new_value = 100 * (1 - (yy - clickarea.bounds.y0) / (clickarea.bounds.height - knob.bounds.height))
  new_value = math.floor(new_value + 0.5)
  clamped_value = clamp(new_value)
  slider.field.user_value = clamped_value
end

local function pointer_left(type, id, dev, x, y, up, cnt)
  pointers[id] = nil
end

local function pointer_aborted(type, id, dev, x, y, up, cnt)
  pointers[id] = nil
end

local function forget_pointers()
  pointers = {}
end

function install_slider_callbacks(view)
  view:set_pointer_updated_callback(pointer_updated)
  view:set_pointer_left_callback(pointer_left)
  view:set_pointer_aborted_callback(pointer_aborted)
  view:set_forget_pointers_callback(forget_pointers)
end
-----------------------------------------------------------------------
-- Slider library ends.
-----------------------------------------------------------------------
'''

script_main = '''\
-- file is the layout file object
-- set a function to call after resolving tags
file:set_resolve_tags_callback(
  function ()
    -- file.device is the device that caused the layout to be loaded
    -- in this case, it's the esqpanel2x40_vfx object.

    for view_name, view in pairs(file.views) do
      install_slider_callbacks(view)

      add_vertical_slider(view, "slider_volume", "slider_knob_volume", "analog_volume")
      add_vertical_slider(view, "slider_data_entry", "slider_knob_data_entry", "analog_data_entry")

      -- TODO: Display a warning about how to enable sliders
      -- view.items["warning"]:set_state(0)
    end
  end
)
'''

def to_id(s):
  """Merge multiple lines (trimming hyphenation),
     then replace non-identifier characters with '_',
     finally case-fold."""
  return re.sub(r'[^a-zA-Z0-9]+', '_', s.replace('-\n','')).casefold()

@dataclass
class Document:
  root: 'Element'

  def __str__(self):
    return f'<?xml version="1.0"?>\n{self.root}'

@dataclass
class Element:
  tag: str
  attrs: dict[str, str] = field(default_factory=dict)
  children: list[any] = field(default_factory=list)

  def append(self, i):
    if (i == self):
      raise Exception(f"{self.tag}: Appending self")
    self.children.append(i)
  
  def extend(self, l):
    for i in l:
      self.append(i)

  def __str__(self):
    items = [ f'<{self.tag}' ]
    if self.attrs is not None:
      items.extend([f' {k}="{v}"' for (k,v) in self.attrs.items() if v is not None])

    if self.children is not None and len(self.children) > 0:
      items.append('>\n')
      items.extend([indent(str(child), '  ') for child in self.children])
      items.append(f'</{self.tag}>\n')

    else:
      items.append(' />\n')
    
    return ''.join(items)

@dataclass
class CDATA:
  contents: str

  def __str__(self):
    parts = self.contents.split(']]>')
    escaped = ']]>]]><[CDATA['.join(parts)
    return f'<![CDATA[\n{indent(escaped, '  ')}\n]]>'

@dataclass
class Space:
  n: int = 1

  def __str__(self):
    return '\n'.join(['' for i in range(self.n + 1)])


@dataclass
class Comment:
  contents: str

  def __str__(self):
    return f'<!-- {self.contents.replace("--", "==")} -->\n'

def clean(d: dict[str, str]) -> dict[str, str]:
  return { k : v for (k, v) in d.items() if v != None }

class Rect:
  def __init__(self, x, y, w, h):
    self.x = x
    self.y = y
    self.w = w
    self.h = h

  def __str__(self):
    return f"Rect({self.x}, {self.y}, {self.w}, {self.h})"
  
  def union(self, other):
    if (self.w == 0 or self.h == 0):
      return other
    elif (other.w == 0 or other.h == 0):
      return self
    else:
      minX = min(self.x, other.x)
      maxX = max(self.x+self.w, other.x+other.w)
      minY = min(self.y, other.y)
      maxY = max(self.y+self.h, other.y+other.h)
      return Rect(minX, minY, maxX-minX, maxY-minY)
    
  def inset(self, dx, dy):
    return Rect(self.x + dx, self.y + dy, self.w - 2*dx, self.h - 2*dy)
  
  def outset(self, dx, dy):
    return Rect(self.x - dx, self.y - dy, self.w + 2*dx, self.h + 2*dy)
  
  def offset(self, dx, dy):
    return Rect(self.x+dx, self.y+dy, self.w, self.h)
  
  def toPath(self, r=None, fill=None, stroke=None):
    rx = f"{r:.3g}" if r != None else None
    return Element('rect', clean({
      'x': f"{self.x:.3g}", 
      'y': f"{self.y:.3g}", 
      'width': f"{self.w:.3g}", 
      'height': f"{self.h:.3g}",
      'rx': rx,
      'fill': fill,
      'stroke': stroke,
    }), [])
  
  def toElement(self, color=None):
    return Element('rect', clean({
      'x': f"{self.x:.3g}", 
      'y': f"{self.y:.3g}", 
      'width': f"{self.w:.3g}", 
      'height': f"{self.h:.3g}",
    }), [

    ])

  
  def getX(self, d):
    return self.x + d * self.w

  def getY(self, d):
    return self.y + d * self.h
  
  def viewBox(self):
    return f"{self.x} {self.y} {self.w} {self.h}"
  
  def toBounds(self, state=None):
    return Element('bounds', clean({
      'x': f"{self.x:.5g}", 
      'y': f"{self.y:.5g}", 
      'width': f"{self.w:.5g}", 
      'height':f"{self.h:.5g}",
      'state':state,
      }), [])

  def fitWithin(self, enclosing):
    xscale = enclosing.w / self.w
    yscale = enclosing.h / self.h
    scale = min(xscale, yscale)

    dx = (enclosing.w - (self.w * scale)) / 2
    dy = (enclosing.h - (self.h * scale)) / 2

    return Rect(enclosing.x + dx, enclosing.y + dy, self.w * scale, self.h * scale)
  
class Slider:
  def __init__(self, x, y, w, h, channel, value):
    self.channel = channel
    self.value = value

    self.rect = Rect(x, y, w, h)
    rect = self.rect.offset(-x, -y)
    translation = "translate(" + x + "," + y + ")"
    self.group = my.createElement("g")
    self.group.setAttribute("transform", translation)

    self.frameColor = "#333333"
    self.frameActiveColor = "#666666"
    self.frame = rect.inset(0.25, 0.25).toPath()
    self.frame.setAttribute("stroke", self.frameColor)
    self.frame.setAttribute("stroke-width", "0.5")
    self.group.appendChild(self.frame)

    self.handleX = 0.75
    self.handleW = w - 1.5
    self.handleH = 4
    self.handleMinY = 0.75
    self.handleMaxY = h - 0.75 - self.handleH

    # self.handle = my.createElement("g")
    # self.handle.appendChild(makeRectPath(0, 0, self.handleW, self.handleH, "#333333"))
    # self.handle.appendChild(makeRectPath(0, 0, self.handleW, 0.75, "#444444"))
    # self.handle.appendChild(makeRectPath(0, 1.75, self.handleW, 0.25, "#222222"))
    # self.handle.appendChild(makeRectPath(0, 2, self.handleW, 0.25, "#444444"))
    # self.handle.appendChild(makeRectPath(0, 3.25, self.handleW, 0.75, "#222222"))
    # self.group.appendChild(self.handle)

ABOVE = 1
CENTERED = 2
BELOW = CENTERED
ABOVE_CENTERED = ABOVE + CENTERED

SHADE_LIGHT = ('light', "#bbbbbb", "#ffffff")
SHADE_MEDIUM = ('medium', "#777777", "#ffffff")
SHADE_DARK = ('dark', "#333333", '#ffffff')

buttonLabelFontSize = 1.8

roughDisplayRect = Rect(15, 6.5, 82, 12)
charRect = Rect(0, 0, 342, 572)
charsRect = Rect(0, 0, 40 * charRect.w, 2 * charRect.h)
displayRect = charsRect.fitWithin(roughDisplayRect)

displayGlassRect = Rect(10, -2, 92, 27)

def rgb_components(rgb):
  return [int(c, 16) / 255.0 for c in wrap(rgb.removeprefix('#'), 2)]

class Panel:
  def __init__(self, keyboard):
    self.keyboard = keyboard
    self.has_sequencer = keyboard.find('sd') >= 0
    self.is_sd1 = keyboard.find('sd1') >= 0

    self.color_vfx = "#299ca3"
    self.color_sd1 = "#db5f6a"

    self.color = self.color_sd1 if self.is_sd1 else self.color_vfx

    self.rect = displayGlassRect

    self.button_shapes = {}
    self.text_definitions = {}
    self.light_definitions = []

    knobTop    = Rect(0, 0,    6.5, 4).offset(0.75, 0.75)
    knobBottom = Rect(0, 18.5, 6.5, 4).offset(0.75, 0.75)

    self.slider_definitions = [
      self.layout_element(name="invisible_rect", contents=[
        self.layout_rect(color="#00000000"),
      ]),
      self.layout_element(name='slider_frame', contents=[
        self.layout_rect(color="#333333", bounds=Rect(0, 0, 8, 24)),
        self.layout_rect(color="#000000", bounds=Rect(0.5, 0.5, 7, 23))
      ]),
      self.layout_element(name="slider_knob", contents=[
        self.layout_rect(color="#333333", bounds=knobTop),
        self.layout_rect(color="#444444", bounds=Rect(0, 0,    6.5, 0.75).offset(0.75, 0.75)),
        self.layout_rect(color="#222222", bounds=Rect(0, 1.75, 6.5, 0.25).offset(0.75, 0.75)),
        self.layout_rect(color="#444444", bounds=Rect(0, 2,    6.5, 0.25).offset(0.75, 0.75)),
        self.layout_rect(color="#222222", bounds=Rect(0, 3.25, 6.5, 0.75).offset(0.75, 0.75)),
      ]),
      self.layout_group(name="slider", contents=[
        self.layout_element(ref="slider_frame", bounds=Rect(0, 0, 8, 24)),
        self.layout_element(id="slider_~slider_id~", ref="invisible_rect", bounds=Rect(0.75, 0.75, 6.5, 18.5)),
        self.layout_element(ref="slider_knob", id="slider_knob_~slider_id~", contents=[
          self.layout_tag('animate', inputtag="~port_name~", inputmask="0x7f"),
          self.layout_bounds(knobTop, state="100"),
          self.layout_bounds(knobBottom, state="0"),
        ]),
      ]),
    ]

    self.vfd_definitions = [
      dedent('''\
  <!-- The VFD elements -->
  <element name="segments" defstate="0">
    <led14seg>
      <color red="0.45" green="1.0" blue="0.95" />
    </led14seg>
  </element>

  <element name="dot" defstate="0">
    <disk statemask="0x4000" state="0"><color red="0.06" green="0.12" blue="0.10" /></disk>
    <disk statemask="0x4000" state="0x4000"><color red="0.45" green="1.00" blue="0.95" /></disk>
  </element>

  <element name="underline" defstate="0">
    <rect statemask="0x8000" state="0"><color red="0.06" green="0.12" blue="0.10" /></rect>
    <rect statemask="0x8000" state="0x8000"><color red="0.45" green="1.00" blue="0.95" /></rect>
  </element>

  <group name="vfd_cell">
    <bounds x="0" y="0" width="342" height="572" />
    <element ref="segments" name="~input~"><bounds x="50" y="69" width="214" height="311" /></element>
    <element ref="dot" name="~input~"><bounds x="253" y="337" width="42" height="42" /></element>
    <element ref="underline" name="~input~"><bounds x="43" y="441" width="183" height="25" /></element>
  </group>

  <element name="vfd_background">
    <rect>
      <color red="0.0" green="0.0" blue="0.0" />
    </rect>
  </element>

  <group name="vfd">
    <element ref="vfd_background">
      <bounds x="0" y="0" width="13680" height="1144" />
    </element>

    <!-- VFDs -->
    <repeat count="2">
      <param name="s" start="0" increment="40" />
      <param name="y" start="0" increment="572" />
      <repeat count="40">
        <param name="n" start="~s~" increment="1" />
        <param name="x" start="0" increment="342" />

        <param name="input" value="vfd~n~" />
        <group ref="vfd_cell">
          <bounds x="~x~" y="~y~" width="342" height="572" />
        </group>

      </repeat>
    </repeat>
  </group>
''')
    ]

    self.decoration_definitions = [
      Element('element', {
        'name': 'background'
      }, [
        Element('rect', {}, [
          self.layout_color("#222222")
        ])
      ]),

      self.layout_element(name='display_glass', contents=[
        self.layout_rect(color="#000000", bounds=displayGlassRect)
      ]),

      self.layout_element(name='up_triangle', contents=[
        self.layout_svg_image(svg=dedent('''\
          <svg width="2" height="1" viewBox="0 0 2 1">
          <path stroke="none" fill="#ffffff" d="M0 1H2L 1 0Z" />
          </svg>
          '''))
      ]),
      
      self.layout_element(name='down_triangle', contents=[
        self.layout_svg_image(svg=dedent('''\
          <svg width="2" height="1" viewBox="0 0 2 1">
          <path stroke="none" fill="#ffffff" d="M0 0H2L1 1Z" />
          </svg>
          '''))
      ]),

      self.layout_element(name='white_rect', contents=[
        self.layout_rect(bounds=Rect(0, 0, 1, 1), color='#ffffff')
      ]),

      self.layout_element(name='accent_rect', contents=[
        self.layout_rect(bounds=Rect(0, 0, 1, 1), color=self.color)
      ])
    ]

    self.button_uses = []
    self.text_uses = []
    self.light_uses = []
    self.slider_uses = []
    self.decoration_uses = [
      self.layout_element(ref='display_glass', bounds=displayGlassRect),
    ]
    self.vfd_uses = [
      dedent(f'''\
      <group ref="vfd">
        {displayRect.toBounds()}
      </group>
      ''')
    ]

    self.show_if = []

    self.view = []
  
  def layout_bounds(self, bounds, state=None):
    return bounds.toBounds(state)

  def layout_color(self, rgb):
    comps = rgb_components(rgb)
    return Element('color', {
      'red': f"{comps[0]:.3g}", 
      'green': f"{comps[1]:.3g}", 
      'blue': f"{comps[2]:.3g}"},
      []
    )
  
  def layout_tag(self, tag, contents=None, bounds=None, color=None, name=None, ref=None, id=None, **kwargs):
    e = Element(tag, clean({
      **kwargs,
      'name': name,
      'ref': ref,
      'id': id,
    }), [])

    if (bounds != None):
      e.append(self.layout_bounds(bounds))

    if (color != None):
      e.append(self.layout_color(color))

    if (contents != None):
      if isinstance(contents, list):
        for i in contents:
          e.append(i)
      else:
        e.append(contents)    
    return e


  def layout_element(self, **kwargs):
    return self.layout_tag('element', **kwargs)

  def layout_group(self, **kwargs):
    return self.layout_tag('group', **kwargs)

  def layout_rect(self, name=None, ref=None, color=None, state=None, statemask=None, bounds=None):
    e = Element('rect', clean({
      'name': name,
      'ref': ref,
      'state': state,
      'statemask': statemask
    }), [])
    if (color != None):
      e.append(self.layout_color(color))
    if bounds != None:
      e.append(self.layout_bounds(bounds))
    return e
  
  def layout_svg_image(self, svg, name=None, color=None, state=None, statemask=None):
    e = Element('image', clean({
      'name': name,
      'state': state,
      'statemask': statemask
    }), [])
    if color != None:
      e.append(self.layout_color(color))
    data = Element('data');
    data.append(CDATA(svg))
    e.append(data)
    return e

  def layout_text(self, s, name=None, color=None, align=None, attr={}):
    e = Element('text', clean({
      **attr,
      'string': s,
      'name': name,
      'align': align
    }), [])
    if color != None:
      e.append(self.layoutColor(color))
    return e

  def addLabel(self, x, y, w, fontSize, label, centered = False):      
    bounds = Rect(x, y, w, fontSize)
    self.rect = self.rect.union(bounds)

    align = "0" if centered else "1"
    alignment = "C" if centered else "L"

    id = f'{to_id(label)}_{alignment}'

    defattr = {}
    useattr = {}

    if id not in self.text_definitions:
      self.text_definitions[id] = self.layout_element(
        contents=self.layout_text(
          label,
          align=align,
          attr=defattr
        ), 
        name=f'text_{id}')
    
    self.text_uses.append(
      self.layout_element(
        ref=f'text_{id}',
        bounds=bounds,
        **useattr
        ))

  def addButton(self, x, y, w, h, label, labelPosition, value, shade, multiPage = False, lightId = None):
    bounds = Rect(x, y, w, h)
    self.rect = self.rect.union(bounds)

    # Ensure that there's a reusable button shape
    (shade_name, rgb_default, rgb_pressed) = shade
    shape_name = f'button_{w}_{h}_{shade_name}'

    if shape_name not in self.button_shapes:
      rect = Rect(0, 0, w, h).inset(0.1, 0.1)
      svg = f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{str(rect.toPath(r=0.5, fill="white")).rstrip()}</svg>'
      definition = self.layout_element(contents=[
        self.layout_svg_image(svg, state="0", color=rgb_default),
        self.layout_svg_image(svg, state="1", color=rgb_pressed)
      ], name=shape_name)
      self.button_shapes[shape_name] = definition
    
    inputtag = "buttons_0" if value < 32 else "buttons_32"
    mask = 1 << (value % 32)
    inputmask = f'0x{mask:08x}'

    button_id = f'button_{value}_{to_id(label)}'

    self.button_uses.append(
      self.layout_element(
        ref=shape_name,
        id=button_id,
        bounds=bounds,
        inputtag=inputtag, inputmask=inputmask,
      )
    )

    if not label.startswith("#"):
      labelLines = label.split("\n")
      nLines = len(labelLines)
      y0 = h if labelPosition == BELOW else -nLines * buttonLabelFontSize
      centered = ((labelPosition & CENTERED) != 0)
      
      for i in range(nLines):
        line = labelLines[i]
        self.addLabel(x, y + y0 + i * buttonLabelFontSize, w, buttonLabelFontSize, line, centered)

    if lightId >= 0:
      mask = 1 << lightId
      maskval = f'0x{mask:04x}'

      self.light_definitions.append(self.layout_element(contents=[
        self.layout_rect(state="0", statemask=maskval, color="#112211"),
        self.layout_rect(state=maskval, statemask=maskval, color="#22ff22"),
      ],name=f"light_{lightId}",))

      self.light_uses.extend([
        self.layout_element(ref=f'light_{lightId}', name='lights', bounds=Rect(x + w/3, y + h/25, w/h, h/3))
      ])

  def addSlider(self, x, y, name):
    bounds = Rect(x, y, 8, 24)  # always 8 wide, 24 tall
    self.rect = self.rect.union(bounds)

    self.slider_uses.extend([
      Element('param', {'name':'slider_id', 'value':f"{name}"}, []),
      Element('param', {'name':'port_name', 'value':f"analog_{name}"}, []),
      self.layout_group(ref="slider", bounds=bounds)
    ])

  def addButtonBelowDisplay(self, x, y, label, value, shade):
    self.addButton(x, y, 6, 4, label, BELOW, value, shade, False, -1)
  
  def addButtonWithLightBelowDisplay(self, x, y, label, value, shade, lightId):
    self.addButton(x, y, 6, 4, label, BELOW, value, shade, False, lightId)
  
  def addLargeButton(self, x, y, label, value, shade, multiPage=False):
    self.addButton(x, y, 6, 4, label, ABOVE, value, shade, False, -1)
  
  def addLargeButtonWithLight(self, x, y, label, value, shade, lightId, centered=False):
    self.addButton(x, y, 6, 4, label, ABOVE_CENTERED if centered else ABOVE, value, shade, False, lightId)

  def addSmallButton(self, x, y, label, value, shade, multiPage):
    self.addButton(x, y, 6, 2, label, ABOVE, value, shade, multiPage, -1)
  
  def addIncDecButton(self, x, y, label, value, shade, multiPage):
    self.addButton(x, y, 6, 2, label, ABOVE_CENTERED, value, shade, multiPage, -1)
  
  def addColoredLine(self, x, y, w, h):
    bounds = Rect(x, y, w, h)
    self.decoration_uses.append(self.layout_element(ref="colored_rect", bounds=bounds))
    self.rect = self.rect.union(bounds)

  def addWhiteLine(self, x, y, w, h):
    bounds = Rect(x, y, w, h)
    self.decoration_uses.append(self.layout_element(ref="white_rect", bounds=bounds))
    self.rect = self.rect.union(bounds)
    
  def addControls(self):
    # Normalize the keyboard string.

    self.addButtonWithLightBelowDisplay(10, 29, "#CartBankSet", 52, SHADE_LIGHT, 0xf)
    if self.is_sd1:
      color = self.color_sd1
      self.addLabel(10, 35, 6, buttonLabelFontSize, "BankSet", centered=True)
    else:
      color = self.color_vfx
      self.addLabel(10, 35, 6, buttonLabelFontSize, "Cart", centered=True)

    self.addButtonWithLightBelowDisplay(16, 29, "#Sounds",   53, SHADE_LIGHT, 0xd)
    self.addLabel(16, 35, 6, buttonLabelFontSize, "Sounds", centered=True)

    self.addButtonWithLightBelowDisplay(22, 29, "#Presets",  54, SHADE_LIGHT, 0x7)
    self.addLabel(22, 35, 6, buttonLabelFontSize, "Presets", centered=True)

    if self.has_sequencer:
      self.addButtonBelowDisplay     (28, 29, "#Seq",      51, SHADE_LIGHT)
      self.addLabel(28, 35, 6, buttonLabelFontSize, "Seq", centered=True)

    self.addButtonWithLightBelowDisplay(42, 29, "#0", 55, SHADE_MEDIUM, 0xe)
    self.addButtonWithLightBelowDisplay(48, 29, "#1", 56, SHADE_MEDIUM, 0x6)
    self.addButtonWithLightBelowDisplay(54, 29, "#2", 57, SHADE_MEDIUM, 0x4)
    self.addButtonWithLightBelowDisplay(60, 29, "#3", 46, SHADE_MEDIUM, 0xc)
    self.addButtonWithLightBelowDisplay(66, 29, "#4", 47, SHADE_MEDIUM, 0x3)
    self.addButtonWithLightBelowDisplay(72, 29, "#5", 48, SHADE_MEDIUM, 0xb)
    self.addButtonWithLightBelowDisplay(78, 29, "#6", 49, SHADE_MEDIUM, 0x2)
    self.addButtonWithLightBelowDisplay(84, 29, "#7", 35, SHADE_MEDIUM, 0xa)
    self.addButtonWithLightBelowDisplay(90, 29, "#8", 34, SHADE_MEDIUM, 0x1)
    self.addButtonWithLightBelowDisplay(96, 29, "#9", 25, SHADE_MEDIUM, 0x9)

    self.addLabel(42, 35, 6, buttonLabelFontSize, "0", centered=True)
    self.addLabel(48, 35, 6, buttonLabelFontSize, "1", centered=True)
    self.addLabel(54, 35, 6, buttonLabelFontSize, "2", centered=True)
    self.addLabel(60, 35, 6, buttonLabelFontSize, "3", centered=True)
    self.addLabel(66, 35, 6, buttonLabelFontSize, "4", centered=True)
    self.addLabel(72, 35, 6, buttonLabelFontSize, "5", centered=True)
    self.addLabel(78, 35, 6, buttonLabelFontSize, "6", centered=True)
    self.addLabel(84, 35, 6, buttonLabelFontSize, "7", centered=True)
    self.addLabel(90, 35, 6, buttonLabelFontSize, "8", centered=True)
    self.addLabel(96, 35, 6, buttonLabelFontSize, "9", centered=True)

    # Large buttons on the main panel part
    self.addLargeButton         (108, 29, "Replace\nProgram", 29, SHADE_MEDIUM)
    if self.has_sequencer:
      self.addWhiteLine(114, 29 - 1.5 * buttonLabelFontSize - 0.05, 3, 0.1)
      self.addLabel(117, 29 - 2 * buttonLabelFontSize, 6, buttonLabelFontSize, "Tracks", centered=True)
      self.addWhiteLine(123, 29 - 1.5 * buttonLabelFontSize - 0.05, 3, 0.1)

      self.addLargeButtonWithLight(114, 29, "1-6",              30, SHADE_MEDIUM, 0x0, centered=True)
      self.addLargeButtonWithLight(120, 29, "7-12",             31, SHADE_MEDIUM, 0x8, centered=True)
    else:
      self.addWhiteLine(114, 29 - 1.5 * buttonLabelFontSize - 0.05, 4, 0.1)
      self.addLabel(118, 29 - 2 * buttonLabelFontSize, 4, buttonLabelFontSize, "Multi", centered=True)
      self.addWhiteLine(122, 29 - 1.5 * buttonLabelFontSize - 0.05, 4, 0.1)
      self.addLargeButtonWithLight(114, 29, "A",              30, SHADE_MEDIUM, 0x0, centered=True)
      self.addLargeButtonWithLight(120, 29, "B",              31, SHADE_MEDIUM, 0x8, centered=True)

    self.addLargeButton         (154, 29, "Select\nVoice", 5, SHADE_MEDIUM)
    self.addLargeButton         (160, 29, "Copy",          9, SHADE_MEDIUM)
    self.addLargeButton         (166, 29, "Write",         3, SHADE_MEDIUM)
    self.addLargeButtonWithLight(172, 29, "Compare",       8, SHADE_MEDIUM, 0x5)

    # Small buttons, main panel
    # -- Performance:
    self.addSmallButton(108, 20, "Patch\nSelect",   26, SHADE_DARK, True)
    self.addSmallButton(114, 20, "MIDI",            27, SHADE_DARK, True)
    self.addSmallButton(120, 20, "Effects",         28, SHADE_DARK, True)

    self.addSmallButton(108, 13, "Key\nZone",       39, SHADE_DARK, False)
    self.addSmallButton(114, 13, "Trans-\npose",    40, SHADE_DARK, False)
    self.addSmallButton(120, 13, "Release",         41, SHADE_DARK, False)

    self.addSmallButton(108,  6, "Volume",          36, SHADE_DARK, False)
    self.addSmallButton(114,  6, "Pan",             37, SHADE_DARK, False)
    self.addSmallButton(120,  6, "Timbre",          38, SHADE_DARK, False)

    # When the keyboard has a sequencer:
    if self.has_sequencer:
      # The 'Master', 'Storage' and 'MIDI Control' buttons are small & at the top,
      # the sequencer buttons are big and at the bottom.
      self.addLargeButton(131, 29, "Rec",           19, SHADE_MEDIUM)
      self.addLargeButton(137, 29, "Stop\n/Cont",   22, SHADE_MEDIUM)
      self.addLargeButton(143, 29, "Play",          23, SHADE_MEDIUM)

      self.addSmallButton(131, 20, "Click",         32, SHADE_DARK, False)
      self.addSmallButton(137, 20, "Seq\nControl",  18, SHADE_DARK, True)
      self.addSmallButton(143, 20, "Locate",        33, SHADE_DARK, True)

      self.addSmallButton(131, 13, "Song",          60, SHADE_DARK, False)
      self.addSmallButton(137, 13, "Seq",           59, SHADE_DARK, False)
      self.addSmallButton(143, 13, "Track",         61, SHADE_DARK, False)

      self.addSmallButton(131,  6, "Master",        20, SHADE_LIGHT, True)
      self.addSmallButton(137,  6, "Storage",       21, SHADE_LIGHT, False)
      self.addSmallButton(143,  6, "MIDI\nControl", 24, SHADE_LIGHT, True)

      self.addWhiteLine(131, 13 - 1.5 * buttonLabelFontSize - 0.05, 7, 0.1)
      self.addLabel(138, 13 - 2 * buttonLabelFontSize, 4, buttonLabelFontSize, "Edit", centered=True)
      self.addWhiteLine(142, 13 - 1.5 * buttonLabelFontSize - 0.05, 7, 0.1)

    else:
      # When there is no Sequencer:
      # The 'Master', 'Storage' and 'MIDI Control' buttons are large & at the bottom,
      # and there are no sequencer buttons
      self.addLargeButton(131, 29, "Master",        20, SHADE_LIGHT, True)
      self.addLargeButton(137, 29, "Storage",       21, SHADE_LIGHT, False)
      self.addLargeButton(143, 29, "MIDI\nControl", 24, SHADE_LIGHT, True)
    
    # -- Programming:
    self.addSmallButton(154, 20, "Wave",             4, SHADE_DARK, False)
    self.addSmallButton(160, 20, "Mod\nMixer",       6, SHADE_DARK, False)
    self.addSmallButton(166, 20, "Program\nControl", 2, SHADE_DARK, False)
    self.addSmallButton(172, 20, "Effects",          7, SHADE_DARK, True)

    self.addSmallButton(154, 13, "Pitch",           11, SHADE_DARK, False)
    self.addSmallButton(160, 13, "Pitch\nMod",      13, SHADE_DARK, False)
    self.addSmallButton(166, 13, "Filters",         15, SHADE_DARK, True)
    self.addSmallButton(172, 13, "Output",          17, SHADE_DARK, True)

    self.addSmallButton(154,  6, "LFO",             10, SHADE_DARK, True)
    self.addSmallButton(160,  6, "Env1",            12, SHADE_DARK, True)
    self.addSmallButton(166,  6, "Env2",            14, SHADE_DARK, True)
    self.addSmallButton(172,  6, "Env3",            16, SHADE_DARK, True)

    # Display buttons - approximate:
    self.addSmallButton(32, 21, "#display_below_left", 50, SHADE_DARK, False)
    self.addSmallButton(57, 21, "#display_below_middle", 44, SHADE_DARK, False)
    self.addSmallButton(82, 21, "#display_below_right", 45, SHADE_DARK, False)

    self.addSmallButton(32,  0, "#display_above_left", 58, SHADE_DARK, False)
    self.addSmallButton(57,  0, "#diplay_above_center", 42, SHADE_DARK, False)
    self.addSmallButton(82,  0, "#display_above_right", 43, SHADE_DARK, False)

    # Value slider
    self.addSlider(-8, 4, "data_entry")

    # Increment and Decrement
    self.addIncDecButton(-17, 22, "#increment", 63, SHADE_DARK, False)
    self.addIncDecButton(-17, 12, "#decrement", 62, SHADE_DARK, False)

    self.decoration_uses.extend([
      self.layout_element(ref="up_triangle", bounds=Rect(-15, 10, 2, 1)),
      self.layout_element(ref="down_triangle", bounds=Rect(-15, 20, 2, 1))
    ])

    # Volume slider
    self.addSlider(-36, 4, "volume")

    # The colored lines along the base:
    self.addColoredLine(-36, 37, 166, 0.5)
    self.addColoredLine(108, 37, 22, 0.5)
    self.addColoredLine(131, 37, 22, 0.5)
    self.addColoredLine(154, 37, 24, 0.5)

    # And the labels just above it:
    self.addLabel(-36, 35, 10, buttonLabelFontSize, "Volume")
    self.addLabel(-17, 35, 10, buttonLabelFontSize, "Data Entry")
    self.addLabel(108, 35, 10, buttonLabelFontSize, "Performance")
    if self.has_sequencer:
      self.addLabel(131, 2-(0.2 + buttonLabelFontSize), 10, buttonLabelFontSize, "System")
      self.addColoredLine(131, 2-0.2, 22, 0.2)
      self.addLabel(131, 35, 10, buttonLabelFontSize, "Sequencer")
    else:
      self.addLabel(131, 35, 10, buttonLabelFontSize, "System")
    self.addLabel(154, 35, 10, buttonLabelFontSize, "Programming")

    # Add just a little space around.
    self.rect = self.rect.outset(2, 2)

    self.decoration_uses.insert(0, # put the background before anything else.
      self.layout_element(ref='background', bounds=self.rect)
    )

  def __str__(self):
    layout = Element('mamelayout', {'version':'2'})
    
    layout.append(Space())
    layout.append(Comment('Decoration definitions'))
    layout.extend(self.decoration_definitions)

    layout.append(Comment('VFD'))
    layout.extend(self.vfd_definitions)

    layout.append(Space())
    layout.append(Comment('Text items'))
    layout.extend([d for (k, d) in self.text_definitions.items()])

    layout.append(Comment('Button shapes'))
    layout.extend([shape for (k, shape) in self.button_shapes.items()])

    layout.append(Space())
    layout.append(Comment('Light items'))
    layout.extend(self.light_definitions)

    layout.append(Space())
    layout.append(Comment('Slider definitions'))
    layout.extend(self.slider_definitions)

    layout.append(Space())
    layout.append(Comment('Panel Group'))

    group = Element('group', {'name':'panel'}, [])
    layout.append(group)

    group.extend(self.decoration_uses)

    group.extend(self.vfd_uses)

    group.extend(self.text_uses)
    group.extend(self.button_uses)
    group.extend(self.light_uses)
    
    group.extend(self.slider_uses)
    
    layout.append(Space())
    layout.append(Comment('Panel View'))
    view = Element('view', {'name':'Panel'}, [
      Element('group', {'ref':'panel'})
    ])
    layout.append(view)

    script = Element('script', {}, [
      CDATA(script_main + slider_library)
    ])
    layout.append(script)

    document = Document(layout)

    return str(document)

def main(argv: list[str]) -> int:
  for i in range(1, len(argv)):
    p = Panel(argv[i])
    p.addControls()
    print(p)
  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv))
