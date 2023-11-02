#!/usr/bin/env python3
"""
LC-3 implementation.
"""
import sys
import array

MEMORY_MAX = 1 << 16 # 65,536
MEMORY = array.array('H')

MR_KBSR = 0xFE00
MR_KBDR = 0xFE02

START = 0x3000

TRAP_GETC_ADDR = 0x20
TRAP_OUT_ADDR = 0x21
TRAP_PUTS_ADDR = 0x22
TRAP_IN_ADDR = 0x23
TRAP_PUTSP_ADDR = 0x24
TRAP_HALT_ADDR = 0x25



REG = {
    0   : 0,
    1   : 0,
    2   : 0,
    3   : 0,
    4   : 0,
    5   : 0,
    6   : 0,
    7   : 0,
    "R_PC": 0,
    "R_COND": 0,
    "R_COUNT": 0
}

# probably will refactor into constants to save processing time instead of dictionary lookups
OPCODE = {
    "BR"    :   0,  # branch
    "ADD"   :   1,  # add
    "LD"    :   2,  # load
    "ST"    :   3,  # store
    "JSR"   :   4,  # jump register
    "AND"   :   5,  # bitwise and
    "LDR"   :   6,  # load register
    "STR"   :   7,  # store register
    "RTI"   :   8,  # unused
    "NOT"   :   9,  # bitwise not
    "LDI"   :   10, # load indirect
    "STI"   :   11, # store indirect
    "JMP"   :   12, # jump
    "RES"   :   13, # reserved (unused)
    "LEA"   :   14, # load effective address
    "TRAP"  :   15  # execute trap
}

FLAG = {
    "FL_POS" : 1 << 0,  # P
    "FL_ZRO" : 1 << 1,  # Z
    "FL_NEG" : 1 << 2   # N
}


def load_file(file_path):
    with open(file_path, 'rb') as input_file:
        MEMORY.frombytes(input_file.read())
        print(MEMORY)
        MEMORY.byteswap()


def swap16(number):
    return (number << 8) | (number >> 8)


def memory_write(address, value):
    MEMORY[address] = value


def memory_read(address):
    return MEMORY[address]
    
        
def update_flags(register):
    if REG[register] == 0:
        REG["R_COND"] = FLAG["FL_ZRO"]
    elif REG[register] >> 15:
        REG["R_COND"] = FLAG["FL_NEG"]
    else:
        REG["R_COND"] = FLAG["FL_POS"]


def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

# def sign_extend(instruction, bit_size):
#    if (instruction >> (bit_size - 1)) & 1:
#        instruction |= (0xFFFF << bit_size)
#    return instruction


def BRANCH(instruction):
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    nzp_conditional_flag_bits = (instruction >> 9) & 0x7
    if (REG["R_COND"] & nzp_conditional_flag_bits):
        REG["R_PC"] = REG["R_PC"] + pc_offset


def ADD(instruction):
    destination_register_code = (instruction >> 9) & 0x7 # move over 9 bits, then compare with 0x7 to extract the 3 rightmost bits
    operand_register_1_code = (instruction >> 6) & 0x7
    imm5_flag = (instruction >> 5) & 0x1 # move over five bits, then compare with 0x1 to extract the rightmost bit which is the indicator of imm5 mode

    if imm5_flag:
        imm5 = sign_extend(instruction & 0x1F, 5)
        REG[destination_register_code] = REG[operand_register_1_code] + imm5
    else:
        operand_register_2_code = instruction & 0x7 # get rightmost three bits, which is the second operand register per the ADD instruction's documentaion (SR2)
        REG[destination_register_code] = REG[operand_register_1_code] + REG[operand_register_2_code]
    
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
        second_source_register_code = (instruction & 0x7)
        REG[destination_register_code] = REG[first_source_register_code] & REG[second_source_register_code] 
    else:
        imm5 = sign_extend(instruction & 0x1F, 5)
        REG[destination_register_code] = REG[first_source_register_code] & imm5


