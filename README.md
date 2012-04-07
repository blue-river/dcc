**DCC v0.9**

DCC is a compiler for the DC language, targeting the [DCPU-16](http://0x10c.com/doc/dcpu-16.txt)

# Installation instructions

DCC requires Python 2.7 and PLY.

If your system does not already have Python 2.7 installed, you can download the
Python 2.7 installer from [http://www.python.org/download/]().

If your Python distribution does not come with easy_install, you can download
easy_install from [http://pypi.python.org/pypi/setuptools]().

Windows users: after installing `easy_install`, add `C:\Python27\Scripts` (assuming
Python is installed in `C:\Python27`) to the `PATH`.

After installing Python and `easy_install`, install PLY using
`easy_install`:

    easy_install ply

Optionally, you can add the DCC directory to the PATH. This allows you to use
dcc.py easily in any directory.

# Credits
DCC is based on [SCC v0.3](https://github.com/zr40/scc).
