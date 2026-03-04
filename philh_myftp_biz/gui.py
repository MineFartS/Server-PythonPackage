from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Label, Button

class Page:

    def __init__(self,
        gui: 'GUI'
    ) -> None:
        
        self._widgets: 'list[dict[str, dict|Label|Button]]' = []
        self.gui = gui

    def Text(self,
        text: str = '<Text>'
    ) -> None:
        from tkinter import Label

        self._widgets += [{
            'class': Label,
            'kwargs': {
                'text': text,
                'pady': 10
            }
        }]

    def Header(self,
        text: str = '<Header>'
    ) -> None:
        from tkinter import Label

        self._widgets += [{
            'class': Label,
            'kwargs': {
                'text': text,
                'font': ('TkDefaultFont', 20),
                'pady': 15
            }
        }]

    def Button(self,
        text: str = '<Button>',
        func: Callable[[], Any] = lambda:...
    ) -> None:
        from tkinter import Button
        
        self._widgets += [{
            'class': Button,
            'kwargs': {
                'text': text, 
                'command': func,
                'pady': 5
            }
        }]

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

            for widget in value._widgets:

                instance: 'Label|Button' = widget['class'](
                    master = self._tk,    
                    **widget['kwargs']
                )

                instance.pack()

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

    def Page(self) -> Page:

        return Page(self)