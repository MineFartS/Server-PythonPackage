from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from .pc import Path

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

class PKL:
    """
    .PKL File
    """

    def __init__(self, path, default=None):
        from .pc import Path
        self.path = Path(path)
        self.default = default

    def read(self):
        """
        Read the data from the file
        """
        from dill import load
        
        try:
            with self.path.open('rb') as f:
                return load(f)
        except:
            return self.default

    def save(self, value) -> None:
        """
        Save data to the file
        """
        from dill import dump
        
        with self.path.open('wb') as f:
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

class JSON:
    """
    .JSON File
    """

    def __init__(self,
        path: 'Path',
        default = {}
    ):
        from .pc import Path

        self.path = Path(path)
        self.__default = default
    
    def read(self):
        """
        Read the contents of the json file
        """
        from json import load
        from .text import hex

        try:
            return load(self.path.open())
        except:
            return self.__default

    def save(self, data):
        """
        Save data to the json file
        """
        from json import dump
        from .text import hex

        dump(
            obj = data,
            fp = self.path.open('w'),
            indent = 3
        )

class INI:
    """
    .INI/.PROPERTIES File
    """

    def __init__(self, path:'Path', default=''):
        from .pc import Path

        self.path = Path(path)
        self.__default = default
    
    def __obj(self):
        from configobj import ConfigObj

        return ConfigObj(self.path.path)

    def read(self):
        try:
            return self.__obj().dict()
        except:
            return self.__default
    
    def save(self, data):

        config = self.__obj()

        for name in data:
            config[name] = data[name]

        config.write()

class YAML:
    """
    .YML/.YAML File
    """
    
    def __init__(self, path, default={}):
        from .pc import Path
        
        self.path = Path(path)
        self.__default = default
    
    def read(self):
        """
        Read the yaml file
        """
        from yaml import safe_load

        try:

            with self.path.open() as f:
                data = safe_load(f)

            if data is None:
                return self.__default
            else:
                return data

        except:
            return self.__default
    
    def save(self, data):
        """
        Save data to the yaml file
        """
        from yaml import dump

        with self.path.open('w') as file:
            dump(data, file, default_flow_style=False, sort_keys=False)

class TXT:
    """
    .TXT File
    """

    def __init__(self, path, default=''):
        from .pc import Path
        
        self.path = Path(path)
        self.__default = default
    
    def read(self):
        """
        Read data from the txt file
        """
        try:
            self.path.open('r').read()
        except:
            return self.__default
    
    def save(self, data) -> None:
        """
        Save data to the txt file
        """
        self.path.open('w').write(str(data))

class ZIP:
    """
    .ZIP File
    """

    def __init__(self, zipfile:'Path'):
        from zipfile import ZipFile
        from .pc import Path

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
        from .pc import warn

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

class CSV:
    """
    .CSV File
    """

    def __init__(self, path, default=''):
        from .pc import Path
        
        self.path = Path(path)
        self.__default = default

    def read(self):
        """
        Read data from the csv file
        """
        from csv import reader

        try:
            with self.path.open() as csvfile:
                return reader(csvfile)
        except:
            return self.__default

    def save(self, data) -> None:
        """
        Save data to the csv file
        """
        from csv import writer

        with self.path.open('w') as csvfile:
            writer(csvfile).writerows(data)

class TOML:
    """
    .TOML File
    """

    def __init__(self, path, default=''):
        from .pc import Path
        
        self.path = Path(path)
        self.__default = default

    def read(self):
        """
        Read data from the toml file
        """
        from toml import load

        try:
            with self.path.open() as f:
                return load(f)
        except:
            return self.__default
        
    def save(self, data) -> None:
        """
        Save data to the toml file
        """
        from tomli_w import dump

        with self.path.open('wb') as f:
            dump(data, f, indent=2)
