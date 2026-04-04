from logging import StreamHandler as __StreamHandler
from logging import basicConfig as __basicConfig
from logging import Formatter as __Formatter
from functools import cached_property
from typing import TYPE_CHECKING
from sys import argv as __argv

if TYPE_CHECKING:
    from logging import LogRecord as __LogRecord

VERBOSE: bool = (len({'-v', '--verbose'} & set(__argv)) >= 1)

HELP: bool = (len({'-h', '--help'} & set(__argv)) >= 1)

class CustomFormatter(__Formatter):

    @cached_property
    def _wfile(self):
        from .terminal import script_file
        from .pc import cache_dir
        from time import time

        file = cache_dir().child(f'{script_file().name}.{time():.0f}.log')

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
        record: '__LogRecord'
    ) -> str:
        from traceback import print_exception
        from io import StringIO

        _tb = StringIO()

        # If an exception is passed
        if record.exc_info:

            # Store the exception string
            print_exception(*record.exc_info, file=_tb)

            _tb.write('\n')

        return _tb.getvalue().strip()

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

    def _file(self) -> str:
        from os.path import basename
        from inspect import stack

        for frame in stack():

            path = frame.filename.lower()

            if '\\lib\\site-packages\\philh_myftp_biz\\' in path:
                continue

            if '\\lib\\logging\\' in path:
                continue

            if path.endswith("\\lib\\threading.py"):
                return '<Thread>'

            name = basename(path)
            line = frame.lineno
            
            return f'{name}:{line}'

        return ''

    def format(self,
        record: '__LogRecord'
    ) -> str:
        from .text import recode
        
        #===============================================
        
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
        
        # Return a string to be printed to the terminal
        line = f"\n{COLOR}\033[1m{TIME} {FILE} {LEVEL}\033[22m\n{MESS}\033[0m\n{TRACE}"

        return recode(line)
    
        #===============================================

class CustomStreamHandler(__StreamHandler):
     
    def __init__(self) -> None:
        from sys import stdout

        super().__init__(stream=stdout)

        # Allow all messages
        self.setLevel(level=10)

        self.setFormatter(fmt=CustomFormatter())
        
        # No New Line
        self.terminator = ''

__basicConfig(
    level = (10 if VERBOSE else 20),
    handlers = [CustomStreamHandler()]
)
