import importlib
from pathlib import Path

from qbot.utils import import_all_modules

for module in import_all_modules(Path(__file__).parent):
    importlib.import_module(f"{__name__}.{module}")
