# DC memory layout

## Register allocation

* `A`: scratch register; return value
* `B`: repeat counter
* `C`: pointer to stack frame
    * `[C+n+1]`: nth function argument
    * `[C+1]`: previous value of C
    * `[C]`: return address
    * `[C-n]`: nth local variable
* `X`: can be used for a local variable
* `Y`: can be used for a local variable
* `Z`: can be used for a local variable
* `I`: can be used for a local variable
* `J`: can be used for a local variable
* `O`: overflow of arithmetic instruction

## Memory

Program code starts at `0x0000`. Fields start immediately following the last instruction. `compilerservices.freememstart` is a constant pointing to the first unused word. The stack starts at `0xffff` and grows downwards.