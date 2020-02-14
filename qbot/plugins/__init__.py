import importlib
from pathlib import Path

from qbot.utils import all_modules_in_directory

for module in all_modules_in_directory(Path(__file__).parent):
    importlib.import_module(f"{__name__}.{module}")
