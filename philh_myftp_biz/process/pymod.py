from ..functools import force_in_types
from .SysTask import SysTask, rscan
from ..pc.Path import Path

class PyModule(SysTask):

    @force_in_types
    def __init__(self, path: Path):
        self.cwd = path.parent
        self.name = path.name

    @property
    def _main(self):
        from ..array import is_sublist

        sublist = ['-m', self.name]

        for proc in rscan():
            if (proc.cwd == self.cwd) and is_sublist(sublist, proc.cmdline):
                return proc

def modscan():
    for proc in rscan():

        if (proc.name() == 'python.exe') and ('-m' in proc.cmdline):

            name = proc.cmdline[ proc.cmdline.index('-m') + 1 ]
            mdir = proc.cwd.child(name)

            yield PyModule(mdir)

