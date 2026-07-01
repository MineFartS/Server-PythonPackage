from typing import Callable, Any, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from tkinter import Widget as _Widget
    from .page import Page
    from ..db import Key

class Widget(dict[str, Any]):

    raw: 'Type[_Widget]'

    _inst: '_Widget' = None

    bind: Callable[[], None] = lambda x: ...
    
    @property
    def inst(self) -> '_Widget | None':
        if self._inst and self._inst.winfo_exists():
            return self._inst

    @inst.setter
    def inst(self, inst:'_Widget') -> None:
        self._inst = inst
        self.bind()

class Text(Widget): 
    
    from tkinter import Label as raw

    def __init__(self, 
        text: str = '<Text>'
    ) -> None:
        self['text'] = text
        self['pady'] = 10

class Link(Widget):

    from tkinter import Label as raw

    driver = None

    def __init__(self,
        text: str = '<Link>',
        url: str = "https://example.com",
    ) -> None:
        self['text'] = text
        self['pady'] = 10
        self['fg'] = "blue"
        self['font'] = ("Arial", 12, "underline")
        self['cursor'] = "hand2"

        self.url = url

    def bind(self) -> None:
        from webbrowser import open

        self.inst.bind(
            "<Button-1>", 
            lambda e: open(self.url)
        )

class Input(Widget):

    from customtkinter import CTkEntry as raw
     
    def __init__(self,
        text: str = '<Input>', *,
        secure: bool = False,
        key: Key = None
    ) -> None:
        
        self['placeholder_text'] = text

        self.key = key 

        if secure:
            self['show'] = '*'

    def bind(self) -> None:

        self.input = ""

        self.inst.bind("<KeyRelease>", self._set)

    def _set(self, _) -> None:
        
        self.input = self.inst.get()

        if self.key:
            self.key.save(self.input)

class Header(Widget):

    from tkinter import Label as raw
        
    def __init__(self, 
        text: str = '<Header>'
    ) -> None:
        self['text'] = text
        self['font'] = ('TkDefaultFont', 20)
        self['pady'] = 15

class Button(Widget):

    from tkinter import Button as raw
        
    def __init__(self,
        text: str = '<Button>', 
        onclick: 'None|Page|Callable[[], Any]' = None,
    ) -> None:
        from .page import Page

        self['text'] = text
        self['pady'] = 5

        if callable(onclick):
            self['command'] = onclick

        elif isinstance(onclick, Page):
            self['command'] = lambda: setattr(onclick.gui, 'page', onclick)

        else:
            self['command'] = lambda: ...

