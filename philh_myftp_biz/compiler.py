from .functools.force_types import force_in_types
from .pc.Path import Path

@force_in_types
def generate_pyi(pyd:Path) -> None:
    from pybind11_stubgen import main
    from sys import path

    if not pyd.with_ext('pyi').exists:
        
        path.append(pyd.parent.path)

        main([pyd.name, '--output-dir', pyd.parent.path])

        path.remove(pyd.parent.path)
