from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Widget as _Widget
    from .page import Page

class Widget(dict[str, Any]):

    raw: '_Widget'

class Text(Widget):
    
    from tkinter import Label as raw
    
    def __init__(self, 
        text: str = '<Text>'
    ) -> None:
        self['text'] = text
        self['pady'] = 10

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

