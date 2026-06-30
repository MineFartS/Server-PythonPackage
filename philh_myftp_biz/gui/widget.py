from typing import Callable, Any, TYPE_CHECKING, Literal, Type

if TYPE_CHECKING:
    from tkinter import Label, Button
    from .window import Window
    from .page import Page

class Widget(dict[str, Any]):

    def __init__(self,
        type: Literal['Label', 'Button', 'Text']
    ) -> None:
        import tkinter

        self.type: 'Type[Label|Button]' = getattr(tkinter, type)

    def instance(self, gui:'Window'):
        return self.type(
            master = gui._tk,
            **self 
        )

    @staticmethod
    def Text(
        text: str = '<Text>'
    ) -> 'Widget':

        widget = Widget('Label')

        widget['text'] = text
        widget['pady'] = 10

        return widget

    @staticmethod
    def Header(
        text: str = '<Header>'
    ) -> 'Widget':
        
        widget = Widget('Label')

        widget['text'] = text
        widget['font'] = ('TkDefaultFont', 20)
        widget['pady'] = 15

        return widget

    @staticmethod
    def Button(
        text: str = '<Button>', 
        onclick: 'None|Page|Callable[[], Any]' = None,
    ) -> 'Widget':
        from .page import Page

        widget = Widget('Button')

        widget['text'] = text
        widget['pady'] = 5

        if callable(onclick):
            widget['command'] = onclick

        elif isinstance(onclick, Page):
            widget['command'] = lambda: setattr(onclick.gui, 'page', onclick)

        return widget

    @staticmethod
    def Console():
        ...
        #widget = Widget('Text')
        # TODO