def LOAD_REG(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    base_register_code = (instruction >> 6) & 0x7
    offset = sign_extend((instruction & 0x3F, 6))
    REG[destination_register_code] = memory_read(REG[base_register_code] + offset)
    update_flags(destination_register_code)


def STORE_REG(instruction):
    source_register_code = (instruction >> 9) & 0x7
    base_register_code = (instruction >> 6) & 0x7
    offset = sign_extend(instruction & 0x3F, 6)
    print(REG[base_register_code])
    print(REG[source_register_code])
    print(offset)
    destination_memory_address = REG[base_register_code] + offset
    memory_write(destination_memory_address, REG[source_register_code])

     
def RTI():
    """Unused."""
    pass


def BIT_NOT(instruction):
    source_register_code = (instruction >> 6) & 0x7
    destination_register_code = (instruction >> 9) & 0x7
    REG[destination_register_code] = ~ REG[source_register_code]
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


def TRAP_GETC_FUNC():
    REG[0] = ord(input())
    update_flags(0)


def TRAP_OUT_FUNC():
    print(REG[0])


def TRAP_PUTS_FUNC():
    base_address = REG[0]
    index = 1
    while True:
        try:
            character = MEMORY[base_address + index]
            if chr(character) not in (r'abcdefghijklmnopqrstuvwxqz!HW \n'):
                index += 1
                continue
            else:
                print(chr(character), end='')
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
    update_flags("R0") # only inputting key since update_flags function


def TRAP_PUTSP_FUNC():
    character = MEMORY + REG[0]
    while character:
        char1 = character & 0xFF
        print(char1)
        char2 = character >> 8
        print(char2, end='')
        character += 1
    sys.stdout.flush()


def TRAP_HALT_FUNC():
    print("HALT")
    sys.exit()


def TRAP(instruction):
    REG[7] = REG["R_PC"]
    trap_vector = (instruction & 0xFF)
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

    

def main():
    # load arguments, read data into memory
    # setup
    REG["R_COND"] = FLAG["FL_ZRO"]          # set condition flag to zero at start
    REG["R_PC"] = 0                     # set start position to START (0x3000)
    load_file('hello.obj')

    while True:
        instruction = memory_read(REG["R_PC"])  # read first instruction at START counter position
        print(f"Count: {REG["R_PC"]} Instruction: {instruction}")
        REG["R_PC"] += 1                        # add 1 to counter register to proceed to next instruction on next loop
        current_opcode = instruction >> 12      # get first 4 bits, which is the opcode
        
        # match opcode and execute instruction
        if current_opcode == OPCODE.get("BR"):      # 0
            BRANCH(instruction)
            print('BRANCH')
        elif current_opcode == OPCODE.get("ADD"):     # 1
            ADD(instruction)
            print('ADD')
        elif current_opcode == OPCODE.get("LD"):      # 2
            LOAD(instruction)
            print('LOAD')
        elif current_opcode == OPCODE.get("ST"):      # 3
            STORE(instruction)
            print('STORE')
        elif current_opcode == OPCODE.get("JSR"):     # 4
            JUMP_REG(instruction)
            print('JUMP REG')
        elif current_opcode == OPCODE.get("AND"):     # 5
            BIT_AND(instruction)
            print('BIT AND')
        elif current_opcode == OPCODE.get("LDR"):     # 6
            LOAD_REG(instruction)
            print('LOAD REG')
        elif current_opcode == OPCODE.get("STR"):     # 7
            STORE_REG(instruction)
            print('STORE REG')
        elif current_opcode == OPCODE.get("RTI"):     # 8
            RTI(instruction)
            print('RTI')
        elif current_opcode == OPCODE.get("NOT"):     # 9
            BIT_NOT(instruction)
            print('BIT NOT')
        elif current_opcode == OPCODE.get("LDI"):     # 10
            LOAD_INDIRECT(instruction)
            print('LOAD INDIRECT')
        elif current_opcode == OPCODE.get("STI"):     # 11
            STORE_INDIRECT(instruction)
            print('STORE INDIRECT')
        elif current_opcode == OPCODE.get("JMP"):     # 12
            JUMP(instruction)
            print('JUMP')
        elif current_opcode == OPCODE.get("RES"):     # 13
            RES(instruction)
            print('RES')
        elif current_opcode == OPCODE.get("LEA"):     # 14
            LOAD_EFFECTIVE_ADDRESS(instruction)
            print('LEA')
        elif current_opcode == OPCODE.get("TRAP"):    # 15
            TRAP(instruction)
            print('\nTRAP')
        else:
            print("No opcode caught.")
            sys.exit()


if __name__ == "__main__":
    main()
    




