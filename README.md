# Chip8-utilities


## compiler

- Usage `python compiler.py source hexfile`
- Compile an instruction file to an Chip8 rom
- Use instruction and register names from http://www.cs.columbia.edu/~sedwards/classes/2016/4840-spring/designs/Chip8.pdf
- Hex data can be directly written in 2 bytes group
- Single byte are followed by a 0 byte (`AF` is written `AF00`)
- Label can be defined by having a line start with `~` i.e. `~label`
- Label can be used by referencing them, replacing them with the previously marked memory address `JP ~label`)
- Single line comment `//`
- Assume rom is stored starting at address `0x200`
- Python 3 should also be supported
