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
    from .pc import temp

    if id:
        id = str(id)
    else:
        id = random(50)

    return temp().child(f'{name}-{id}.{ext}')

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

    _read: Callable[[], Any]

    save = Callable[[Any], None]
    """Write data to the file"""

    def read(self):
        """Read data from the file"""

        if self.path.exists:

            value = self._read()

            if value:
                return value
            else:
                return self.default

    def _read_UTF8(self) -> bytes:

        with self.path.open() as f:
        
            raw: str = f.read()

            return raw.encode('utf-8')

#========================================================

class XML(_Template):
    """
    .XML File
    """

    def _read(self) -> dict:
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

    def _read(self):
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

    def _read(self):
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
    
    def _read(self):
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
    
    def _read(self):
        from yaml import safe_load

        return safe_load(self._read_UTF8())
    
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
    
    def _read(self):
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

        folder = temp('extract', 'zip')

        self._zip.extract(file, str(folder))

        for p in folder.descendants:
            
            if p.is_file:
                
                p.move(savepath)
                
                folder.delete()
                
                break 

    def extractAll(self,
        dst: 'Path',
        show_progress: bool = True
    ) -> None:
        """
        Extract all files from the zip archive
        """
        from tqdm import tqdm

        dst.mkdir()

        if show_progress:
            
            with tqdm(total=len(self.files), unit=' file') as pbar:
                
                for file in self.files():
                    
                    pbar.update(1)

                    self.extractFile(file, str(dst))

        else:
            self._zip.extractall(str(dst))

class CSV(_Template):
    """
    .CSV File
    """

    def _read(self):
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

    def _read(self):
        from toml import load

        with self.path.open() as f:
            return load(f)
        
    def save(self, data:dict) -> None:
        from tomli_w import dump

        with self.path.open('wb') as f:
            dump(data, f, indent=2)

#========================================================