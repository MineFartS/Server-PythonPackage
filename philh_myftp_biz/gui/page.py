from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from .widget import Widget
    from .window import Window

class Page(list[Widget]):

    def __init__(self,
        gui: 'Window'
    ) -> None:
        self.gui = gui

    def __iadd__(self, value: Widget) -> Self:
        return super().__iadd__([value])
