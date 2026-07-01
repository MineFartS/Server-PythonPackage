from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .page import Page
    
class Window:

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
        
        for widget in (value or []):
            widget.inst = widget.raw(self._tk, **widget)
            widget.inst.pack()

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

    def Page(self) -> Page:
        from .page import Page
        return Page(self)
    
    def reload(self) -> None:

        self.page = self.page

        self._tk.update()
