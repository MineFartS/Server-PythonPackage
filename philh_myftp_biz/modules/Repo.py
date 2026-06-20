from ..pc import Path

class Repo:

    def __init__(self, path:Path) -> None:
        from git import Repo
        
        self._repo = Repo(str(path))

        self.add  = self._repo.index.add

        self.diff = self._repo.index.diff

        self.commit = self._repo.index.commit

        self.rm   = self._repo.git.rm

        self.head = self._repo.head

        self.init = self._repo.init

        self.new_tag = self._repo.create_tag

    def refresh(self):

        self.rm('-r', '--cached', '.')

        self.add(['.'])

    def push(self):

        remote = self._repo.remotes[0]

        remote.push()
