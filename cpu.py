#!/usr/bin/env python3
"""
LC-3 implementation.
"""
import sys
import array

MEMORY_MAX = 1 << 16 # 65,536
MEMORY = array.array('H', [0 for i in range(MEMORY_MAX)])

MR_KBSR = 0xFE00
MR_KBDR = 0xFE02

START = 0x3000

REG = {
    "R0": 0,
    "R1": 0,
    "R2": 0,
    "R3": 0,
    "R4": 0,
    "R5": 0,
    "R6": 0,
    'R7': 0,
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

def memory_write(address, value):
    MEMORY[address] = value


def memory_read(address):
    pass
        

def update_flags(register):
    if REG[register] == 0:
        REG["R_COND"] = FLAG["FL_ZRO"]
    elif REG[register] >> 15:
        REG["R_COND"] = FLAG["FL_NEG"]
    else:
        REG["R_COND"] = FLAG["FL_POS"]


def sign_extend(instruction, bit_size):
    if (instruction >> (bit_size - 1)) & 1:
        instruction |= (0xFFFF << bit_size)
    return instruction


def BRANCH(instruction):
    pass


def ADD(instruction):
    destination_register_code = (instruction >> 9) & 0x7 # move over 9 bits, then compare with 0x7 to extract the 3 rightmost bits
    operand_register_1_code = (instruction >> 6) & 0x7
    imm5_flag = (instruction >> 5) & 0x1 # move over five bits, then compare with 0x1 to extract the rightmost bit which is the indicator of imm5 mode

    if imm5_flag:
        imm5 = sign_extend(instruction & 0x1F, 5)
        REG[destination_register_code] = REG[operand_register_1_code] + imm5
        pass # add the number found in the last 5 bits
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


def JUMP_REG():
    pass


def BIT_AND():
    pass


def LOAD_REG(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    base_register_code = (instruction >> 6) & 0x7
    offset = sign_extend((instruction & 0x3F, 6))
    REG[destination_register_code] = memory_read(REG[base_register_code] + offset)
    update_flags(destination_register_code)


def STORE_REG(instruction):
    source_register_code = (instruction >> 9) & 0x7
    base_register_code = (instruction >> 6) & 0x7
    offset = sign_extend((instruction & 0x3F), 6)
    destination_memory_address = REG[base_register_code] + offset
    memory_write(destination_memory_address, REG[source_register_code])
    pass


def RTI():
    pass


def BIT_NOT():
    pass


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
    pass


def LOAD_EFFECTIVE_ADDRESS(instruction):
    destination_register_code = (instruction >> 9) & 0x7
    pc_offset = sign_extend(instruction & 0x1FF, 9)
    REG[destination_register_code] = REG["R_PC"] + pc_offset
    update_flags(destination_register_code) 


def TRAP():
    pass


def main():
    # load arguments, read data into memory
    # setup
    REG["R_COND"] = FLAG["FL_ZRO"]          # set condition flag to zero at start
    REG["R_PC"] = START                     # set start position to START (0x3000)
    
    while True:
        instruction = read_memory(REG["R_PC"])  # read first instruction at START counter position
        REG["R_PC"] += 1                        # add 1 to counter register to proceed to next instruction on next loop
        current_opcode = instruction >> 12      # get first 4 bits, which is the opcode
        
        # match opcode and execute instruction
        match current_opcode:
            case OPCODE.get("BR"):      # 0
                BRANCH()
            case OPCODE.get("ADD"):     # 1
                ADD(instruction)
            case OPCODE.get("LD"):      # 2
                LOAD()
            case OPCODE.get("ST"):      # 3
                STORE()
            case OPCODE.get("JSR"):     # 4
                JUMP_REG()
            case OPCODE.get("AND"):     # 5
                BIT_AND()
            case OPCODE.get("LDR"):     # 6
                LOAD_REG()
            case OPCODE.get("STR"):     # 7
                STORE_REG()
            case OPCODE.get("RTI"):     # 8
                RTI()
            case OPCODE.get("NOT"):     # 9
                BIT_NOT()
            case OPCODE.get("LDI"):     # 10
                LOAD_INDIRECT()
            case OPCODE.get("STI"):     # 11
                STORE_INDIRECT()
            case OPCODE.get("JMP"):     # 12
                JUMP()
            case OPCODE.get("RES"):     # 13
                RES()
            case OPCODE.get("LEA"):     # 14
                LOAD_EFFECTIVE_ADDRESS()
            case OPCODE.get("TRAP"):    # 15
                TRAP()
            case _:
                print("No opcode caught.")
                sys.exit()


if __name__ == "__main__":
    main()
    




