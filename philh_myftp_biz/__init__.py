from logging import StreamHandler as __StreamHandler
from logging import basicConfig as __basicConfig
from logging import Formatter as __Formatter
from functools import cached_property
from typing import TYPE_CHECKING
from sys import argv as __argv

if TYPE_CHECKING:
    from logging import LogRecord as __LogRecord
    from inspect import FrameInfo

#================================================================

def _arg(*name:str):
    return len(set(name) & set(__argv))

#================================================================

from .classtools import singleton
from .num import MutInt

@singleton
class VERBOSE(MutInt):

    def __init__(self):
        super().__init__(None)
        self.resume()

    def pause(self):
        self.value = 0

    def resume(self):
        self.value = _arg('-v', '--verbose')

#================================================================

HELP: bool = _arg('-h', '--help')

#================================================================

class _Formatter(__Formatter):

    table: dict[int, tuple[str, str]] = {
        10: ('VERB', 'GRAY'),
        20: ('INFO', 'WHITE'),
        25: ('MAIN', 'YELLOW'),
        30: ('WARN', 'YELLOW'),
        40: ('FAIL', 'RED'),
        50: ('CRIT', 'MAGENTA'),
    }

    @cached_property
    def _wfile(self):
        from .terminal import script_file
        from .pc import loc
        from time import time

        file = loc.logs.child(f'{script_file().name}.{time():.0f}.log')

        file.open('w').close()

        return file

    def _traceback(self,
        record: __LogRecord
    ) -> str:
        from traceback import extract_tb

        if record.exc_info is None:
            return ''

        tb = extract_tb(record.exc_info[2])

        outp = ''

        for frame in self._stack(tb):
            
            outp += f'\nFile "{frame.filename}", line {frame.lineno}'
            
        outp += '\n'
        outp += str(record.exc_info).split('>, ')[1].split(', <')[0]

        return outp.strip() + '\n'

    def _message(self,
        record: '__LogRecord'    
    ) -> str:
        from .classtools import stringify
        from .json import dumps
        
        if isinstance(record.msg, (str, int, float, bool)):
            message = str(record.msg)

        elif isinstance(record.msg, (tuple, list, dict)):
            message = dumps(record.msg, indent=2)
        
        else:
            message = stringify(record.msg)

        return message \
            .encode(errors='ignore') \
            .decode() \
            .strip('\n')

    def _stack(self, frames:list[FrameInfo]):

        for frame in frames:

            path = frame.filename.lower()

            if '\\lib\\logging\\' in path:
                continue

            if '\\site-packages\\fastapi\\' in path:
                continue

            if '\\site-packages\\starlette\\' in path:
                continue

            if '\\site-packages\\uvicorn\\' in path:
                continue

            if "\\lib\\threading.py" in path:
                continue

            if "\\Lib\\contextlib.py" in path:
                continue

            yield frame

    def _file(self) -> str:
        from os.path import basename
        from inspect import stack

        _stack = self._stack(stack())

        for frame in _stack:

            if '\\site-packages\\philh_myftp_biz\\' in frame.filename:
                continue
    
            name = basename(frame.filename)
            line = frame.lineno
            
            return f'{name}:{line}'
        
        return ''

    def format(self,
        record: '__LogRecord'
    ) -> str:
        from .text import recode
        from .time import now
        from .db import Color
        
        # Ignore records from other modules
        if record.name != 'root':
            return ''

        #===============================================

        n = now()

        TIME = n.stamp(format='%y/%m/%d %H:%M:%S') + f'.{n.centisecond:02d}'

        FILE = self._file()

        LEVEL, COLOR = self.table[record.levelno]
        COLOR = Color.values[COLOR]

        MESS = self._message(record)

        TRACE = self._traceback(record)

        #===============================================
        # output

        try:
            
            # Write to the logfile
            with self._wfile.open('a') as f:

                line = f"\n{TIME} {FILE} {LEVEL}\n{MESS}\n{TRACE}"
                
                f.write(recode(line))
        
        except OSError:
            pass

        #===============================================

        if VERBOSE or (record.levelno > 10):

            # Return a string to be printed to the terminal
            line = f"\n{COLOR}\033[1m{TIME} {FILE} {LEVEL}\033[22m\n{MESS}\033[0m\n{TRACE}"

            return recode(line)
        
        else:
            return ''
    
        #===============================================

#================================================================

class _StreamHandler(__StreamHandler):
     
    def __init__(self) -> None:
        from sys import stdout

        super().__init__(stream=stdout)

        # Allow all messages
        self.setLevel(level=10)

        self.setFormatter(fmt=_Formatter())
        
        # No New Line
        self.terminator = ''

#================================================================

__basicConfig(
    level = 10,
    handlers = [_StreamHandler()]
)

#================================================================