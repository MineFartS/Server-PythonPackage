from .SubProcess import TerminalMap, _TerminalMap
from ..pc.Path import Path

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

        TerminalMap['py']['args'] = [pyexe.path]
        TerminalMap['pym']['args'] = [pyexe.path, '-m']

    def disable(self): 
        TerminalMap['py']  = _TerminalMap['py']
        TerminalMap['pym'] = _TerminalMap['pym']
