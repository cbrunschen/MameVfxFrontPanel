#!/usr/bin/env python3

from textwrap import indent, dedent, wrap
from dataclasses import dataclass, field
from sys import argv, exit
from argparse import ArgumentParser

from view import *
from mame_layout import *
from js_html import *

def main():
  parser = ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  group.add_argument('-l', '--layout', choices=['vfx','vfxsd','sd1'])
  group.add_argument('-js', '--javascript', action='store_true')
  # parser.add_argument('-fs', '--fontsize', default=1.4)

  args = parser.parse_args()
  visitor = None
  if args.javascript:
    visitor = HTMLJSVisitor()
  elif args.layout:
    visitor = MameLayoutVisitor(args.layout)
  
  if visitor:
    p = Panel(visitor.defaultFontSize())
    visitor.visitPanel(p)
    print(visitor)
  else:
    eprint(f'No visitor specified!')
    parser.print_usage(stderr)

if __name__ == '__main__':
  exit(main())
