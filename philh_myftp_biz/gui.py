from typing import Callable, Any

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

    def __init__(self) -> None:
        from tkinter import Tk

        self._tk = Tk()

        # Prevent User from resizing/maximizing window
        self._tk.resizable(width=False, height=False)

        self.run = self._tk.mainloop

        self.title = 'New Window'

        self.size = (500, 300)

    def start(self) -> None:
        from .process import Thread

        Thread(self._tk.mainloop)

    def Text(self,
        text: str = '<Text>'
    ) -> None:
        from tkinter import Label

        Label(
            master = self._tk, 
            text = text,
            pady = 10
        ).pack()

    def Header(self,
        text: str = '<Header>'
    ) -> None:
        from tkinter import Label

        Label(
            master = self._tk,
            text = text,
            font = ('TkDefaultFont', 20),
            pady = 15
        ).pack()

    def Button(self,
        text: str = '<Button>',
        func: Callable[[], Any] = lambda:...
    ) -> None:
        from tkinter import Button
        
        Button(
            master = self._tk, 
            text = text, 
            command = func,
            pady = 5
        ).pack()