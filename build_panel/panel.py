
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

buttonLabelFontSize = 1.8

roughDisplayRect = Rect(15, 6.5, 82, 12)
charRect = Rect(0, 0, 342, 572)
charsRect = Rect(0, 0, 40 * charRect.w, 2 * charRect.h)
displayRect = charsRect.fitWithin(roughDisplayRect)

displayGlassRect = Rect(10, -2, 92, 27)

class PanelElement:
  def accept(self, visitor: 'PanelVisitor') -> None:
    pass

class PanelVisitor:
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
class AccentColor(PanelElement):
  rgb: str

  def accept(self, visitor: PanelVisitor):
    visitor.visitAccentColor(self)

@dataclass
class Display(PanelElement):
  bounds: Rect

  def accept(self, visitor: PanelVisitor):
    visitor.visitDisplay(self)

@dataclass
class Button(PanelElement):
  bounds: Rect
  label: str
  number: int
  shade: Shade
  light: 'Light' = None

  def accept(self, visitor):
    visitor.visitButton(self)

@dataclass
class Light(PanelElement):
  bounds: Rect
  number: int

  def accept(self, visitor):
    visitor.visitLight(self)

@dataclass
class Slider(PanelElement):
  bounds: Rect
  channel: int
  name: str

  def accept(self, visitor):
    visitor.visitSlider(self)

@dataclass
class Label(PanelElement):
  bounds: Rect
  text: str
  fontSize: float
  italic: bool
  centered: bool

  def accept(self, visitor):
    visitor.visitLabel(self)

@dataclass
class Rectangle(PanelElement):
  bounds: Rect
  color: str
    
  def accept(self, visitor):
    visitor.visitRectangle(self)

@dataclass
class Symbol(PanelElement):
  bounds: Rect
  name: str
  color: str

