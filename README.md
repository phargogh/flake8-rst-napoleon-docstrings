# flake8-rst-napoleon-docstrings
Experimental: Flake8 linter for sphinx.ext.napoleon-parsed Google/Numpy-style docstrings

This flake8 plugin preprocesses your docstrings with napoleon before checking
RST correctness.

It is recommended to _also_ use `pip install flake8-docstrings`, as that will
lint other aspects of your docstring.  Consider using `flake8
--docstring-convention=google`.
