**DCC v0.9**

DCC is a compiler for the DC language, targeting the [DCPU-16](http://0x10c.com/doc/dcpu-16.txt)

# Installation

DCC requires Python 2.7 and PLY. PLY can be installed using `easy_install ply`.

Optionally, you can add a symlink to dcc.py somewhere in your `PATH`. This allows you to use
dcc easily in any directory.

# Usage

Place your `.dc` source files (named according to the module name) in a single directory. Run `dcc.py` in that directory. The compiler will automatically compile referenced modules and generate output in `output.asm`.

# Credits

DCC is based on [SCC v0.3](https://github.com/zr40/scc).
