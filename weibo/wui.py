#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'lihe <imanux@sina.com>'
__date__ = '23/12/2017 11:05 AM'
__description__ = '''
    ☰
  ☱   ☴
☲   ☯   ☵
  ☳   ☶
    ☷
'''

import os
import sys

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

import urwid
from urwid import Columns, AttrMap, Button, WidgetWrap, Text

palette = [
    (None, 'light gray', 'black'),
    ('heading', 'black', 'light gray'),
    ('line', 'black', 'light gray'),
    ('options', 'dark gray', 'black'),
    ('focus heading', 'white', 'dark red'),
    ('focus line', 'black', 'dark red'),
    ('focus options', 'black', 'light gray'),
    ('selected', 'white', 'dark blue'),
]
focus_map = {
    'heading': 'focus heading',
    'options': 'focus options',
    'line': 'focus line',
}


class HBoxes(Columns):
    def __init__(self):
        Columns.__init__(self, [], dividechars=1)

    def open_box(self, box):
        if self.contents:
            del self.contents[self.focus_position + 1:]

        self.contents.append((
            AttrMap(box, 'options', focus_map=focus_map),
            self.options('given', 24),
        ))
        self.focus_position = len(self.contents) - 1


top = HBoxes()


class MenuButton(Button):
    def __init__(self, cap, cb):
        Button.__init__(self, '')
        urwid.connect_signal(self, 'click', cb)
        self._w = AttrMap(
            urwid.SelectableIcon(
                ['  \N{BULLET}', cap], 2
            ),
            None,
            'selected',
        )


class SubMenu(WidgetWrap):
    def __init__(self, cap, choices):
        WidgetWrap.__init__(
            self,
            MenuButton(
                [cap, "\N{HORIZONTAL ELLIPSIS}"], self.open_menu
            ))
        line = urwid.Divider('\N{LOWER ONE QUARTER BLOCK}')
        listbox = urwid.ListBox(
            urwid.SimpleFocusListWalker(
                [
                    AttrMap(Text(['\n   ', cap]), 'heading'),
                    AttrMap(line, 'line'),
                    urwid.Divider()
                ]
                + choices
                + [urwid.Divider()]
            ))

        self.menu = AttrMap(listbox, 'options')

    def open_menu(self, btn):
        top.open_box(self.menu)


class Choice(WidgetWrap):
    def __init__(self, cap):
        WidgetWrap.__init__(
            self,
            MenuButton(cap, self.item_chosen)
        )
        self.cap = cap

    def item_chosen(self, btn):
        res = Text(['   You chose', self.cap, '\n'])
        done = MenuButton('Ok', exit_program)
        res_box = urwid.Filler(urwid.Pile([res, done]))
        top.open_box(AttrMap(res_box, 'options'))


def exit_on_q(key):
    if key in ('q', 'Q'):
        exit_program(key)


def exit_program(key):
    raise urwid.ExitMainLoop()


menu_top = SubMenu(
    '弱弱弱一生', [
        SubMenu('Applications', [
            SubMenu('Accessories', [
                Choice('Text Editor'),
                Choice('Terminal'),
            ]),
        ]),
        SubMenu('System', [
            SubMenu('Preferences', [
                Choice('Appearance'),
            ]),
            Choice('Lock Screen'),
        ]),
    ]
)


def run():
    top.open_box(menu_top.menu)
    urwid.MainLoop(
        urwid.Filler(top, 'top', 10),
        palette=palette,
        unhandled_input=exit_on_q
    ).run()


if __name__ == '__main__':
    run()
