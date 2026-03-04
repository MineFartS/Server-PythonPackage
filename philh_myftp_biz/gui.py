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

    def __init__(self) -> None:
        from tkinter import Tk

        self._tk = Tk()
        
        self.title = 'New Window'

        self.run = self._tk.mainloop

    def start(self) -> None:
        from .process import Thread

        Thread(self._tk.mainloop)

    def Text(self,
        text: str = '<Text>'
    ) -> None:
        from tkinter import Label

        Label(
            master = self._tk, 
            text = text
        ).pack()

    def Button(self,
        text: str = '<Button>',
        func: Callable[[], Any] = lambda:...
    ) -> None:
        from tkinter import Button
        
        Button(
            master = self._tk, 
            text = text, 
            command = func
        ).pack()