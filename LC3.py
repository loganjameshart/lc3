#!/usr/bin/env python3
"""
LC-3 implementation.
Source tutorial: https://www.jmeiners.com/lc3-vm/
"""


import sys
import array
import msvcrt
from string import printable


""" *** ----- HARDWARE EMULATION ----- *** """


MEMORY_MAX = 1 << 16  # 65,536
MEMORY = array.array("H", [0] * MEMORY_MAX)

MR_KBSR = 0xFE00
MR_KBDR = 0xFE02

START_INDEX = 0x3000

TRAP_GETC_ADDR = 0x20
TRAP_OUT_ADDR = 0x21
TRAP_PUTS_ADDR = 0x22
TRAP_IN_ADDR = 0x23
TRAP_PUTSP_ADDR = 0x24
TRAP_HALT_ADDR = 0x25

REG = {
    0 : 0,
    1 : 0,
    2 : 0,
    3 : 0,
    4 : 0,
    5 : 0,
    6 : 0,
    7 : 0,
    "R_PC": 0,
    "R_COND": 0,
    "R_COUNT": 0,
}


OPCODE = {
    "BR" : 0,  # branch
    "ADD": 1,  # add
    "LD" : 2,  # load
    "ST" : 3,  # store
    "JSR": 4,  # jump register
    "AND": 5,  # bitwise and
    "LDR": 6,  # load register
    "STR": 7,  # store register
    "RTI": 8,  # unused
    "NOT": 9,  # bitwise not
    "LDI": 10,  # load indirect
    "STI": 11,  # store indirect
    "JMP": 12,  # jump
    "RES": 13,  # reserved (unused)
    "LEA": 14,  # load effective address
    "TRAP": 15,  # execute trap
}


FLAG = {
    "FL_POS": 1 << 0,
    "FL_ZRO": 1 << 1,
    "FL_NEG": 1 << 2  
}


""" *** ----- FUNCTIONALITY IMPLEMENTATION ----- *** """


def load_file(file_path):
    """Loads file into program's requested start location."""
    global MEMORY
    with open(file_path, "rb") as input_file:
        data = input_file.read()
        temp_array = array.array('H')
        temp_array.frombytes(data)
        temp_array.byteswap()  # change endianness NOW to get correct address
        origin = temp_array[0] # first 16 bits are start address 
        for item in temp_array:
            MEMORY.insert(origin, item)
            origin += 1

    del temp_array
    del MEMORY[MEMORY_MAX:] # cleanup and return to memory limit



def memory_write(address, value):
    """Writes value to particular memory address."""
    MEMORY[address] = value


def memory_read(address):
    """Reads value from particular memory address or keyboard memory."""
    if address == MR_KBDR:
        if not msvcrt.kbhit():
            MEMORY[MR_KBSR] = (1 << 15)
            MEMORY[MR_KBDR] = ord(msvcrt.getch())
    else: 
        MEMORY[MR_KBSR] = 0

    return MEMORY[address]


def update_flags(register):
    """Updates the Boolean Flag Register by comparing with register being queried."""
    if REG[register] == 0:
        REG["R_COND"] = FLAG["FL_ZRO"]
    elif REG[register] >> 15:
        REG["R_COND"] = FLAG["FL_NEG"]
    else:
        REG["R_COND"] = FLAG["FL_POS"]


def sign_extend(value, bits):
    """Sign extension implementation in Python."""
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


""" *** ----- OPERATION IMPLEMENTATION ----- *** """

"""
See https://www.jmeiners.com/lc3-vm/supplies/lc3-isa.pdf for descriptions of each operation.
"""


def BRANCH(instruction):
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    nzp_conditional_flag_bits = (instruction >> 9) & 0x7
    if REG["R_COND"] & nzp_conditional_flag_bits:
        REG["R_PC"] = REG["R_PC"] + pc_offset