@dataclass
class Conditional(PanelElement):
  condition: str
  ifTrue: list[PanelElement] = field(default_factory=list)
  ifFalse: list[PanelElement] = field(default_factory=list)
  items: list[PanelElement] = None

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
class Panel(PanelElement):
  # these are all internal variables really
  keyboard: str = None
  rect: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0))
  background: Rectangle = None
  conditional: Conditional = None
  items: list[PanelElement] = field(default_factory=list)

  color_vfx = "#299ca3"
  color_sd1 = "#db5f6a"

  def __post_init__(self):
    self.onCondition('isSd1')
    if self.isTrue():
      self.setAccentColor(self.color_sd1)
    if self.isFalse():
      self.setAccentColor(self.color_vfx)
    self.endCondition()

    self.background = Rectangle(self.rect, '#222222')
    self.add(self.background)
    self.add(Rectangle(displayGlassRect, '#000000'))
    self.add(Display(displayRect))

    self.addButtonWithLightBelowDisplay(10, 29, "#CartBankSet", 52, SHADE_LIGHT, 0xf)
    
    self.onCondition('isSd1')
    if self.isTrue():
      self.addLabel(10, 35, 6, buttonLabelFontSize, "BankSet", centered=True)
    if self.isFalse():
      self.addLabel(10, 35, 6, buttonLabelFontSize, "Cart", centered=True)
    self.endCondition()

    self.addButtonWithLightBelowDisplay(16, 29, "#Sounds",   53, SHADE_LIGHT, 0xd)
    self.addLabel(16, 35, 6, buttonLabelFontSize, "Sounds", centered=True)

    self.addButtonWithLightBelowDisplay(22, 29, "#Presets",  54, SHADE_LIGHT, 0x7)
    self.addLabel(22, 35, 6, buttonLabelFontSize, "Presets", centered=True)

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
    self.addSlider(-8, 4, 3, "data_entry")

    # Increment and Decrement
    self.addIncDecButton(-17, 22, "#increment", 63, SHADE_DARK, False)
    self.addIncDecButton(-17, 12, "#decrement", 62, SHADE_DARK, False)

    self.addUpTriangle(-15, 10, 2, 1)
    self.addDownTriangle(-15, 20, 2, 1)

    # Volume slider
    self.addSlider(-36, 4, 5, "volume")

    # The colored lines along the base:
    self.addAccentColoredLine(-36, 37, 166, 0.5)
    self.addAccentColoredLine(108, 37, 22, 0.5)
    self.addAccentColoredLine(131, 37, 22, 0.5)
    self.addAccentColoredLine(154, 37, 24, 0.5)

    # And the labels just above it:
    self.addLabel(-36, 35, 10, buttonLabelFontSize, "Volume")
    self.addLabel(-17, 35, 10, buttonLabelFontSize, "Data Entry")
    self.addLabel(108, 35, 10, buttonLabelFontSize, "Performance")
    self.addLabel(154, 35, 10, buttonLabelFontSize, "Programming")

    # The things that are conditional.
    # When the keyboard has a sequencer:
    self.onCondition("hasSeq")
    if self.isTrue():
      self.addButtonBelowDisplay     (28, 29, "#Seq",      51, SHADE_LIGHT)
      self.addLabel(28, 35, 6, buttonLabelFontSize, "Seq", centered=True)

      self.addWhiteLine(114, 29 - 1.5 * buttonLabelFontSize - 0.05, 3, 0.1)
      self.addLabel(117, 29 - 2 * buttonLabelFontSize, 6, buttonLabelFontSize, "Tracks", centered=True)
      self.addWhiteLine(123, 29 - 1.5 * buttonLabelFontSize - 0.05, 3, 0.1)
      self.addLargeButtonWithLight(114, 29, "1-6",              30, SHADE_MEDIUM, 0x0, centered=True)
      self.addLargeButtonWithLight(120, 29, "7-12",             31, SHADE_MEDIUM, 0x8, centered=True)
      
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

      self.addLabel(131, 2-(0.2 + buttonLabelFontSize), 10, buttonLabelFontSize, "System")
      self.addAccentColoredLine(131, 2-0.2, 22, 0.2)
      self.addLabel(131, 35, 10, buttonLabelFontSize, "Sequencer")

    # When there is no sequencer:
    if self.isFalse():
      self.addWhiteLine(114, 29 - 1.5 * buttonLabelFontSize - 0.05, 4, 0.1)
      self.addLabel(118, 29 - 2 * buttonLabelFontSize, 4, buttonLabelFontSize, "Multi", centered=True)
      self.addWhiteLine(122, 29 - 1.5 * buttonLabelFontSize - 0.05, 4, 0.1)
      self.addLargeButtonWithLight(114, 29, "A",              30, SHADE_MEDIUM, 0x0, centered=True)
      self.addLargeButtonWithLight(120, 29, "B",              31, SHADE_MEDIUM, 0x8, centered=True)

      # The 'Master', 'Storage' and 'MIDI Control' buttons are large & at the bottom,
      # and there are no sequencer buttons
      self.addLargeButton(131, 29, "Master",        20, SHADE_LIGHT, True)
      self.addLargeButton(137, 29, "Storage",       21, SHADE_LIGHT, False)
      self.addLargeButton(143, 29, "MIDI\nControl", 24, SHADE_LIGHT, True)

      self.addLabel(131, 35, 10, buttonLabelFontSize, "System")
    self.endCondition()

    # Add just a little space around.
    self.rect = self.rect.outset(2, 2)
    # Update the background bounds as well.
    self.background.bounds = self.rect

  def add(self, e):
    destination = self.conditional.items if self.conditional else self.items
    destination.append(e)
    self.rect = self.rect.enclosing(e)
  
  def setAccentColor(self, rgb):
    self.add(AccentColor(rgb))
  
  def addLabel(self, x, y, w, fontSize, label, italic = False, centered = False):      
    self.add(Label(Rect(x, y, w, fontSize), label, fontSize, italic, centered))
  
  def addButton(self, x, y, w, h, label, labelPosition, value, shade, multiPage = False, lightId = -1):
    button = Button(Rect(x, y, w, h), label, value, shade)
    self.add(button)

    if not label.startswith("#"):
      labelLines = label.split("\n")
      nLines = len(labelLines)
      y0 = h if labelPosition == BELOW else -nLines * buttonLabelFontSize
      centered = ((labelPosition & CENTERED) != 0)
      
      for i in range(nLines):
        line = labelLines[i]
        self.addLabel(x, y + y0 + i * buttonLabelFontSize, w, buttonLabelFontSize, line, italic=True, centered=centered)
    
    if lightId >= 0:
      # Light bounds are relative to button bounds
      button.light = Light(Rect(w/3, h/25, w/3, h/3), lightId)

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
  
  def addSlider(self, x, y, channel, name):
    self.add(Slider(Rect(x, y, 8, 24), channel, name)) # always 8 wide, 24 tall

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
    return self.conditional.isTrue()

  def isFalse(self):
    return self.conditional.isFalse()

  def endCondition(self):
    self.conditional = self.conditional.end()
