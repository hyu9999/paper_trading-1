import os
import sys
sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "PaperTrading"
copyright = "2020, pTraderTeam"
author = "pTraderTeam"
master_doc = "index"


# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.openapi"
]
templates_path = ["_templates"]
language = "zh_CN"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"
html_static_path = ["_static"]
htmlhelp_basename = "paper_trading"