def ADD(instruction):
    destination_register_code = (instruction >> 9) & 0x7  # move over 9 bits, then mask with 0x7 to extract the 3 rightmost bits
    operand_register_1_code = (instruction >> 6) & 0x7
    imm5_flag = (instruction >> 5) & 0x1  # move over five bits, then mask with 0x1 to extract the rightmost bit which is the indicator of imm5 mode

    if imm5_flag:
        imm5 = sign_extend(instruction & 0x1F, 5)
        REG[destination_register_code] = REG[operand_register_1_code] + imm5
    else:
        operand_register_2_code = (instruction & 0x7)  # get rightmost three bits, which is the second operand register per the ADD instruction's documentaion (SR2)
        REG[destination_register_code] = (REG[operand_register_1_code] + REG[operand_register_2_code])

    update_flags(destination_register_code)


def LOAD(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    REG[destination_register_code] = memory_read(REG["R_PC"] + pc_offset)
    update_flags(destination_register_code)


def STORE(instruction):
    source_register_code = (instruction >> 9) & 0x7
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    destination_memory_address = REG["R_PC"] + pc_offset
    memory_write(destination_memory_address, REG[source_register_code])


def JUMP_REG(instruction):
    REG[7] = REG["R_PC"]
    bit_flag = (instruction >> 11) & 1
    if bit_flag == 0:
        subroutine_address = (instruction >> 6) & 0x7
        REG["R_PC"] = REG[subroutine_address]
    else:
        pc_offset = sign_extend(instruction & 0x7FF, 11)
        REG["R_PC"] = pc_offset + REG["R_PC"]


def BIT_AND(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    first_source_register_code = (instruction >> 6) & 0x7
    bit_flag = (instruction >> 5) & 0x1
    if bit_flag == 0:
        second_source_register_code = instruction & 0x7
        REG[destination_register_code] = (REG[first_source_register_code] & REG[second_source_register_code])
    else:
        imm5 = sign_extend(instruction & 0x1F, 5)
        REG[destination_register_code] = REG[first_source_register_code] & imm5


def LOAD_REG(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    base_register_code = (instruction >> 6) & 0x7
    offset = sign_extend((instruction & 0x3F), 6)
    REG[destination_register_code] = memory_read(REG[base_register_code] + offset)
    update_flags(destination_register_code)


# not currently working - issue with unsigned int
def STORE_REG(instruction):
    source_register_code = (instruction >> 9) & 0x7
    base_register_code = (instruction >> 6) & 0x7
    offset = sign_extend(instruction & 0x3F, 6)
    destination_memory_address = REG[base_register_code] + offset
    memory_write(destination_memory_address, REG[source_register_code])


def RTI():
    """Unused."""
    pass


def BIT_NOT(instruction):
    source_register_code = (instruction >> 6) & 0x7
    destination_register_code = (instruction >> 9) & 0x7
    REG[destination_register_code] = ~REG[source_register_code]
    update_flags(destination_register_code)


def LOAD_INDIRECT(instruction):
    destination_register = (instruction >> 9) & 0x7
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    indirect_memory_address = REG["R_PC"] + pc_offset
    direct_memory_address = memory_read(indirect_memory_address)
    REG[destination_register] = memory_read(direct_memory_address)
    update_flags(REG[destination_register])


def STORE_INDIRECT(instruction):
    source_register_code = (instruction >> 9) & 0x7
    pc_offset = sign_extend((instruction & 0x1FF, 9))
    indirect_memory_address = pc_offset + REG["R_PC"]
    direct_memory_address = memory_read(indirect_memory_address)
    memory_write(direct_memory_address, REG[source_register_code])


def JUMP(instruction):
    base_register = (instruction >> 6) & 0x7
    REG["R_PC"] = REG[base_register]


def RES():
    """Unused."""
    pass


def LOAD_EFFECTIVE_ADDRESS(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    REG[destination_register_code] = REG["R_PC"] + pc_offset
    update_flags(destination_register_code)


""" *** ----- TRAP SUB-OPERATIONS IMPLEMENTATION ----- *** """


def TRAP_GETC_FUNC():
    REG[0] = ord(sys.stdin.read(1))
    update_flags(0)


def TRAP_OUT_FUNC():
    print(chr(REG[0]))
    sys.stdout.flush()


def TRAP_PUTS_FUNC():
    base_address = REG[0]
    index = 0
    while True:
        try:
            character = MEMORY[base_address + index]
            if chr(character) not in printable:  # basic test for Hello World, need to improve
                index += 1
                continue
            else:
                print(chr(character), end="")
                index += 1
                continue
        except IndexError:
            break

    sys.stdout.flush()


def TRAP_IN_FUNC():
    while True:
        character = input("> Please enter a single character: ")
        if len(character) > 1:
            continue
        else:
            break
    REG[0] = ord(character)
    update_flags(0)


def TRAP_PUTSP_FUNC():
    character = MEMORY + REG[0]
    while character:
        char1 = character & 0xFF
        print(char1)
        char2 = character >> 8
        print(char2, end="")
        character += 1
    sys.stdout.flush()


def TRAP_HALT_FUNC():
    print("\n--- HALT ---\n")
    sys.exit()


def TRAP(instruction):
    REG[7] = REG["R_PC"]
    trap_vector = instruction & 0xFF
    if trap_vector == TRAP_GETC_ADDR:
        TRAP_GETC_FUNC()
    elif trap_vector == TRAP_OUT_ADDR:
        TRAP_OUT_FUNC()
    elif trap_vector == TRAP_PUTS_ADDR:
        TRAP_PUTS_FUNC()
    elif trap_vector == TRAP_IN_ADDR:
        TRAP_IN_FUNC()
    elif trap_vector == TRAP_PUTSP_ADDR:
        TRAP_PUTSP_FUNC()
    elif trap_vector == TRAP_HALT_ADDR:
        TRAP_HALT_FUNC()
    else:
        print("Bad trapcode.")


""" *** ----- MAIN EXECUTION LOOP ----- *** """


def main():
    if len(sys.argv) < 2:
        print("ERROR: No file found.\n> Input a file in the format 'python3 LC3.py [file_path]\n")
        sys.exit(1)
    else:
        REG["R_COND"] = FLAG["FL_ZRO"]  # set condition flag to zero at start
        REG["R_PC"] = START_INDEX  # set start position to START (0x3000)
        load_file(sys.argv[1])

        while True:
            instruction = memory_read(REG["R_PC"])
            REG["R_PC"] += 1
            current_opcode = instruction >> 12
            print(f"Count: {REG['R_PC']}\t Instruction: {bin(instruction)}")

            if current_opcode == OPCODE["BR"]:  # 0
                BRANCH(instruction)

            elif current_opcode == OPCODE["ADD"]:  # 1
                ADD(instruction)

            elif current_opcode == OPCODE["LD"]:  # 2
                LOAD(instruction)

            elif current_opcode == OPCODE["ST"]:  # 3
                STORE(instruction)

            elif current_opcode == OPCODE["JSR"]:  # 4
                JUMP_REG(instruction)

            elif current_opcode == OPCODE["AND"]:  # 5
                BIT_AND(instruction)

            elif current_opcode == OPCODE["LDR"]:  # 6
                LOAD_REG(instruction)

            elif current_opcode == OPCODE["STR"]:  # 7
                STORE_REG(instruction)

            elif current_opcode == OPCODE["RTI"]:  # 8
                RTI(instruction)

            elif current_opcode == OPCODE["NOT"]:  # 9
                BIT_NOT(instruction)

            elif current_opcode == OPCODE["LDI"]:  # 10
                LOAD_INDIRECT(instruction)

            elif current_opcode == OPCODE["STI"]:  # 11
                STORE_INDIRECT(instruction)

            elif current_opcode == OPCODE["JMP"]:  # 12
                JUMP(instruction)

            elif current_opcode == OPCODE["RES"]:  # 13
                RES(instruction)

            elif current_opcode == OPCODE["LEA"]:  # 14
                LOAD_EFFECTIVE_ADDRESS(instruction)

            elif current_opcode == OPCODE["TRAP"]:  # 15
                TRAP(instruction)

            else:
                print("No opcode caught.")
                sys.exit(1)


if __name__ == "__main__":
    main()

