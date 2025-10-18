#!/usr/bin/env python3

from textwrap import dedent

from rect import *
from view import *
from myxml import *

class MameLayoutVisitor(ViewVisitor):
  def __init__(self, keyboard):
    self.keyboard = keyboard
    self.conditions = {
      'isSd1': keyboard.find("sd1") >= 0,
      'hasSeq': keyboard.find('sd') >= 0,
    }

    self.colored_rects = {}
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
        self.layout_element(id="slider_~slider_id~", ref="invisible_rect", bounds=Rect(0.75, 0.75, 6.5, 22.5)),
        self.layout_element(ref="slider_knob", id="slider_knob_~slider_id~", contents=[
          self.layout_tag('animate', inputtag="~port_name~", inputmask="0x7f"),
          self.layout_bounds(knobTop, state="1023"),
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
      self.layout_element(name='triangle_up', contents=[
        self.layout_svg_image(svg=dedent('''\
          <svg width="2" height="1" viewBox="0 0 2 1">
          <path stroke="none" fill="#ffffff" d="M0 1H2L 1 0Z" />
          </svg>
          '''))
      ]),
      
      self.layout_element(name='triangle_down', contents=[
        self.layout_svg_image(svg=dedent('''\
          <svg width="2" height="1" viewBox="0 0 2 1">
          <path stroke="none" fill="#ffffff" d="M0 0H2L1 1Z" />
          </svg>
          '''))
      ]),

    ]

    self.button_uses = []
    self.text_uses = []
    self.light_uses = []
    self.slider_uses = []
    self.decoration_uses = []
    self.vfd_uses = []

  def layout_bounds(self, bounds, state=None):
    return bounds.toBounds(state)

  def layout_color(self, rgb, **kwargs):
    comps = rgb_components(rgb)
    return Element('color', {
      **kwargs,
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

  def layout_rect(self, name=None, ref=None, color=None, state=None, statemask=None, bounds=None, contents=[]):
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
    e.extend(contents)
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

  def layout_param(self, k, v):
    return Element('param', {'name':k, 'value':v}, [])
  
  def defaultFontSize(self):
    return 4.3
  
  def visitAccentColor(self, accent_color: AccentColor):
    self.accent_color = accent_color.rgb

  def visitConditional(self, conditional: 'Conditional'):
    for i in (conditional.ifTrue if self.conditions[conditional.condition] else conditional.ifFalse):
      i.accept(self)

  def visitDisplay(self, display: 'Display'):
    self.vfd_uses.append(
      dedent(f'''\
        <group ref="vfd">
          {display.bounds.toBounds()}
        </group>
        ''')
    )

  def visitButton(self, button: 'Button'):
    x = button.bounds.x
    y = button.bounds.y
    w = button.bounds.w
    h = button.bounds.h

    # Ensure that there's a reusable button shape
    shade = button.shade
    shape_name = f'button_{w}_{h}_{shade.name}'

    if shape_name not in self.button_shapes:
      rect = Rect(0, 0, w, h).inset(0.25, 0.25)
      svg = f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{str(rect.toPath(r=1.25, fill="white")).rstrip()}</svg>'
      definition = self.layout_element(contents=[
        self.layout_svg_image(svg, state="0", color=shade.color),
        self.layout_svg_image(svg, state="1", color=shade.pressed_color)
      ], name=shape_name)
      self.button_shapes[shape_name] = definition
    
    inputtag = "buttons_0" if button.number < 32 else "buttons_32"
    mask = 1 << (button.number % 32)
    inputmask = f'0x{mask:08x}'

    button_id = f'button_{button.number}_{to_id(button.label)}'

    self.button_uses.append(
      self.layout_element(
        ref=shape_name,
        id=button_id,
        bounds=button.bounds,
        inputtag=inputtag, inputmask=inputmask,
      )
    )

    if button.light:
      light = button.light
      bit = 1 << light.number
      maskval = f'0x{bit:04x}'

      self.light_definitions.append(self.layout_element(contents=[
        self.layout_rect(state="0", statemask=maskval, color="#112211"),
        self.layout_rect(state=maskval, statemask=maskval, color="#22ff22"),
      ],name=f"light_{light.number}",))

      self.light_uses.extend([
        self.layout_element(ref=f'light_{light.number}', name='lights', bounds=light.bounds.offset(x, y))
      ])

  def visitLabel(self, label: 'Label'):
    align = None if label.centered else "1"
    alignment = "" if label.centered else "L_"

    id = f'{alignment}{to_id(label.text)}'

    defattr = {}
    useattr = {}

    if id not in self.text_definitions:
      self.text_definitions[id] = self.layout_element(
        contents=self.layout_text(
          label.text,
          align=align,
          attr=defattr
        ), 
        name=f'text_{id}')
    
    self.text_uses.append(
      self.layout_element(
        ref=f'text_{id}',
        bounds=label.bounds,
        **useattr
        ))

  def visitSlider(self, slider: 'Slider'):
    self.slider_uses.extend([
      self.layout_param('slider_id', slider.name),
      self.layout_param('port_name', f"analog_{slider.name}"),
      self.layout_group(ref="slider", bounds=slider.bounds)
    ])

  def visitRectangle(self, rectangle: 'Rectangle'):
    if rectangle.color == 'accent':
      color = self.accent_color
    else:
      color = rectangle.color
    rect_id = f'rect_{color.removeprefix("#")}'
    if rect_id not in self.colored_rects:
      self.colored_rects[rect_id] = self.layout_element(name=rect_id, contents=[
        self.layout_rect(color=color)
      ])
    self.decoration_uses.append(self.layout_element(ref=rect_id, bounds=rectangle.bounds))
    
  def visitSymbol(self, symbol: 'Symbol'):
    self.decoration_uses.append(
      self.layout_element(ref=symbol.name, bounds=symbol.bounds)
    )

  def __str__(self):
    layout = Element('mamelayout', {'version':'2'})
    
    layout.append(Space())
    layout.append(Comment('Decoration definitions'))
    layout.extend(self.decoration_definitions)
    layout.extend(self.colored_rects.values())

    layout.append(Space())
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
      CDATA(self.load("mame_layout_script.lua"))
    ])
    layout.append(script)

    document = Document(layout)

    return str(document)




