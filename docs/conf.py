import sys
from datetime import datetime

# Do not touch these. They use the local prawcore over the global prawcore.
sys.path.insert(0, ".")
sys.path.insert(1, "..")

from prawcore import __version__

always_use_bars_union = True
autodoc_typehints = "description"
copyright = datetime.today().strftime("%Y, Bryce Boe")
exclude_patterns = ["_build"]
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]
html_theme = "furo"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/stable/", None),
}
nitpicky = True
project = "prawcore"
release = __version__
version = ".".join(__version__.split(".", 2)[:2])
