
#!/usr/bin/env python

from dataclasses import dataclass, field
from rect import *
from util import *
from os import path

ABOVE = 1
CENTERED = 2
BELOW = CENTERED
ABOVE_CENTERED = ABOVE | CENTERED

@dataclass
class Shade:
  name: str
  color: str
  pressed_color: str

SHADE_LIGHT = Shade('light', "#bbbbbb", "#ffffff")
SHADE_MEDIUM = Shade('medium', "#777777", "#ffffff")
SHADE_DARK = Shade('dark', "#333333", '#ffffff')

roughDisplayRect = Rect(37.5, 16.25, 205, 30)
charRect = Rect(0, 0, 342, 572)
charsRect = Rect(0, 0, 40 * charRect.w, 2 * charRect.h)
displayRect = charsRect.fitWithin(roughDisplayRect)

displayGlassRect = Rect(25, -5, 230, 67.5)

class ViewElement:
  def accept(self, visitor: 'ViewVisitor') -> None:
    pass

class ViewVisitor:
  def defaultFontSize(self):
    return 3.5
  
  def load(self, fname):
    p = path.join(path.dirname(path.realpath(__file__)), fname)
    with open(p, "rt") as f:
      return f.read(-1)

  def visitPanel(self, panel: 'Panel'):
    for i in panel.items:
      i.accept(self)

  def visitConditional(self, conditional: 'Conditional'):
    pass

  def visitAccentColor(self, accent_color: 'AccentColor'):
    pass

  def visitDisplay(self, display: 'Display'):
    pass

  def visitButton(self, button: 'Button'):
    pass

  def visitLight(self, light: 'Light'):
    pass

  def visitLabel(self, label: 'Label'):
    pass

  def visitSlider(self, slider: 'Slider'):
    pass

  def visitRectangle(self, rectangle: 'Rectangle'):
    pass

  def visitSymbol(self, rectangle: 'Symbol'):
    pass

@dataclass
class AccentColor(ViewElement):
  rgb: str

  def accept(self, visitor: ViewVisitor):
    visitor.visitAccentColor(self)

@dataclass
class Display(ViewElement):
  bounds: Rect

  def accept(self, visitor: ViewVisitor):
    visitor.visitDisplay(self)

@dataclass
class Button(ViewElement):
  bounds: Rect
  label: str
  number: int
  shade: Shade
  light: 'Light|None' = None

  def accept(self, visitor):
    visitor.visitButton(self)

@dataclass
class Light(ViewElement):
  bounds: Rect
  number: int

  def accept(self, visitor):
    visitor.visitLight(self)

@dataclass
class Slider(ViewElement):
  bounds: Rect
  channel: int
  name: str

  def accept(self, visitor):
    visitor.visitSlider(self)

@dataclass
class Label(ViewElement):
  bounds: Rect
  text: str
  fontSize: float
  bold: bool
  italic: bool
  centered: bool

  def accept(self, visitor):
    visitor.visitLabel(self)

@dataclass
class Rectangle(ViewElement):
  bounds: Rect
  color: str
    
  def accept(self, visitor):
    visitor.visitRectangle(self)

@dataclass
class Symbol(ViewElement):
  bounds: Rect
  name: str
  color: str

  def accept(self, visitor):
    visitor.visitSymbol(self)

@dataclass
class Conditional(ViewElement):
  condition: str
  ifTrue: list[ViewElement] = field(default_factory=list)
  ifFalse: list[ViewElement] = field(default_factory=list)
  items: list[ViewElement]|None = None

  def isTrue(self):
    self.items = self.ifTrue
    return True

  def isFalse(self):
    self.items = self.ifFalse
    return True
  
  def end(self):
    self.items = None
    return None
    
  def accept(self, visitor):
    visitor.visitConditional(self)

