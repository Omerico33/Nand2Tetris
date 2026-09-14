#!/usr/bin/env python3
import sys
import os

# Push segment[i] to the stack, prog_name is used to differentiate between
# static variables.
def push(segment, i, prog_name):
    global pushD
    match segment:
        case 'constant':
            return '@' + i + '\nD=A\n' + pushD
        case 'local':
            return '@LCL\nD=M\n@' + i + '\nA=D+A\nD=M\n' + pushD
        case 'argument':
            return '@ARG\nD=M\n@' + i + '\nA=D+A\nD=M\n' + pushD
        case 'this':
            return '@THIS\nD=M\n@' + i + '\nA=D+A\nD=M\n' + pushD
        case 'that':
            return '@THAT\nD=M\n@' + i + '\nA=D+A\nD=M\n' + pushD
        case 'static':
            return '@' + prog_name + '.' + i + '\nD=M\n' + pushD
        case 'temp':
            return '@R' + str(5 + int(i)) + '\nD=M\n' + pushD
        case 'pointer':
            match i:
                case '0':
                    return '@THIS\nD=M\n' + pushD
                case '1':
                    return '@THAT\nD=M\n' + pushD

# Pop from the stack to segment[i], prog_name is used to differentiate between
# static variables.
def pop(segment, i, prog_name):
    global popD
    match segment:
        case 'local':
            return '@LCL\nD=M\n@' + i + '\nD=D+A\n' + popD
        case 'argument':
            return '@ARG\nD=M\n@' + i + '\nD=D+A\n' + popD
        case 'this':
            return '@THIS\nD=M\n@' + i + '\nD=D+A\n' + popD
        case 'that':
            return '@THAT\nD=M\n@' + i + '\nD=D+A\n' + popD
        case 'static':
            return '@SP\nM=M-1\nA=M\nD=M\n@' + prog_name + '.' + i + '\nM=D\n'
        case 'temp':
            return '@SP\nM=M-1\nA=M\nD=M\n@R' + str(5 + int(i)) + '\nM=D\n'
        case 'pointer':
            match i:
                case '0':
                    return '@SP\nM=M-1\nA=M\nD=M\n@THIS\nM=D\n'
                case '1':
                    return '@SP\nM=M-1\nA=M\nD=M\n@THAT\nM=D\n'

# Push the address in <segment> to the stack.
def push_address(segment):
    return '@' + segment + '\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'

