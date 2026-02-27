from logging import basicConfig, StreamHandler, LogRecord, Formatter
from sys import argv, stdout

VERBOSE: bool = (len({'-v', '--verbose'} & set(argv)) >= 1)

class CustomStreamHandler(StreamHandler):
    
    class CustomFormatter(Formatter):

        def format(self,
            record: LogRecord
        ) -> str:
            from traceback import print_exception
            from io import StringIO
            from .db import Color
            from .time import now

            # If the record is from a different module
            if record.name != 'root':

                # Do Nothing
                return ''
            
            # If the record is either from this module or the main execution
            else:

                Traceback = StringIO()

                # If an exception is passed
                if record.exc_info:

                    # Store the exception string
                    print_exception(*record.exc_info, file=Traceback)

                    Traceback.write('\n')

                # Get the current time
                n = now()

                # Parse the Terminal color value and the level name from the record
                match record.levelno:

                    case 10:

                        LEVEL = 'VERB'

                        if '\\Lib\\site-packages\\philh_myftp_biz\\' in record.pathname:
                            COLOR = 'GRAY'
                        else:
                            COLOR = 'WHITE'
                    
                    case 20: COLOR, LEVEL = ('WHITE',   'INFO')
                    
                    case 30: COLOR, LEVEL = ('YELLOW',  'WARN')
                    
                    case 40: COLOR, LEVEL = ('RED',     'FAIL')
                    
                    case 50: COLOR, LEVEL = ('MAGENTA', 'CRIT')

                    case _: raise KeyError()

                # Return a string to be printed to the terminal
                return \
                    f'\n{Color.values[COLOR]}\033[1m'+ \
                    f'{n.year-2000:02d}-{n.month:02d}-{n.day:02d} {n.hour:02d}-{n.minute:02d}-{n.second:02d}.{n.centisecond:02d} '+ \
                    f'{record.filename}:{record.lineno} '+ \
                    f'{LEVEL}\033[22m\n'+ \
                    f'{record.msg}\033[0m\n'+ \
                    Traceback.getvalue()
    
    def __init__(self):

        super().__init__(stdout)

        # Allow all messages
        self.setLevel(10)

        self.setFormatter(self.CustomFormatter())
        
        # No New Line
        self.terminator = ''

basicConfig(
    level = (10 if VERBOSE else 20),
    handlers = [CustomStreamHandler()]
)