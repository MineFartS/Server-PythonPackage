from io import StringIO
from re import compile

ansi_escape = compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x0c')

class UnconsumingIO:
    
    def __init__(self, 
        stream: StringIO,
        clean: bool = False
    ) -> None:
        self._clean = clean
        self._stream = stream
        self._buffer = ""

    def read(self, size=None):
        from ..terminal import _cls_cmd
    
        self._buffer += self._stream.read()

        if self._clean:
            self._buffer = self._buffer.split(_cls_cmd)[-1]
            self._buffer = ansi_escape.sub('', self._buffer)

        if size is None:
            return self._buffer
        else:
            return self._buffer[:size]

