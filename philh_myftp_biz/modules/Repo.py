from ..pc import Path

class Repo:

    def __init__(self, path:Path) -> None:
        from git import Repo

        self.path = Path(path)
        
        self._repo = Repo(str(path))

        self.diff = self._repo.index.diff

        self.commit = self._repo.index.commit

        self.rm   = self._repo.git.rm

        self.head = self._repo.head

        self.init = self._repo.init

        self.new_tag = self._repo.create_tag

        self.REMOTE = self._repo.remotes[0]

        self.push = self.REMOTE.push

        self.reset = self._repo.git.reset
        """Unstage all files"""

    def refresh(self):

        self.rm('-r', '--cached', '.')

        self.add(['.'])

    def focus(self, path:str):

        # Reset the index to clear any manually staged files
        self.reset()

        # Stage only the specific subfolder
        self.add(path)

    def add(self, path:str):
        """Stage specific subfolder"""

        abs = self.path.child(path)

        self._repo.git.add(str(abs))

    @property
    def changes(self) -> int:
        return len(self.diff(self.head.commit))
    
    def update_submodules(self) -> None:
        self._repo.git.submodule('update', '--remote', '--recursive', '--init')
