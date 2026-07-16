from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from .page import Page

class ClosedWindowException(BaseException):
    def throw() -> NoReturn:
        raise ClosedWindowException('Window was improperly terminated')

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

    def __report_callback_exception(self, exc_type, exc_value, exc_traceback) -> None:
        from sys import __excepthook__

        if issubclass(exc_type, ClosedWindowException):
            self._tk.quit()
            self._saved_exc = exc_type(exc_value).with_traceback(exc_traceback)
        else:
            __excepthook__(exc_type, exc_value, exc_traceback)

    def __init__(self) -> None:
        from tkinter import Tk

        self._tk = Tk()
        self.close = self._tk.destroy

        # Prevent User from resizing/maximizing window
        self._tk.resizable(width=False, height=False)
        
        self._tk.report_callback_exception = self.__report_callback_exception

        self._tk.protocol(
            "WM_DELETE_WINDOW",
            ClosedWindowException.throw
        )

        self.title = 'New Window'

        self.size = (500, 300)

    def run(self) -> None:

        self._tk.mainloop()

        if hasattr(self, '_saved_exc'):
            raise self._saved_exc

    def Page(self) -> Page:
        from .page import Page
        return Page(self)
    
    def reload(self) -> None:

        self.page = self.page

        self._tk.update()
