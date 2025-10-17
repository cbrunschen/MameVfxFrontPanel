#!/usr/bin/env python

from dataclasses import dataclass

from myxml import *
from util import *

@dataclass
class Rect:
  x: float
  y: float
  w: float
  h: float
  
  def union(self, other):
    if other is None or not isinstance(other, Rect):
      return self
    
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
  
  def enclosing(self, o):
    if hasattr(o, 'bounds'):
      return self.union(o.bounds)
    else:
      return self
    
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
    }), [])
  
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

  def coords(self):
    return f'{self.x:.5g}, {self.y:.5g}, {self.w:.5g}, {self.h:.5g}'