@dataclass
class Panel(ViewElement):
  fontSize: float
  # these are all internal variables really
  keyboard: str|None = None
  bounds: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
  background: Rectangle|None = None
  conditional: Conditional|None = None
  items: list[ViewElement] = field(default_factory=list)

  color_vfx = "#299ca3"
  color_sd1 = "#db5f6a"

  def __post_init__(self):
    self.onCondition('isSd1')
    if self.isTrue():
      self.setAccentColor(self.color_sd1)
    if self.isFalse():
      self.setAccentColor(self.color_vfx)
    self.endCondition()

    self.background = Rectangle(self.bounds, '#222222')
    self.add(self.background)
    self.add(Rectangle(displayGlassRect, '#000000'))
    self.add(Display(displayRect))

    self.addButtonWithLightBelowDisplay(25, 72.5, "#CartBankSet", 52, SHADE_LIGHT, 0xf)
    
    self.onCondition('isSd1')
    if self.isTrue():
      self.addLabel(25, 87.5, 15, self.fontSize, "BankSet", bold=True, centered=True)
    if self.isFalse():
      self.addLabel(25, 87.5, 15, self.fontSize, "Cart", bold=True, centered=True)
    self.endCondition()

    self.addButtonWithLightBelowDisplay(40, 72.5, "#Sounds",   53, SHADE_LIGHT, 0xd)
    self.addLabel(40, 87.5, 15, self.fontSize, "Sounds", bold=True, centered=True)

    self.addButtonWithLightBelowDisplay(55, 72.5, "#Presets",  54, SHADE_LIGHT, 0x7)
    self.addLabel(55, 87.5, 15, self.fontSize, "Presets", bold=True, centered=True)

    self.addButtonWithLightBelowDisplay(105, 72.5, "#0", 55, SHADE_MEDIUM, 0xe)
    self.addButtonWithLightBelowDisplay(120, 72.5, "#1", 56, SHADE_MEDIUM, 0x6)
    self.addButtonWithLightBelowDisplay(135, 72.5, "#2", 57, SHADE_MEDIUM, 0x4)
    self.addButtonWithLightBelowDisplay(150, 72.5, "#3", 46, SHADE_MEDIUM, 0xc)
    self.addButtonWithLightBelowDisplay(165, 72.5, "#4", 47, SHADE_MEDIUM, 0x3)
    self.addButtonWithLightBelowDisplay(180, 72.5, "#5", 48, SHADE_MEDIUM, 0xb)
    self.addButtonWithLightBelowDisplay(195, 72.5, "#6", 49, SHADE_MEDIUM, 0x2)
    self.addButtonWithLightBelowDisplay(210, 72.5, "#7", 35, SHADE_MEDIUM, 0xa)
    self.addButtonWithLightBelowDisplay(225, 72.5, "#8", 34, SHADE_MEDIUM, 0x1)
    self.addButtonWithLightBelowDisplay(240, 72.5, "#9", 25, SHADE_MEDIUM, 0x9)

    self.addLabel(105, 87.5, 15, self.fontSize, "0", bold=True, centered=True)
    self.addLabel(120, 87.5, 15, self.fontSize, "1", bold=True, centered=True)
    self.addLabel(135, 87.5, 15, self.fontSize, "2", bold=True, centered=True)
    self.addLabel(150, 87.5, 15, self.fontSize, "3", bold=True, centered=True)
    self.addLabel(165, 87.5, 15, self.fontSize, "4", bold=True, centered=True)
    self.addLabel(180, 87.5, 15, self.fontSize, "5", bold=True, centered=True)
    self.addLabel(195, 87.5, 15, self.fontSize, "6", bold=True, centered=True)
    self.addLabel(210, 87.5, 15, self.fontSize, "7", bold=True, centered=True)
    self.addLabel(225, 87.5, 15, self.fontSize, "8", bold=True, centered=True)
    self.addLabel(240, 87.5, 15, self.fontSize, "9", bold=True, centered=True)

    # Large buttons on the main panel part
    self.addLargeButton         (270, 72.5, "Replace\nProgram", 29, SHADE_MEDIUM)

    self.addLargeButton         (385, 72.5, "Select\nVoice", 5, SHADE_MEDIUM)
    self.addLargeButton         (400, 72.5, "Copy",          9, SHADE_MEDIUM)
    self.addLargeButton         (415, 72.5, "Write",         3, SHADE_MEDIUM)
    self.addLargeButtonWithLight(430, 72.5, "Compare",       8, SHADE_MEDIUM, 0x5)

    # Small buttons, main panel
    # -- Performance:
    self.addSmallButton(270, 50, "Patch\nSelect",   26, SHADE_DARK, True)
    self.addSmallButton(285, 50, "MIDI",            27, SHADE_DARK, True)
    self.addSmallButton(300, 50, "Effects",         28, SHADE_DARK, True)

    self.addSmallButton(270, 32.5, "Key\nZone",       39, SHADE_DARK, False)
    self.addSmallButton(285, 32.5, "Trans-\npose",    40, SHADE_DARK, False)
    self.addSmallButton(300, 32.5, "Release",         41, SHADE_DARK, False)

    self.addSmallButton(270,  15, "Volume",          36, SHADE_DARK, False)
    self.addSmallButton(285,  15, "Pan",             37, SHADE_DARK, False)
    self.addSmallButton(300,  15, "Timbre",          38, SHADE_DARK, False)
    
    # -- Programming:
    self.addSmallButton(385, 50, "Wave",             4, SHADE_DARK, False)
    self.addSmallButton(400, 50, "Mod\nMixer",       6, SHADE_DARK, False)
    self.addSmallButton(415, 50, "Program\nControl", 2, SHADE_DARK, False)
    self.addSmallButton(430, 50, "Effects",          7, SHADE_DARK, True)

    self.addSmallButton(385, 32.5, "Pitch",           11, SHADE_DARK, False)
    self.addSmallButton(400, 32.5, "Pitch\nMod",      13, SHADE_DARK, False)
    self.addSmallButton(415, 32.5, "Filters",         15, SHADE_DARK, True)
    self.addSmallButton(430, 32.5, "Output",          17, SHADE_DARK, True)

    self.addSmallButton(385,  15, "LFO",             10, SHADE_DARK, True)
    self.addSmallButton(400,  15, "Env1",            12, SHADE_DARK, True)
    self.addSmallButton(415,  15, "Env2",            14, SHADE_DARK, True)
    self.addSmallButton(430,  15, "Env3",            16, SHADE_DARK, True)

    # Display buttons - approximate:
    self.addSmallButton(80, 52.5, "#display_below_left", 50, SHADE_DARK, False)
    self.addSmallButton(142.5, 52.5, "#display_below_middle", 44, SHADE_DARK, False)
    self.addSmallButton(200, 52.5, "#display_below_right", 45, SHADE_DARK, False)

    self.addSmallButton(80,  0, "#display_above_left", 58, SHADE_DARK, False)
    self.addSmallButton(142.5,  0, "#diplay_above_center", 42, SHADE_DARK, False)
    self.addSmallButton(200,  0, "#display_above_right", 43, SHADE_DARK, False)

    # Value slider
    self.addSlider(-20, 10, 3, "data_entry")

    # Increment and Decrement
    self.addIncDecButton(-42.5, 55, "#decrement", 63, SHADE_DARK, False)
    self.addIncDecButton(-42.5, 30, "#increment", 62, SHADE_DARK, False)

    self.addDownTriangle(-37.5, 50, 5, 2.5)
    self.addUpTriangle(-37.5, 25, 5, 2.5)

    # Volume slider
    self.addSlider(-90, 10, 5, "volume")

    # The colored lines along the base:
    self.addAccentColoredLine(-90, 92.5, 415, 0.5)
    self.addAccentColoredLine(270, 92.5, 55, 0.5)
    self.addAccentColoredLine(327.5, 92.5, 55, 0.5)
    self.addAccentColoredLine(385, 92.5, 60, 0.5)

    # And the labels just above it:
    self.addLabel(-90, 87.5, 35, self.fontSize, "Volume", bold=True)
    self.addLabel(-42.5, 87.5, 35, self.fontSize, "Data Entry", bold=True)
    self.addLabel(270, 87.5, 35, self.fontSize, "Performance", bold=True)
    self.addLabel(385, 87.5, 35, self.fontSize, "Programming", bold=True)

    # The things that are conditional.
    # When the keyboard has a sequencer:
    self.onCondition("hasSeq")
    if self.isTrue():
      self.addButtonBelowDisplay     (70, 72.5, "#Seq",      51, SHADE_LIGHT)
      self.addLabel(70, 87.5, 15, self.fontSize, "Seq", centered=True, bold=True)

      self.addWhiteLine(285, 72.5 - 1.5 * self.fontSize - 0.05, 7.5, 0.25)
      self.addLabel(292.5, 72.5 - 2 * self.fontSize, 15, self.fontSize, "Tracks", centered=True)
      self.addWhiteLine(307.5, 72.5 - 1.5 * self.fontSize - 0.05, 7.5, 0.25)
      self.addLargeButtonWithLight(285, 72.5, "1-6",              30, SHADE_MEDIUM, 0x0, centered=True)
      self.addLargeButtonWithLight(300, 72.5, "7-12",             31, SHADE_MEDIUM, 0x8, centered=True)
      
      # The 'Master', 'Storage' and 'MIDI Control' buttons are small & at the top,
      # the sequencer buttons are big and at the bottom.
      self.addLargeButton(327.5, 72.5, "Rec",           19, SHADE_MEDIUM)
      self.addLargeButton(342.5, 72.5, "Stop\n/Cont",   22, SHADE_MEDIUM)
      self.addLargeButton(357.5, 72.5, "Play",          23, SHADE_MEDIUM)

      self.addSmallButton(327.5, 50, "Click",         32, SHADE_DARK, False)
      self.addSmallButton(342.5, 50, "Seq\nControl",  18, SHADE_DARK, True)
      self.addSmallButton(357.5, 50, "Locate",        33, SHADE_DARK, True)

      self.addSmallButton(327.5, 32.5, "Song",          60, SHADE_DARK, False)
      self.addSmallButton(342.5, 32.5, "Seq",           59, SHADE_DARK, False)
      self.addSmallButton(357.5, 32.5, "Track",         61, SHADE_DARK, False)

      self.addSmallButton(327.5,  15, "Master",        20, SHADE_LIGHT, True)
      self.addSmallButton(342.5,  15, "Storage",       21, SHADE_LIGHT, False)
      self.addSmallButton(357.5,  15, "MIDI\nControl", 24, SHADE_LIGHT, True)

      self.addWhiteLine(327.5, 32.5 - 1.5 * self.fontSize - 0.05, 17.5, 0.25)
      self.addLabel(345, 32.5 - 2 * self.fontSize, 10, self.fontSize, "Edit", centered=True)
      self.addWhiteLine(355, 32.5 - 1.5 * self.fontSize - 0.05, 17.5, 0.25)

      self.addLabel(327.5, 5-(0.5 + self.fontSize), 35, self.fontSize, "System", bold=True)
      self.addAccentColoredLine(327.5, 5-0.5, 55, 0.5)
      self.addLabel(327.5, 87.5, 25, self.fontSize, "Sequencer", bold=True)

    # When there is no sequencer:
    if self.isFalse():
      self.addWhiteLine(285, 72.5 - 1.5 * self.fontSize - 0.05, 10, 0.1)
      self.addLabel(295, 72.5 - 2 * self.fontSize, 10, self.fontSize, "Multi", centered=True)
      self.addWhiteLine(305, 72.5 - 1.5 * self.fontSize - 0.05, 10, 0.1)
      self.addLargeButtonWithLight(285, 72.5, "A",              30, SHADE_MEDIUM, 0x0, centered=True)
      self.addLargeButtonWithLight(300, 72.5, "B",              31, SHADE_MEDIUM, 0x8, centered=True)

      # The 'Master', 'Storage' and 'MIDI Control' buttons are large & at the bottom,
      # and there are no sequencer buttons
      self.addLargeButton(327.5, 72.5, "Master",        20, SHADE_LIGHT, True)
      self.addLargeButton(342.5, 72.5, "Storage",       21, SHADE_LIGHT, False)
      self.addLargeButton(357.5, 72.5, "MIDI\nControl", 24, SHADE_LIGHT, True)

      self.addLabel(327.5, 87.5, 35, self.fontSize, "System", bold=True)
    self.endCondition()

    # Add just a little space around.
    self.bounds = self.bounds.outset(5, 5)
    # Update the background bounds as well.
    self.background.bounds = self.bounds

  def add(self, e):
    destination = self.conditional.items if self.conditional else self.items
    destination.append(e)
    self.bounds = self.bounds.enclosing(e)
  
  def setAccentColor(self, rgb):
    self.add(AccentColor(rgb))
  
  def addLabel(self, x, y, w, fontSize, label, bold = False, italic = False, centered = False):      
    self.add(Label(Rect(x, y, w, fontSize), label, fontSize, bold, italic, centered))
  
  def addButton(self, x, y, w, h, label, labelPosition, value, shade, multiPage = False, lightId = -1):
    button = Button(Rect(x, y, w, h), label, value, shade)
    self.add(button)

    if not label.startswith("#"):
      labelLines = label.split("\n")
      nLines = len(labelLines)
      y0 = h if labelPosition == BELOW else -nLines * self.fontSize
      centered = ((labelPosition & CENTERED) != 0)
      
      for i in range(nLines):
        line = labelLines[i]
        self.addLabel(x, y + y0 + i * self.fontSize, w, self.fontSize, line, bold=False, italic=True, centered=centered)
    
    if lightId >= 0:
      # Light bounds are relative to button bounds
      button.light = Light(Rect(w/3, h/25, w/3, h/3), lightId)

  def addButtonBelowDisplay(self, x, y, label, value, shade):
    self.addButton(x, y, 15, 10, label, BELOW, value, shade, False, -1)
  
  def addButtonWithLightBelowDisplay(self, x, y, label, value, shade, lightId):
    self.addButton(x, y, 15, 10, label, BELOW, value, shade, False, lightId)
  
  def addLargeButton(self, x, y, label, value, shade, multiPage=False):
    self.addButton(x, y, 15, 10, label, ABOVE, value, shade, False, -1)
  
  def addLargeButtonWithLight(self, x, y, label, value, shade, lightId, centered=False):
    self.addButton(x, y, 15, 10, label, ABOVE_CENTERED if centered else ABOVE, value, shade, False, lightId)

  def addSmallButton(self, x, y, label, value, shade, multiPage):
    self.addButton(x, y, 15, 5, label, ABOVE, value, shade, multiPage, -1)
  
  def addIncDecButton(self, x, y, label, value, shade, multiPage):
    self.addButton(x, y, 15, 5, label, ABOVE_CENTERED, value, shade, multiPage, -1)
  
  def addSlider(self, x, y, channel, name):
    self.add(Slider(Rect(x, y, 20, 60), channel, name)) # always 20 wide, 60 tall

  def addAccentColoredLine(self, x, y, w, h):
    self.add(Rectangle(Rect(x, y, w, h), "accent"))

  def addWhiteLine(self, x, y, w, h):
    self.add(Rectangle(Rect(x, y, w, h), "#ffffff"))

  def addUpTriangle(self, x, y, w, h):
    self.add(Symbol(Rect(x, y, w, h), 'triangle_up', "#ffffff"))

  def addDownTriangle(self, x, y, w, h):
    self.add(Symbol(Rect(x, y, w, h), 'triangle_down', "#ffffff"))

  def onCondition(self, condition):
    conditional = Conditional(condition)
    self.add(conditional)
    self.conditional = conditional
  
  def isTrue(self):
    return self.conditional.isTrue() if self.conditional is not None else False

  def isFalse(self):
    return self.conditional.isFalse() if self.conditional is not None else False

  def endCondition(self):
    self.conditional = self.conditional.end() if self.conditional is not None else None
