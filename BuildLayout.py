#!/usr/bin/env python3

from textwrap import indent, dedent, wrap
from dataclasses import dataclass, field
import re
import sys

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
    return f'<[CDATA[\n{indent(escaped, '  ')}\n]]>'

@dataclass
class Space:
  n: int = 1

  def __str__(self):
    return '\n'.join(['' for i in range(self.n + 1)])


@dataclass
class Comment:
  contents: str

  def __str__(self):
    return f'<-- {self.contents.replace("--", "==")} -->\n'

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
  
  def toPath(self, r=None):
    rx = f"{r:.3g}" if r != None else None
    return Element('rect', clean({
      'x': f"{self.x:.3g}", 
      'y': f"{self.y:.3g}", 
      'width': f"{self.w:.3g}", 
      'height': f"{self.h:.3g}", 
      'rx': rx
    }), [])

  
  def getX(self, d):
    return self.x + d * self.w

  def getY(self, d):
    return self.y + d * self.h
  
  def viewBox(self):
    return f"{self.x} {self.y} {self.w} {self.h}"
  
  def toBounds(self):
    return Element('bounds', {
      'x': f"{self.x:.3g}", 
      'y': f"{self.y:.3g}", 
      'width': f"{self.w:.3g}", 
      'height':f"{self.h:.3g}"
      }, [])
  
displayRect = Rect(15, 7, 82, 13)

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

fontSize = 1.4


def rgb_components(rgb):
  return [int(c, 16) / 255.0 for c in wrap(rgb.removeprefix('#'), 2)]

@dataclass
class Condition:
  name: str
  mask: int
  state: bool

  def opposite(self):
    return Condition(self.name, self.mask, not self.state)

@dataclass
class ConditionalLabel:
  label: str
  condition: Condition

