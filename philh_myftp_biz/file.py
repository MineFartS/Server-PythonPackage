from typing import TYPE_CHECKING, Generator, Callable, Any

if TYPE_CHECKING:
    from .pc import Path

#========================================================

def temp(
    name: str = 'undefined',
    ext: str = 'ph',
    id: str = None
) -> 'Path':
    """
    Get a random path in the temporary directory
    """
    from .text import random
    from .pc import tempdir

    if id:
        id = str(id)
    else:
        id = random(50)

    return tempdir.child(f'{name}-{id}.{ext}')

#========================================================

class _Template:

    def __init__(self,
        path: 'Path',
        default: Any = None
    ) -> None:

        self.path    = path

        self.default = default

        # Make the parent dir of the output path
        path.parent.mkdir()

    parsed: Any

    save = Callable[[Any], None]
    """Write data to the file"""

    def read(self):
        """Read data from the file"""

        if self.path.exists:

            value = self.parsed

            if value:
                return value
            else:
                return self.default

    @property
    def raw(self) -> bytes:

        with self.path.open() as f:
        
            raw: str = f.read()

            return raw.encode('utf-8')

#========================================================

class XML(_Template):
    """
    .XML File
    """

    @property
    def parsed(self) -> dict:
        from xmltodict import parse

        with self.path.open() as f:

            return parse(f.read())

    def save(self,
        data: dict
    ) -> None:
        from xmltodict import unparse

        with self.path.open('w') as f:

            data = unparse(data, pretty=True)

            f.write(data)

class PKL(_Template):
    """
    .PKL File
    """

    @property
    def parsed(self):
        from dill import load
        
        with self.path.open('rb') as f:
            return load(f)

    def save(self,
        value: Any
    ) -> None:
        from dill import dump
        
        with self.path.open(mode='wb') as f:
            dump(obj=value, file=f)

class VHDX:
    """
    .VHDX File
    """

    def __init__(self,
        VHD: 'Path',
        MNT: 'Path',
        timeout: int = 30,
        readonly: bool = False
    ) -> None:
        
        self.VHD = VHD
        self.MNT = MNT
        
        self.timeout: int = timeout
        
        self.readonly: bool = readonly

    def mount(self) -> None:
        from .process import RunHidden

        RunHidden(
            args = [
                f'Mount-VHD',
                '-Path', self.VHD,
                '-NoDriveLetter',
                '-Passthru',
                ('-ReadOnly' if self.readonly else ''),
                '| Get-Disk | Get-Partition | Add-PartitionAccessPath',
                '-AccessPath', self.MNT
            ],
            terminal = 'ps',
            timeout = self.timeout
        )

    def dismount(self) -> None:
        from .process import RunHidden
        
        RunHidden(
            args = [
                f'Dismount-DiskImage',
                '-ImagePath', self.VHD
            ],
            terminal = 'ps',
            timeout = self.timeout
        )

        # Delete the mounting directory
        self.MNT.delete()

class JSON(_Template):
    """
    .JSON File
    """

    @property
    def parsed(self):
        from json import load

        return load(fp=self.path.open())

    def save(self, data: dict) -> None:
        from json import dump

        dump(
            obj = data,
            fp = self.path.open(mode='w'),
            indent = 3
        )

class INI(_Template):
    """
    .INI/.PROPERTIES File
    """
    
    @property
    def parsed(self):
        from configobj import ConfigObj
        
        return ConfigObj(str(self.path)).dict()
         
    def save(self, data:dict) -> None:
        from configobj import ConfigObj

        obj = ConfigObj(str(self.path))

        for name in data:
            obj[name] = data[name]

        obj.write()

class YAML(_Template):
    """
    .YML/.YAML File
    """
    
    @property
    def parsed(self):
        from yaml import safe_load

        return safe_load(self.raw)
    
    def save(self, data:dict) -> None:
        from yaml import dump

        dump(
            data = data, 
            stream = self.path.open(mode='w'),
            default_flow_style = False,
            sort_keys = False
        )

class TXT(_Template):
    """
    .TXT File
    """
    
    @property
    def parsed(self):
        """
        Read data from the txt file
        """
        return self.path.open(mode='r').read()
    
    def save(self, data:str) -> None:
        """
        Save data to the txt file
        """
        self.path.open(mode='w').write(str(data))

class ZIP:
    """
    .ZIP File
    """

    def __init__(self,
        path: 'Path'
    ) -> None:
        from zipfile import ZipFile

        self.path = path

        self._zip = ZipFile(str(path))
        
        self.files: Callable[[], list[str]] = self._zip.namelist

    def search(self,
        term: str
    ) -> Generator[str]:
        """
        Search for files in the archive

        Ex: ZIP.search('test123') -> 'test123.json'
        """

        for f in self.files():
            
            if term in f:
                
                yield f

    def extractFile(self,
        file: str, 
        savepath: 'Path'
    ) -> None:
        """
        Extract a single file from the zip archive
        """
        self._zip.extract(file, str(savepath))

    def extractAll(self,
        path: 'Path'
    ) -> None:
        """
        Extract all files from the zip archive
        """

        path.mkdir()

        self._zip.extractall(str(path))

class CSV(_Template):
    """
    .CSV File
    """

    @property
    def parsed(self):
        from csv import reader

        with self.path.open() as csvfile:
            return reader(csvfile)

    def save(self, data:list[list]) -> None:
        from csv import writer

        with self.path.open('w') as csvfile:
            writer(csvfile).writerows(data)

class TOML(_Template):
    """
    .TOML File
    """

    @property
    def parsed(self):
        from toml import load

        with self.path.open() as f:
            return load(f)
        
    def save(self, data:dict) -> None:
        from tomli_w import dump

        with self.path.open('wb') as f:
            dump(data, f, indent=2)

#========================================================