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
    from .pc import Path, mkdir
    from tempfile import gettempdir

    SERVER = Path('E:/__temp__/')
    OS = Path(gettempdir() + '/philh_myftp_biz/')

    if SERVER.exists():
        dir = SERVER
    else:
        mkdir(OS)
        dir = OS

    if id:
        id = str(id)
    else:
        id = random(50)

    return dir.child(f'{name}-{id}.{ext}')

#========================================================

class _Template:

    def __init__(self,
        path: 'Path',
        default = ''
    ):
        self._default = default
        self._path    = path

    read = Callable[[], Any]
    """
    Read data from the file
    """
    
    save = Callable[[Any], None]
    """
    Save data to the file
    """

#========================================================

class XML:
    """
    .XML File
    """

    def __init__(self, path, title):
        from xml.etree import ElementTree
        from .pc import Path

        self.root = ElementTree(title)
        self.path = Path(path)

    def child(element, title:str, text:str):
        """
        
        """
        from xml.etree import ElementTree

        e = ElementTree.SubElement(element, title)
        e.text = text

        return e

    def save(self) -> None:
        """
        Save the current XML data to the file 
        """
        from xml.etree import ElementTree
        from bs4 import BeautifulSoup
        
        tree = ElementTree.ElementTree(self.root)
        
        tree.write(self.path.path, encoding="utf-8", xml_declaration=True)
        
        d = BeautifulSoup(self.path.open(), 'xml').prettify()

        self.path.write(d)

class PKL(_Template):
    """
    .PKL File
    """

    def read(self):
        from dill import load
        
        try:
            with self._path.open('rb') as f:
                return load(f)
        except:
            return self._default

    def save(self, value) -> None:
        from dill import dump
        
        with self._path.open('wb') as f:
            dump(value, f)

class VHDX:
    """
    .VHDX File
    """

    __via_with = False

    def __enter__(self):
        self.__via_with = True
        if not self.mount():
            return

    def __exit__(self, *_):
        if self.__via_with:
            self.dismount()

    def __init__(self,
        VHD: 'Path',
        MNT: 'Path',
        timeout: int = 30,
        ReadOnly: bool = False
    ):
        self.VHD = VHD
        self.MNT = MNT
        self.__timeout = timeout
        self.__readonly = ReadOnly

    def mount(self):
        from .__init__ import run

        run(
            args = [
                f'Mount-VHD',
                '-Path', self.VHD,
                '-NoDriveLetter',
                '-Passthru',
                {True:'-ReadOnly', False:''} [self.__readonly],
                '| Get-Disk | Get-Partition | Add-PartitionAccessPath',
                '-AccessPath', self.MNT
            ],
            wait = True,
            terminal = 'pscmd',
            hide = True,
            timeout = self.__timeout
        )

    def dismount(self):
        from .__init__ import run
        
        run(
            args = [
                f'Dismount-DiskImage',
                '-ImagePath', self.VHD
            ],
            wait = True,
            terminal = 'pscmd',
            hide = True,
            timeout = self.__timeout
        )

        # Delete the mounting directory
        self.MNT.delete()

class JSON(_Template):
    """
    .JSON File
    """

    def read(self):
        from json import load

        try:
            return load(self._path.open())
        except:
            return self._default

    def save(self, data):
        from json import dump

        dump(
            obj = data,
            fp = self._path.open('w'),
            indent = 3
        )

class INI(_Template):
    """
    .INI/.PROPERTIES File
    """
    
    def read(self):
        from configobj import ConfigObj
        
        try:
            obj = ConfigObj(str(self._path))
            return obj.dict()
        except:
            return self._default
    
    def save(self, data):
        from configobj import ConfigObj

        obj = ConfigObj(str(self._path))

        for name in data:
            obj[name] = data[name]

        obj.write()

class YAML(_Template):
    """
    .YML/.YAML File
    """
    
    def read(self):
        from yaml import safe_load

        try:

            with self._path.open() as f:
                data = safe_load(f)

            if data:
                return data
            else:
                return self._default

        except:
            return self._default
    
    def save(self, data):
        from yaml import dump

        dump(
            data = data, 
            stream = self._path.open('w'),
            default_flow_style = False,
            sort_keys = False
        )

class TXT(_Template):
    """
    .TXT File
    """
    
    def read(self):
        """
        Read data from the txt file
        """
        try:
            return self._path.open('r').read()
        except:
            return self._default
    
    def save(self, data):
        """
        Save data to the txt file
        """
        self._path.open('w').write(str(data))

class ZIP:
    """
    .ZIP File
    """

    def __init__(self, zipfile:'Path'):
        from zipfile import ZipFile

        self.zipfile = zipfile
        self.__zip = ZipFile(str(zipfile))
        self.files = self.__zip.namelist()

    def search(self, term:str) -> Generator[str]:
        """
        Search for files in the archive

        Ex: ZIP.search('test123') -> 'test123.json'
        """
        for f in self.files:
            if term in f:
                yield f

    def extractFile(self, file:str, path:'Path') -> None:
        """
        Extract a single file from the zip archive
        """
        from zipfile import BadZipFile
        from .terminal import warn

        folder = temp('extract', 'zip')

        try:
            self.__zip.extract(file, str(folder))

            for p in folder.descendants():
                if p.isfile():
                   p.move(path)
                   folder.delete()
                   break 

        except BadZipFile as e:
            warn(e)

    def extractAll(self,
        dst: 'Path',
        show_progress: bool = True
    ):
        """
        Extract all files from the zip archive
        """
        from tqdm import tqdm
        from .pc import mkdir

        mkdir(dst)

        if show_progress:
            
            with tqdm(total=len(self.files), unit=' file') as pbar:
                for file in self.files:
                    pbar.update(1)
                    self.extractFile(file, str(dst))

        else:
            self.__zip.extractall(str(dst))

class CSV(_Template):
    """
    .CSV File
    """

    def read(self):
        from csv import reader

        try:
            with self._path.open() as csvfile:
                return reader(csvfile)
        except:
            return self._default

    def save(self, data) -> None:
        from csv import writer

        with self._path.open('w') as csvfile:
            writer(csvfile).writerows(data)

class TOML(_Template):
    """
    .TOML File
    """

    def read(self):
        from toml import load

        try:
            with self._path.open() as f:
                return load(f)
        except:
            return self._default
        
    def save(self, data) -> None:
        from tomli_w import dump

        with self._path.open('wb') as f:
            dump(data, f, indent=2)

#========================================================