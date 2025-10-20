#!/usr/bin/env python

from re import sub
from textwrap import wrap
from sys import stderr

def to_id(s):
  """Merge multiple lines (trimming hyphenation),
     then replace non-identifier characters with '_',
     finally case-fold."""
  return sub(r'[^a-zA-Z0-9]', '_', s.replace('-\n','')).casefold()

def clean(d: dict[str, str|None]) -> dict[str, str]:
  return { k : v for (k, v) in d.items() if v != None }

def rgb_components(rgb):
  return [int(c, 16) / 255.0 for c in wrap(rgb.removeprefix('#'), 2)]

def eprint(*args, **kwargs):
  print(*args, file=stderr, **kwargs)
