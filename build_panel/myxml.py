#!/usr/bin/env python

from dataclasses import dataclass, field
from textwrap import indent

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