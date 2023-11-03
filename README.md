# Python LC-3

This project is an implementation of the LC-3 (Little Computer 3) architecture in Python. LC-3 is a simple, educational computer architecture used for teaching computer organization and assembly language programming.

## Overview

The LC-3 emulator is designed to execute LC-3 assembly programs and provide a basic understanding of how a computer's hardware and assembly language interact. It allows you to load and run LC-3 programs, as well as interact with them using various trap routines.

## Getting Started

To run this LC-3 emulator, follow these steps:

1. Clone or download this repository to your local machine.
2. Make sure you have Python 3 installed.
3. Open a terminal or command prompt and navigate to the project directory.
4. Execute the emulator by running the command:

   ```
   python3 LC3.py [your_lc3_program.obj]
   ```

   Replace `[your_lc3_program.obj]` with the path to your LC-3 program file in .obj format.

## LC-3 Operations

The emulator supports the following LC-3 operations:

- Branch (BR)
- Add (ADD)
- Load (LD)
- Store (ST)
- Jump Register (JSR)
- Bitwise AND (AND)
- Load Register (LDR)
- Store Register (STR)
- Bitwise NOT (NOT)
- Load Indirect (LDI)
- Store Indirect (STI)
- Jump (JMP)
- Load Effective Address (LEA)
- Trap (TRAP)

## File Loading

The emulator can load LC-3 program files (in .obj format) into memory at the specified location (0x3000 by default). The loaded program can be executed by running the emulator.

## Input and Output - TO DO

The LC-3 emulator will provide:

- Reading characters from the keyboard
- Printing characters to the console
- Reading and printing strings
- Halting program execution

## Debugger View - TO DO

I'd like to implement a quick GUI in Tkinter that:

- Allows you to step forwards and backwards in the program execution, one step at a time
- Displays program output in a separate window (as opposed to terminal)
- Provides functionality for loading .obj files from different areas (as opposed to roaming directories in the terminal)

## License

This LC-3 emulator is provided under the MIT License.

## Acknowledgments

This project was inspired by the LC-3 architecture and a tutorial provided by [jmeiners.com](https://www.jmeiners.com/lc3-vm/). Special thanks to the author for the valuable resources and documentation.
