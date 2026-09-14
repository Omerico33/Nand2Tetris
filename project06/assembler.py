#!/usr/bin/env python3
import sys

def is_int(s):
    return len(s) > 0 and (s[0] == '-' or s[0].isdigit()) and (len(s) == 1 or s[1:].isdigit())

def int_to_bin(n):
    res = ''
    while n > 0:
        res = str(n%2) + res
        n = n // 2
    return res

RAM_counter = 16
ROM_counter = 0
variables = {'SP':0, 'LCL':1, 'ARG':2, 'THIS':3, 'THAT':4,
         'R0':0, 'R1':1, 'R2':2, 'R3':3, 'R4':4, 'R5':5, 'R6':6, 'R7':7, 'R8':8, 'R9':9, 'R10':10,
         'R11':11, 'R12':12, 'R13':13, 'R14':14, 'R15':15,
         'SCREEN':16384,
         'KBD':24576}
labels = {}
comp_translator = {'0':'0101010', '1':'0111111', '-1':'0111010', 'D':'0001100', 'A':'0110000',
                   '!D':'0001101', '!A':'0110001', '-D':'0001111', '-A':'0110011', 'D+1':'0011111',
                   'A+1':'0110111', 'D-1':'0001110', 'A-1':'0110010', 'D+A':'0000010', 'D-A':'0010011',
                   'A-D':'0000111', 'D&A':'0000000', 'D|A':'0010101',
                   'M':'1110000', '!M':'1110001', '-M':'1110011', 'M+1':'1110111', 'M-1':'1110010',
                   'D+M':'1000010', 'D-M':'1010011', 'M-D':'1000111', 'D&M':'1000000', 'D|M':'1010101',
                   'A<<':'0100000', 'D<<':'0110000', 'M<<':'1100000', 'A>>':'0000000', 'D>>':'0010000',
                   'M>>':'1000000'}
jump_translator = {'JGT':'001', 'JEQ':'010', 'JGE':'011', 'JLT':'100', 'JNE':'101', 'JLE':'110',
                   'JMP':'111'}

f = open(sys.argv[1])
g = open(sys.argv[1][:-3] + 'hack', 'w')

lines = f.readlines()
f.close()

# Firstly map all the labels in the program.
i = 0
while i < len(lines):
    comment_index = lines[i].find('//')
    if comment_index != -1:
        lines[i] = lines[i][0:comment_index]
    lines[i] = lines[i].replace(' ', '').replace('\t', '').replace('\n', '')
    if len(lines[i]) > 1 and lines[i][0] == '(' and lines[i][-1] == ')':
        labels[lines[i][1:-1]] = ROM_counter
        lines.pop(i)
    else:
        if len(lines[i]) == 0:
            lines.pop(i)
        else:
            ROM_counter += 1
            i += 1

for i in range(len(lines)):
    new_line = '\n' if i < len(lines)-1 else ''
    # A-instruction:
    if lines[i][0] == '@':
        if is_int(lines[i][1:]):
            n = int(lines[i][1:])
        else:
            if lines[i][1:] in labels:
                n = labels[lines[i][1:]]
            else:
                if lines[i][1:] not in variables:
                    variables[lines[i][1:]] = RAM_counter
                    RAM_counter += 1
                n = variables[lines[i][1:]]
        bin_repr = int_to_bin(n)
        g.write(('0' * (16 - len(bin_repr))) + bin_repr + new_line)
    # C-instruction:
    else:
        sep1 = lines[i].find('=')
        sep2 = lines[i].find(';')
        if sep1 == -1:
            if sep2 == -1:
                comp_code = lines[i]
                jump = '000'
            else:
                comp_code = lines[i][:sep2]
                jump = jump_translator[lines[i][sep2+1:]]
            dest = '000'
        else:
            if sep2 == -1:
                comp_code = lines[i][sep1+1:]
                jump = '000'
            else:
                comp_code = lines[i][sep1+1:sep2]
                jump = jump_translator[lines[i][sep2+1:]]
            d1 = int('A' in lines[i][:sep1])
            d2 = int('D' in lines[i][:sep1])
            d3 = int('M' in lines[i][:sep1])
            dest = str(d1) + str(d2) + str(d3)
        comp = comp_translator[comp_code]
        op_code = '101' if (('<<' in comp_code) or ('>>' in comp_code)) else '111'
        g.write(op_code + comp + dest + jump + new_line)

g.close()