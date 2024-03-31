# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

# noinspection PyUnresolvedReferences
import firmware.version as v  # noqa: E402

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

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
extensions = ['sphinx.ext.autosectionlabel', 'sphinx_rtd_theme']
# noinspection SpellCheckingInspection
latex_theme = "howto"