class Panel:
  def __init__(self):
    self.rect = displayRect

    self.button_shapes = {}
    self.text_definitions = {}
    self.light_definitions = [
      Element('element', {}, [
        Element('rect', {
          'state': '0',
          'statemask': '~lightmask~',
        }, [
          self.layout_color("#112211")
        ]),

        Element('rect', {
          'state': '~lightmask~',
          'statemask': '~lightmask~',
        }, [
          self.layout_color("#22ff22")        
        ]),
      ])
    ]
    self.slider_definitions = []

    self.button_uses = []
    self.text_uses = []
    self.light_uses = []
    self.slider_uses = []

    self.view = []
  
  def layout_bounds(self, bounds):
    return bounds.toBounds()

  def layout_color(self, rgb):
    comps = rgb_components(rgb)
    return Element('color', {
      'red': f"{comps[0]:.3g}", 
      'green': f"{comps[1]:.3g}", 
      'blue': f"{comps[2]:.3g}"},
      []
    )
  
  def layout_tag(self, tag, contents=None, bounds=None, color=None, name=None, ref=None, **kwargs):
    e = Element(tag, clean({
      **kwargs,
      'name': name,
      'ref': ref
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

  def layout_rect(self, name=None, color=None, state=None, statemask=None):
    e = Element('rect', clean({
      'name': name,
      'state': state,
      'statemask': statemask
    }), [])
    if (color != None):
      e.append(self.layout_color(color))
    return e
  
  def layout_svg_image(self, svg, name=None, color=None, state=None, statemask=None):
    e = Element('image', clean({
      'name': name,
      'state': state,
      'statemask': statemask
    }), [])
    if color != None:
      e.append(self.layout_color(color))
    e.append(CDATA(svg))
    return e

  def layout_text(self, s, name=None, color=None, state=None, statemask=None, align=None):
    e = Element('text', clean({
      'string': s,
      'name': name,
      'state': state,
      'statemask': statemask,
      'align': align
    }), [])
    if color != None:
      e.append(self.layoutColor(color))
    return e

  def addButton(self, x, y, w, h, label, labelPosition, value, shade, multiPage = False, lightId = None, condition = None):
    bounds = Rect(x, y, w, h)
    self.rect = self.rect.union(bounds)

    # Ensure that there's a reusable button shape
    (shade_name, rgb_default, rgb_pressed) = shade
    shape_name = f'button_{w}_{h}_{shade_name}'
    if shape_name not in self.button_shapes:
      rect = Rect(0, 0, w, h).inset(0.1, 0.1)
      svg = f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{str(rect.toPath()).rstrip()}</svg>'
      definition = self.layout_element(contents=[
        self.layout_svg_image(svg, state="0", color=rgb_default),
        self.layout_svg_image(svg, state="1", color=rgb_pressed)
      ], name=shape_name)
      self.button_shapes[shape_name] = definition
    
    inputtag = "buttons_0" if value < 32 else "buttons_32"
    mask = 1 << (value % 32)
    inputmask = f'0x{mask:08x}'

    if condition != None:
      self.button_uses.append(
        self.layout_element(
          bounds=bounds,
          inputtag=inputtag, inputmask=inputmask,
          name=condition.name, statemask=condition.mask, state=condition.mask if condition.state else 0
        )
      )
    else:
      self.button_uses.append(
        self.layout_element(
          bounds=bounds,
          inputtag=inputtag, inputmask=inputmask
        )
      )

    def placeLabel(label, condition=None):
      labelLines = label.split("\n")
      nLines = len(labelLines)
      y0 = (1 - nLines) * fontSize
      align = None if ((labelPosition & CENTERED) != 0) else "1"
      if labelPosition == ABOVE:
        y0 = (1 - nLines) * fontSize - 0.3
      if labelPosition == BELOW:
        y0 = h + fontSize - 0.3
      
      for i in range(nLines):
        line = labelLines[i]
        id = re.sub(r'[^a-zA-Z0-9]+', '_', line).casefold()
        if align is not None:
          id = f'{id}__leftaligned'

        textBounds = Rect(x, y + y0 + i * fontSize, w, fontSize)
        if id not in self.text_definitions:
          self.text_definitions[id] = self.layout_element(
            contents=self.layout_text(
              labelLines[i],
              align=align
            ), 
            name=f'text_{id}')
        
        self.text_uses.append(
          self.layout_element(
            ref=f'text_{id}',
            bounds=textBounds,
            name=condition.name if condition else None, 
            statemask=condition.mask if condition else None, 
            state=(condition.mask if condition.state else 0) if condition else None
            ))

    if isinstance(label, list) and len(label) > 0 and isinstance(label[0], ConditionalLabel):
      for cl in label:
        placeLabel(cl.label, cl.condition)
      label = None

    elif label.startswith("#"):
      id = re.sub(r'[^a-zA-Z0-9]+', '_', label.replace('-\n',''))
      label = None

    if label != None:
      placeLabel(label)

    if lightId >= 0:
      self.light_uses.extend([
        Element('param', {'name':'lightmask', 'value':f"{1 << lightId:04x}"}),
        self.layout_element(ref=f'light', bounds=Rect(x + w/3, y + h/25, w/h, h/3))
      ])  

  def addSlider(self, x, y, w, h, channel, value):
    bounds = Rect(x, y, w, h)
    self.rect = self.rect.union(bounds)
    self.slider_uses.extend([
      Element('param', {'name':'slider_id', 'value':f"slider_{channel}"}, []),
      Element('param', {'name':'port_name', 'value':f"analog_{channel}"}, []),
      self.layout_group(ref="slider", bounds=bounds)
    ])

  def addButtonBelowDisplay(self, x, y, label, value, shade, condition=None):
    self.addButton(x, y, 6, 4, label, BELOW, value, shade, False, -1, condition=condition)
  
  def addButtonWithLightBelowDisplay(self, x, y, label, value, shade, lightId, condition=None):
    self.addButton(x, y, 6, 4, label, BELOW, value, shade, False, lightId, condition=condition)
  
  def addLargeButton(self, x, y, label, value, shade, multiPage=False, condition=None):
    self.addButton(x, y, 6, 4, label, ABOVE, value, shade, False, -1, condition=condition)
  
  def addLargeButtonWithLight(self, x, y, label, value, shade, lightId, condition=None):
    self.addButton(x, y, 6, 4, label, ABOVE, value, shade, False, lightId, condition=condition)

  def addSmallButton(self, x, y, label, value, shade, multiPage, condition=None):
    self.addButton(x, y, 6, 2, label, ABOVE, value, shade, multiPage, -1, condition=condition)
  
  def addIncDecButton(self, x, y, label, value, shade, multiPage, condition=None):
    self.addButton(x, y, 6, 2, label, ABOVE_CENTERED, value, shade, multiPage, -1, condition=condition)
  
  def addControls(self):
    # Normalize the keyboard string.

    hasSeq = Condition('variant', "0x01", True)
    noSeq = hasSeq.opposite()

    hasBankSet = Condition('variant', "0x2", True);
    noBankSet = hasBankSet.opposite();

    self.addButtonWithLightBelowDisplay(10, 29, [
      ConditionalLabel("BankSet", hasBankSet),
      ConditionalLabel("Cart", noBankSet),
    ], 52, SHADE_LIGHT, 0xf, condition=hasBankSet)

    self.addButtonWithLightBelowDisplay(16, 29, "Sounds",   53, SHADE_LIGHT, 0xd)
    self.addButtonWithLightBelowDisplay(22, 29, "Presets",  54, SHADE_LIGHT, 0x7)

    self.addButtonBelowDisplay     (28, 29, "Seq",      51, SHADE_LIGHT, condition=hasSeq)

    self.addButtonWithLightBelowDisplay(42, 29, "0", 55, SHADE_MEDIUM, 0xe)
    self.addButtonWithLightBelowDisplay(48, 29, "1", 56, SHADE_MEDIUM, 0x6)
    self.addButtonWithLightBelowDisplay(54, 29, "2", 57, SHADE_MEDIUM, 0x4)
    self.addButtonWithLightBelowDisplay(60, 29, "3", 46, SHADE_MEDIUM, 0xc)
    self.addButtonWithLightBelowDisplay(66, 29, "4", 47, SHADE_MEDIUM, 0x3)
    self.addButtonWithLightBelowDisplay(72, 29, "5", 48, SHADE_MEDIUM, 0xb)
    self.addButtonWithLightBelowDisplay(78, 29, "6", 49, SHADE_MEDIUM, 0x2)
    self.addButtonWithLightBelowDisplay(84, 29, "7", 35, SHADE_MEDIUM, 0xa)
    self.addButtonWithLightBelowDisplay(90, 29, "8", 34, SHADE_MEDIUM, 0x1)
    self.addButtonWithLightBelowDisplay(96, 29, "9", 25, SHADE_MEDIUM, 0x9)

    # Large buttons on the main panel part
    self.addLargeButton         (108, 29, "Replace\nProgram", 29, SHADE_MEDIUM)
    self.addLargeButtonWithLight(114, 29, "1-6",              30, SHADE_MEDIUM, 0x0)
    self.addLargeButtonWithLight(120, 29, "7-12",             31, SHADE_MEDIUM, 0x8)

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
    # The 'Master', 'Storage' and 'MIDI Control' buttons are small & at the top,
    # the sequencer buttons are big and at the bottom.
    self.addLargeButton(131, 29, "Rec",           19, SHADE_MEDIUM, condition=hasSeq)
    self.addLargeButton(137, 29, "Stop\n/Cont",   22, SHADE_MEDIUM, condition=hasSeq)
    self.addLargeButton(143, 29, "Play",          23, SHADE_MEDIUM, condition=hasSeq)

    self.addSmallButton(131, 20, "Click",         32, SHADE_DARK, False, condition=hasSeq)
    self.addSmallButton(137, 20, "Seq\nControl",  18, SHADE_DARK, True, condition=hasSeq)
    self.addSmallButton(143, 20, "Locate",        33, SHADE_DARK, True, condition=hasSeq)

    self.addSmallButton(131, 13, "Song",          60, SHADE_DARK, False, condition=hasSeq)
    self.addSmallButton(137, 13, "Seq",           59, SHADE_DARK, False, condition=hasSeq)
    self.addSmallButton(143, 13, "Track",         61, SHADE_DARK, False, condition=hasSeq)

    self.addSmallButton(131,  6, "Master",        20, SHADE_LIGHT, True, condition=hasSeq)
    self.addSmallButton(137,  6, "Storage",       21, SHADE_LIGHT, False, condition=hasSeq)
    self.addSmallButton(143,  6, "MIDI\nControl", 24, SHADE_LIGHT, True, condition=hasSeq)

    # When there is no Seuencer:
    # The 'Master', 'Storage' and 'MIDI Control' buttons are large & at the bottom,
    # and there are no sequencer buttons
    self.addLargeButton(131, 29, "Master",        20, SHADE_LIGHT, True, condition=noSeq)
    self.addLargeButton(137, 29, "Storage",       21, SHADE_LIGHT, False, condition=noSeq)
    self.addLargeButton(143, 29, "MIDI\nControl", 24, SHADE_LIGHT, True, condition=noSeq)
    

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

    self.addSmallButton(32,  4, "#display_above_left", 58, SHADE_DARK, False)
    self.addSmallButton(57,  4, "#diplay_above_center", 42, SHADE_DARK, False)
    self.addSmallButton(82,  4, "#display_above_right", 43, SHADE_DARK, False)

    # Value slider
    self.addSlider(-2.75, 4, 7, 22, 3, 0.7)

    # Increment and Decrement
    self.addIncDecButton(-12.5, 22, "#increment", 63, SHADE_DARK, False)
    self.addIncDecButton(-12.5, 12, "#decrement", 62, SHADE_DARK, False)

    # Volume slider
    self.addSlider(-30, 4, 7, 22, 5, 1.0)

    self.rect = self.rect.outset(2, 2)

  def __str__(self):
    sections = Element('Foo', {}, [])
    sections.append(Comment('Button shapes'))
    sections.extend([shape for (k, shape) in self.button_shapes.items()])

    sections.append(Space())
    sections.append(Comment('Text items'))
    sections.extend([d for (k, d) in self.text_definitions.items()])

    sections.append(Space())
    sections.append(Comment('Light items'))
    sections.extend(self.light_definitions)

    sections.append(Space())
    sections.append(Comment('Slider definitions'))
    sections.extend(self.slider_definitions)

    sections.append(Space())
    sections.append(Comment('Now use these!'))

    group = Element('group', {'name':"Panel"}, [])
    sections.append(group)
    group.extend(self.button_uses)
    group.extend(self.light_uses)
    group.extend(self.text_uses)
    group.extend(self.slider_uses)

    # return str(sections)
    
    return str(sections)

    # print(f"sections: {sections}")
    # sio = StringIO
    # ElementTree(sections).write(sio, encoding='unicode')
    # return sio.getvalue()

p = Panel()
p.addControls()

print(p)
