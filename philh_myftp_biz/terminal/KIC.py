from typing import TYPE_CHECKING
from ..classtools import singleton

if TYPE_CHECKING:
    from signal import _HANDLER
    from types import FrameType
    from types import TracebackType

from signal import SIGINT  as _INT
from signal import SIG_DFL as _DFL

@singleton
class KIC:
    """KeyboardInterrupt Catcher"""
    
    traceback: 'None|TracebackType' = None

    def enable(self) -> None:
        from signal import signal

        signal(self._INT, self._handler)

    def disable(self) -> None:
        from signal import signal
        
        signal(self._INT, self._DFL)

    def _handler(self,
        sig: '_HANDLER',
        frame: 'FrameType'
    ) -> None:
        from types import TracebackType

        self.traceback = TracebackType(
            tb_next = None, 
            tb_frame = frame, 
            tb_lasti = frame.f_lasti, 
            tb_lineno = frame.f_lineno
        )

    def check(self):

        if self.traceback:
            raise KeyboardInterrupt().with_traceback(self.traceback)