def translate(filename):
    f = open(filename)
    lines = f.readlines()
    f.close()
    i = 0
    prog_name = filename[:-3].split('//')[-1]
    res = ''
    cur_func = prog_name
    labels_count = {'eq': 0, 'gt': 0, 'lt': 0}
    ret_label_counters = {}
    vm_labels = set()
    
    # Firstly, remove white spaces, empty lines, and comments.
    while i < len(lines):
        comment_index = lines[i].find('//')
        if comment_index != -1:
            lines[i] = lines[i][0:comment_index]
        lines[i] = lines[i].strip().split()
        if len(lines[i]) == 0:
            lines.pop(i)
        else:
            if lines[i][0] == 'label':
                vm_labels.add(lines[i][1])
            i += 1
    
    # The actual translation.
    for line in lines:
        # Stack commands.
        if line[0] in {'push', 'pop'}:
            if line[0] == 'push':
                res += push(line[1], line[2], prog_name)
            else:
                res += pop(line[1], line[2], prog_name)
        # Binary operations.
        if line[0] in {'add', 'sub', 'and', 'or'}:
            match line[0]:
                case 'add':
                    op = '+'
                case 'sub':
                    op = '-'
                case 'and':
                    op = '&'
                case 'or':
                    op = '|'
            if op == '-':
                res += '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nD=M' + op + 'D\n' + pushD
            else:
                res += '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nD=D' + op + 'M\n' + pushD
        # Unary operations.
        if line[0] in {'neg', 'not'}:
            if line[0] == 'neg':
                op = '-'
            else:
                op = '!'
            res += '@SP\nM=M-1\nA=M\nD=' + op + 'M\n' + pushD
        # Shift operations.
        if line[0] in {'shiftleft', 'shiftright'}:
            if line[0] == 'shiftleft':
                op = '<<'
            else:
                op = '>>'
            res += '@SP\nM=M-1\nA=M\nD=M' + op + '\n' + pushD
        # Logic commands.
        if line[0] in {'eq', 'gt', 'lt'}:
            while line[0].upper() + str(labels_count[line[0]]) in vm_labels:
                labels_count[line[0]] += 1
            label = prog_name + '.' + line[0].upper() + str(labels_count[line[0]])
            res += '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nD=M-D\n' + \
                    '@R13\nM=-1\n@' + label + '\nD;J' + line[0].upper() + '\n@R13\nM=0\n(' + label + ')\n' + \
                    '@R13\nD=M\n' + pushD
            labels_count[line[0]] += 1
        # Branching and functions commands.
        if line[0] in {'label', 'goto', 'if-goto', 'call', 'function', 'return'}:
            match line[0]:
                case 'label':
                    res += '(' + prog_name + '.' + line[1] + ')\n'
                case 'goto':
                    res += '@' + prog_name + '.' + line[1] + '\n0;JMP\n'
                case 'if-goto':
                    res += '@SP\nM=M-1\nA=M\nD=M\n@' + prog_name + '.' + line[1] + '\nD;JNE\n'
                case 'call':
                    ret_label = cur_func + '$ret'
                    if ret_label in ret_label_counters:
                        ret_label_counters[ret_label] += 1
                    else:
                        ret_label_counters[ret_label] = 0
                    while ret_label + str(ret_label_counters[ret_label]) in vm_labels:
                        ret_label_counters[ret_label] += 1
                    ret_label += str(ret_label_counters[ret_label])
                    res += push('constant', ret_label, prog_name) + \
                           push_address('LCL') + push_address('ARG') + \
                           push_address('THIS') + push_address('THAT') + \
                           '@SP\nD=M\n@' + str(5 + int(line[2])) + '\nD=D-A\n@ARG\nM=D\n' + \
                           '@SP\nD=M\n@LCL\nM=D\n' + \
                           '@' + line[1] + '\n0;JMP\n' + \
                           '(' + ret_label + ')\n'
                case 'function':
                    if prog_name + '.' in line[1]:
                        func_name = line[1]
                    else:
                        func_name = prog_name + '.' + line[1]
                    res += '(' + func_name + ')\n'
                    for i in range(int(line[2])):
                        res += push('constant', '0', prog_name)
                    cur_func = func_name
                case 'return':
                    res += '@LCL\nD=M\n@5\nA=D-A\nD=M\n@R13\nM=D\n' + \
                           '@SP\nM=M-1\nA=M\nD=M\n@ARG\nA=M\nM=D\n' +\
                           '@ARG\nD=M+1\n@SP\nM=D\n' + \
                           '@LCL\nA=M-1\nD=M\n@THAT\nM=D\n' + \
                           '@LCL\nD=M\n@2\nA=D-A\nD=M\n@THIS\nM=D\n' + \
                           '@LCL\nD=M\n@3\nA=D-A\nD=M\n@ARG\nM=D\n' + \
                           '@LCL\nD=M\n@4\nA=D-A\nD=M\n@LCL\nM=D\n' + \
                           '@R13\nA=M\n0;JMP\n'
                    cur_func = prog_name
    return res

# Push the value of the D register to the stack.
pushD = '@SP\nA=M\nM=D\n@SP\nM=M+1\n'
# Pop from the stack to the D register.
popD = '@R13\nM=D\n@SP\nM=M-1\nA=M\nD=M\n@R13\nA=M\nM=D\n'

# Check whether we're dealing with a single vm file or a folder with multiple
# vm files.
if len(sys.argv[1]) > 3 and sys.argv[1][-3:] == '.vm':
    g = open(sys.argv[1][:-2] + 'asm', 'w')
    asm_code = translate(sys.argv[1])
else:
    g = open(sys.argv[1] + '//' + sys.argv[1] + '.asm', 'w')
    asm_code = ''
    for filename in os.listdir(sys.argv[1]):
        if len(filename) > 3 and filename[-3:] == '.vm':
            asm_code += translate(sys.argv[1] + '//' + filename)
g.write(asm_code)
g.close()