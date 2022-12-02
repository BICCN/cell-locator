# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sphinx_rtd_theme
import os
import sys

sys.path.insert(0, os.path.abspath('../cell-locator-cli/src'))


# -- Project information -----------------------------------------------------

project = 'Cell Locator'
copyright = '2021, Allen Institute for Brain Science, Kitware'
author = 'Allen Institute for Brain Science, Kitware'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'notfound.extension',  # Show a better 404 page when an invalid address is entered
    'sphinx_rtd_theme',
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinxcontrib.autoprogram',
]

myst_enable_extensions = [
    "colon_fence",  # Allow code fence using ::: (see https://myst-parser.readthedocs.io/en/latest/using/syntax-optional.html#syntax-colon-fence)
    "html_image", # Allow using isolated img tags (i.e. not wrapped in any other HTML) to specify attributes like width.
    "linkify",  # Allow automatic creation of links from URLs (it is sufficient to write https://google.com instead of <https://google.com>)
]

myst_heading_anchors = 3

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
