from logging import basicConfig, StreamHandler, LogRecord, Formatter
from functools import cached_property
from sys import argv, stdout

VERBOSE: bool = (len({'-v', '--verbose'} & set(argv)) >= 1)

HELP: bool = (len({'-h', '--help'} & set(argv)) >= 1)

class CustomFormatter(Formatter):

    def __init__(self) -> None:
        from .pc import pycache
        from time import time
        from os import path

        super().__init__()

        self.file = pycache.child(f'{path.basename(argv[0])} - {time():.0f}.log')

    @cached_property
    def _wfile(self):
        return self.file.open('w')

    def format(self,
        record: LogRecord
    ) -> str:
        from traceback import print_exception
        from .classtools import stringify
        from io import StringIO
        from .db import Color
        from .time import now

        #===============================================

        # If the record is from a different module
        if record.name != 'root':

            # Do Nothing
            return ''

        #===============================================
        # PARSE: TRACE

        _tb = StringIO()

        # If an exception is passed
        if record.exc_info:

            # Store the exception string
            print_exception(*record.exc_info, file=_tb)

            _tb.write('\n')

        TRACE = _tb.getvalue()

        #===============================================
        # PARSE: LEVEL & COLOR

        match record.levelno:

            case 10:

                LEVEL = 'VERB'

                if '\\Lib\\site-packages\\philh_myftp_biz\\' in record.pathname:
                    COLOR = Color.values['GRAY']
                else:
                    COLOR = Color.values['WHITE']
            
            case 20: 
                COLOR = Color.values['WHITE']
                LEVEL = 'INFO'
            
            case 25: 
                COLOR = Color.values['YELLOW']
                LEVEL = 'MAIN'
            
            case 30: 
                COLOR = Color.values['YELLOW']
                LEVEL = 'WARN'
            
            case 40: 
                COLOR = Color.values['RED']
                LEVEL = 'FAIL'
            
            case 50: 
                COLOR = Color.values['MAGENTA']
                LEVEL = 'CRIT'

            case _: raise KeyError()

        #===============================================
        # PARSE: MESS

        if isinstance(record.msg, str):
            MESS = record.msg
        else:
            MESS = stringify(record.msg)

        #===============================================
        # PARSE: TIME

        n = now()

        TIME = n.stamp(format='%y-%m-%d %H-%M-%S') + f'.{n.centisecond}'

        #===============================================
        # PARSE: FILE

        FILE = f'{record.filename}:{record.lineno}'

        #===============================================
        # output

        # Write to the logfile
        self._wfile.write(f"\n{TIME} {FILE} {LEVEL}\n{MESS}\n{TRACE}")
        
        # Return a string to be printed to the terminal
        return f"\n{COLOR}\033[1m{TIME} {FILE} {LEVEL}\033[22m\n{MESS}\033[0m\n{TRACE}"
    
        #===============================================

class CustomStreamHandler(StreamHandler):
     
    def __init__(self) -> None:

        super().__init__(stream=stdout)

        # Allow all messages
        self.setLevel(level=10)

        self.setFormatter(fmt=CustomFormatter())
        
        # No New Line
        self.terminator = ''

basicConfig(
    level = (10 if VERBOSE else 20),
    handlers = [CustomStreamHandler()]
)
