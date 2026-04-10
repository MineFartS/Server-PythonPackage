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

from .num import MutInt

class _VERBOSE(MutInt):

    def __init__(self):
        super().__init__(None)
        self.resume()

    def pause(self):
        self.value = 0

    def resume(self):
        self.value = _arg('-v', '--verbose')

VERBOSE = _VERBOSE()

#================================================================

HELP: bool = _arg('-h', '--help')

#================================================================

class CustomFormatter(__Formatter):

    @cached_property
    def _wfile(self):
        from .terminal import script_file
        from .pc import loc
        from time import time

        file = loc.logs.child(f'{script_file().name}.{time():.0f}.log')

        file.open('w').close()

        return file
    
    def _levelname(self,
        record: '__LogRecord'
    ) -> str: # pyright: ignore[reportReturnType]
        
        match record.levelno: # pyright: ignore[reportMatchNotExhaustive]

            case 10:
                return 'VERB'

            case 20: 
                return 'INFO'
            
            case 25: 
                return 'MAIN'
            
            case 30: 
                return 'WARN'
            
            case 40: 
                return 'FAIL'
            
            case 50: 
                return 'CRIT'

    def _color(self,
        record: '__LogRecord'
    ) -> str: # pyright: ignore[reportReturnType]
        from .db import Color
        
        match record.levelno: # pyright: ignore[reportMatchNotExhaustive]

            case 10:

                if '\\Lib\\site-packages\\philh_myftp_biz\\' in record.pathname:
                    return Color.values['GRAY']
                else:
                    return Color.values['WHITE']
            
            case 20: 
                return Color.values['WHITE']
            
            case 25: 
                return Color.values['YELLOW']
            
            case 30: 
                return Color.values['YELLOW']
            
            case 40: 
                return Color.values['RED']
            
            case 50: 
                return Color.values['MAGENTA']

    def _traceback(self,
        record: __LogRecord
    ) -> str:
        from traceback import extract_tb

        if record.exc_info is None:
            return ''

        tb = extract_tb(record.exc_info[2])

        outp = []

        for frame in self._stack(tb):
            
            outp.append(f'File "{frame.filename}", line {frame.lineno}')
            
        outp += [str(record.exc_info).split('>, ')[1].split(', <')[0]]

        return "\n".join(outp).strip()

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

    def _timestamp(self) -> str:
        from .time import now
        
        n = now()

        return n.stamp(format='%y/%m/%d %H:%M:%S') + f'.{n.centisecond:02d}'

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
        
        # Ignore records from other modules
        if record.name != 'root':
            return ''

        #===============================================

        COLOR = self._color(record)

        TIME = self._timestamp()

        FILE = self._file()

        LEVEL = self._levelname(record)

        MESS = self._message(record)

        TRACE = self._traceback(record)

        #===============================================
        # output

        # Write to the logfile
        with self._wfile.open('a') as f:

            line = f"\n{TIME} {FILE} {LEVEL}\n{MESS}\n{TRACE}"
            
            f.write(recode(line))
        
        #===============================================

        if VERBOSE or (record.levelno > 10):

            # Return a string to be printed to the terminal
            line = f"\n{COLOR}\033[1m{TIME} {FILE} {LEVEL}\033[22m\n{MESS}\033[0m\n{TRACE}"

            return recode(line)
        
        else:
            return ''
    
        #===============================================

#================================================================

class CustomStreamHandler(__StreamHandler):
     
    def __init__(self) -> None:
        from sys import stdout

        super().__init__(stream=stdout)

        # Allow all messages
        self.setLevel(level=10)

        self.setFormatter(fmt=CustomFormatter())
        
        # No New Line
        self.terminator = ''

#================================================================

__basicConfig(
    level = 10,
    handlers = [CustomStreamHandler()]
)

#================================================================