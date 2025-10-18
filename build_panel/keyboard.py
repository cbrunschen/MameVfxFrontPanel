#!/usr/bin/env python3

from dataclasses import dataclass, field
from rect import *
from util import *
from os import path

# measured:
# width of the 61 keys, from edge of white key to edge of white key,
# not including space outside the keys but including the 'kerf' between the keys
w_61 = 845

# the length of the black keys
l_black = 88

# the length of the white keys
l_white = 138

# the horizontal space, kerf, between keys
kerf_x = 1

# the vertical space between the lower end of a black key and the upper end of the surrounding white keys
kerf_y = 2

# the number of octaves on the measured keyboard
octaves = 5

# calculate the width of each white key
w_white = ((w_61 + kerf_x) / (7 * octaves + 1)) - kerf_x

# calculate the width of each black key
w_black = ((w_61 - w_white) / (12 * octaves)) - kerf_x

# calculate the width a number of octaves,
# _not_ including an extra 'C' above or sorrounding kerf
def w_oct(i):
  return (w_white + kerf_x) * (7 * i) - kerf_x


class KeyboardElement:
  def accept(self, visitor: 'KeyboardVisitor') -> None:
    pass

class KeyboardVisitor:
  def visitKey(self, bk: 'Key'):
    pass

  def visitKeyboard(self, kb: 'Keyboard'):
    for k in kb.keys:
      k.accept(self)

@dataclass
class Key(KeyboardElement):
  black: bool
  bounds: Rect
  number: int

  def accept(self, visitor: KeyboardVisitor):
    visitor.visitKey(self)

@dataclass
class Keyboard(KeyboardElement):
  octaves: int
  # this will be populated
  keys: list[KeyboardElement] = field(default_factory=list)

  def accept(self, visitor: KeyboardVisitor):
    visitor.visitKeyboard(self)

  @property
  def bounds(self) -> Rect:
    b = Rect(0, 0, 0, 0)
    for k in self.keys:
      b = b.union(k.bounds)

    # b is now the rectangle of akk the keys with internal kerf, but no external space.
    # Add 2.5mm laterally and 5.0 mm below.
    b = Rect(b.x - 2.5, b.y, b.width + 5.0, b.height + 5.0)

  def __post_init__(self):
    

