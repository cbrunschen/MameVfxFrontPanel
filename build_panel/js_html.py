#!/usr/bin/env python3

from textwrap import indent, dedent, wrap
from dataclasses import dataclass, field

from panel import *

class HTMLJSVisitor(PanelVisitor):

  def __init__(self):
    self.indent = '    '
    self.code = []
  
  def iin(self):
    self.indent = '  ' + self.indent
  
  def iout(self):
    self.indent = self.indent.removeprefix('  ')
  
  def defaultFontSize(self):
    return 3.5

  def append(self, s):
    self.code.append(indent(s, self.indent))
  
  def extend(self, s):
    self.code.extend([indent(l, self.indent) for l in s])

  def visitPanel(self, panel):
    super().visitPanel(panel)
    self.append(f'this.container.setAttribute("viewBox", "{panel.bounds.viewBox()}");')
  
  def visitAccentColor(self, color: AccentColor):
    self.append(f'this.accentColor = "{color.rgb}";')
  
  def visitConditional(self, conditional: Conditional):
    self.append(f'if ({conditional.condition}) {{')
    self.iin()
    for i in conditional.ifTrue:
      i.accept(self)
    self.iout()
    self.append(f'}} else {{ // not {conditional.condition}')
    self.iin()
    for i in conditional.ifFalse:
      i.accept(self)
    self.iout()
    self.append('}')

  def visitDisplay(self, display: 'Display'):
    self.append(dedent(f'''
      this.displayContainer = createElement("svg");
      this.display = new Display(this.displayContainer, 2, 40);
      this.displayContainer.setAttribute("preserveAspectRatio", "xMidYMid meet");
      this.displayContainer.setAttribute("x", {display.bounds.x});
      this.displayContainer.setAttribute("y", {display.bounds.y});
      this.displayContainer.setAttribute("width", {display.bounds.w});
      this.displayContainer.setAttribute("height", {display.bounds.h});
      this.container.appendChild(this.displayContainer);
    '''))

  def visitButton(self, button: 'Button'):
    shade = button.shade.name.upper()
    addButton = f'this.addButton({button.bounds.coords()}, {button.number}, Shade.{shade})'
    if button.light:
      light = button.light
      self.append(f'{addButton}.addLight(this.addLight({light.bounds.coords()}, {light.number}));')
    else:
      self.append(f'{addButton};')

  def visitLabel(self, label: 'Label'):
    bold = 'true' if label.bold else 'false'
    italic = 'true' if label.italic else 'false'
    centered = 'true' if label.centered else 'false'
    self.append(f'this.addLabel({label.bounds.coords()}, "{label.text}", {label.fontSize}, {bold}, {italic}, {centered});')

  def visitSlider(self, slider: 'Slider'):
    self.append(f'this.addSlider({slider.bounds.coords()}, {slider.channel}, 0.5);')

  def visitRectangle(self, rectangle: 'Rectangle'):
    color = 'this.accentColor' if rectangle.color == 'accent' else f'"{rectangle.color}"'
    self.append(f'this.addRectangle({rectangle.bounds.coords()}, {color});')

  def visitSymbol(self, symbol: 'Symbol'):
    self.append(f'this.addSymbol({symbol.bounds.coords()}, "{symbol.name}");')
  
  def __str__(self):
    (preamble, postamble) = self.load("FrontPanel.js").split('//CODE//')
    return '\n'.join([preamble] + self.code + [postamble])
