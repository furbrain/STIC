# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import version as v
project = 'SAP6'
# noinspection PyShadowingBuiltins
copyright = '2023, Phil Underwood'
author = 'Phil Underwood'
release = v.get_sw_version()
version = v.get_sw_version()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
extensions = ['sphinx.ext.autosectionlabel']
# noinspection SpellCheckingInspection
latex_elements = {
    'extraclassoptions': 'openany,oneside'
}
