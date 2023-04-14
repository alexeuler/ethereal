import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import sphinx_rtd_theme

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Web3Cat"
copyright = "2022, Mono6"
author = "Mono6"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
]

autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "member-order": "bysource",
    "undoc-members": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "web3": ("https://web3py.readthedocs.io/en/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "bokeh": ("https://docs.bokeh.org/en/latest", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
# html_logo = ""
html_static_path = ["_static"]
