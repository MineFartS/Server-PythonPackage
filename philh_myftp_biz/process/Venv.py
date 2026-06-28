from .SubProcess import TerminalMap
from ..pc.Path import Path
from sys import executable

pypaths = [
    "/Scripts/python.exe",
    "/python.exe"
]

class SubVenv(Path):
    """Set Venv for SubProcess"""

    def enable(self):

        pyexe = next(filter(
            lambda p: p.exists,
            [self.child(p) for p in pypaths]
        ))

        TerminalMap['py'] = [pyexe.path]
        TerminalMap['pym'] = [pyexe.path, '-m']

    def disable(self): 
        TerminalMap['py'] = [executable]
        TerminalMap['pym'] = [executable, '-m']
