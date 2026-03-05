from typing import Callable, Any, TYPE_CHECKING, Literal, Type, Self

if TYPE_CHECKING:
    from tkinter import Label, Button

class Widget(dict[str, Any]):

    def __init__(self,
        type: Literal['Label', 'Button', 'Text']
    ) -> None:
        import tkinter

        self.type: 'Type[Label|Button]' = getattr(tkinter, type)

    def instance(self, gui:'GUI'):
        return self.type(
            master = gui._tk,
            **self 
        )

    @staticmethod
    def Text(
        text: str = '<Text>'
    ) -> Widget:

        widget = Widget('Label')

        widget['text'] = text
        widget['pady'] = 10

        return widget

    @staticmethod
    def Header(
        text: str = '<Header>'
    ) -> Widget:
        
        widget = Widget('Label')

        widget['text'] = text
        widget['font'] = ('TkDefaultFont', 20)
        widget['pady'] = 15

        return widget

    @staticmethod
    def Button(
        text: str = '<Button>', 
        onclick: None|Page|Callable[[], Any] = None,
    ) -> Widget:

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

class Page(list[Widget]):

    def __iadd__(self, value: Widget) -> Self:
        return super().__iadd__([value])

class GUI:

    #====================================================
    # TITLE

    @property
    def title(self) -> str:

        return self._tk.title()

    @title.setter
    def title(self, value:str) -> None:

        self._tk.title(value)

    #====================================================
    # SIZE

    @property
    def size(self) -> tuple[int, int]:

        height = self._tk.winfo_height()
        width = self._tk.winfo_width()

        return (width, height)

    @size.setter
    def size(self, value:tuple[int, int]) -> None:

        self._tk.geometry(f'{value[0]}x{value[1]}')

    #====================================================
    # PAGE

    @property
    def page(self) -> None | Page:

        if hasattr(self, '_page'):
            return self._page

    @page.setter
    def page(self,
        value: Page | None
    ) -> None:
        
        self._page = value
        
        for widget in self._tk.winfo_children():
            widget.destroy()
        
        if value:

            for widget in value:

                widget.instance(gui=self).pack()

    #====================================================

    def __init__(self) -> None:
        from tkinter import Tk

        self._tk = Tk()

        # Prevent User from resizing/maximizing window
        self._tk.resizable(width=False, height=False)
        self.run = self._tk.mainloop
        self.close = self._tk.destroy

        self.title = 'New Window'

        self.size = (500, 300)

    def start(self) -> None:
        from .process import Thread

        Thread(self._tk.mainloop)

    def reload(self) -> None:
        self.page = self.page