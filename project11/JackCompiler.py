#!/usr/bin/env python3
import sys
import builtins
import os

# The current token is a string i.f.f. it stars and ends with '"'.
def is_string(s):
    return len(s) > 0 and s[0] == '"' and s[-1] == '"'
# The current token is an identifier i.f.f. it is not a keyword, it doesn't
# start with a digit and all of its characters are either english letters,
# digits or underlines.
def is_identifier(s):
    if s == '' or s[0].isdigit() or s in keywords:
        return False
    for c in s:
        if not (48 <= ord(c) <= 57 or 65 <= ord(c) <= 90 or 97 <= ord(c) <= 122 or c == '_'):
            return False
    return True

def outside_string(line, i):
    if i == -1:
        return False
    left_quote = True
    right_quote = True
    j = i - 1
    while j > 0:
        if line[j] == '"':
            left_quote = False
            break
        j -= 1
    j = i + 1
    while j < len(line):
        if line[j] == '"':
            right_quote = False
            break
        j += 1
    return left_quote or right_quote

keywords = {'class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char',
            'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while',
            'return'}
symbols = {'{', '}', '[', ']', '(', ')', '.', ',', ';', '+', '-', '*', '/', '&', '|', '~', '>', '<', '=', '^', '#'}

# Converts a symbol to xml format.
symbol_to_xml = {}
for symbol in symbols:
    symbol_to_xml[symbol] = symbol
symbol_to_xml['>'] = '&gt;'
symbol_to_xml['<'] = '&lt;'
symbol_to_xml['&'] = '&amp;'

# Symbol tables.
symbol_indices = {'field' : {}, 'static' : {}, 'local' : {}, 'arg' : {}, 'class' : {}, 'subroutine' : {}}
symbol_types = {'field' : [], 'static' : [], 'local' : [], 'arg' : []}
index_counters = {'field' : 0, 'static' : 0, 'local' : 0, 'arg' : 0}
# Flags indicating if the compiler is inside a subroutine/method/constructor.
subroutine_flag = False
method_flag = False
constructor_flag = False
categories = ['static', 'field']
subroutine_categories = ['arg', 'local', 'static', 'field']
# The type of each subroutine (method/function/constructor).
subroutine_types = {}

# Converts variable type to the proper VM segment.
category_to_segment = {'field':'this', 'static':'static', 'local':'local', 'arg':'argument'}

# Converts an operation to the proper VM command/function call.
bin_ops_to_vm = {'+':'add', '-':'sub', '*':'call Math.multiply 2', '/':'call Math.divide 2',
                 '&':'and', '|':'or', '>':'gt', '<':'lt', '=':'eq'}
un_ops_to_vm = {'~':'not', '-':'neg', '^':'shiftleft', '#':'shiftright'}

current_class = None
class_size = {}

labels_counter = 0

class JackTokenizer:
    def __init__(self, filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        i = 0
        # Firstly get rid of all the comments in the code.
        while i < len(lines):
            comment_index = lines[i].find('//')
            if outside_string(lines[i], comment_index):
                lines[i] = lines[i][:comment_index]
            else:
                comment_start_index = lines[i].find('/*')
                if outside_string(lines[i], comment_start_index):
                    comment_end_index = lines[i].find('*/', comment_start_index)
                    if comment_end_index != -1:
                        lines[i] = lines[i][:comment_start_index] + lines[i][comment_end_index+2:]
                    else:
                        lines[i] = lines[i][:comment_start_index]
                        i += 1
                        while i < len(lines) and ('*/' not in lines[i]):
                            lines.pop(i)
                        comment_end_index = lines[i].find('*/')
                        lines[i] = lines[i][comment_end_index+2:]
                else:
                    comment_start_index = lines[i].find('/**')
                    if outside_string(lines[i], comment_start_index):
                        comment_end_index = lines[i].find('*/', comment_start_index)
                        if comment_end_index != -1:
                            lines[i] = lines[i][:comment_start_index] + lines[i][comment_end_index+2:]
                        else:
                            lines[i] = lines[i][:comment_start_index]
                            i += 1
                            while i < len(lines) and ('*/' not in lines[i]):
                                lines.pop(i)
                            comment_end_index = lines[i].find('*/')
                            lines[i] = lines[i][comment_end_index+2:]
            i += 1

        i = 0
        # Secondly deal with string symbols and white spaces.
        while i < len(lines):
            split_line = lines[i].split('"')
            lines[i] = []
            for j in range(len(split_line)):
                if j%2 == 0:
                    lines[i] += split_line[j].split()
                else:
                    lines[i] += ['"' + split_line[j] + '"']
            if len(lines[i]) == 0:
                lines.pop(i)
            else:
                i += 1

        # Concatenates the lines to get an array of the tokens.
        self.tokens = []
        for line in lines:
            self.tokens += line

        # Look up the symbols in the array and separate them as different tokens.
        i = 0
        while i < len(self.tokens):
            found_symbol = False
            if self.tokens[i][0] != '"':
                for symbol in symbols:
                    symbol_index = self.tokens[i].find(symbol)
                    if symbol_index != -1 and self.tokens[i] != symbol:
                        if symbol_index == 0:
                            self.tokens = self.tokens[:i] + \
                                          [symbol, self.tokens[i][symbol_index+1:]] + \
                                          self.tokens[i + 1:]
                        else:
                            if symbol_index == len(self.tokens[i]) - 1:
                                self.tokens = self.tokens[:i] + \
                                              [self.tokens[i][:symbol_index], symbol] + \
                                              self.tokens[i + 1:]
                            else:
                                self.tokens = self.tokens[:i] + \
                                [self.tokens[i][:symbol_index], symbol, self.tokens[i][symbol_index+1:]] + \
                                self.tokens[i+1:]
                        found_symbol = True
                        break
            if not found_symbol:
                i += 1

        self.cur_token = None

    def hasMoreTokens(self):
        return len(self.tokens) > 0

    def advance(self):
        self.cur_token = self.tokens.pop(0)

    def tokenType(self):
        if self.cur_token in keywords:
            return 'keyword'
        if self.cur_token in symbols:
            return 'symbol'
        if self.cur_token.isdigit():
            return 'intConstant'
        if is_string(self.cur_token):
            return 'stringConstant'
        if is_identifier(self.cur_token):
            return 'identifier'

    def getCurToken(self):
        return self.cur_token

class Class:
    """
    name (str) : Class name.
    components (list<Subroutine,ClassVarDec>) : The components of the class.
    """
    def __init__(self, tknzr):
        global current_class, class_size
        tknzr.advance()
        self.name = Identifier(tknzr.getCurToken(), 'class', None, False, None)
        current_class = tknzr.getCurToken()
        class_size[current_class] = 0
        self.components = []
        tknzr.advance()
        tknzr.advance()
        while tknzr.getCurToken() != '}':
            if tknzr.getCurToken() in {'constructor', 'function', 'method'}:
                self.components.append(Subroutine(tknzr))
            if tknzr.getCurToken() in {'field', 'static'}:
                self.components.append(ClassVarDec(tknzr))
                if self.components[-1].dec_type == 'field':
                    class_size[current_class] += len(self.components[-1].variables)

    def __str__(self):
        res = '<class>\n<keyword> class </keyword>\n' + str(self.name) + '<symbol> { </symbol>\n'
        for component in self.components:
            res += str(component)
        res += '<symbol> } </symbol>\n</class>\n'
        return res

    def compile(self):
        res = ''
        for component in self.components:
            if type(component) is Subroutine:
                res += component.compile()
        return res

class Subroutine:
    """
    func_typr (str) : constructor/function/method.
    ret_val (str) : int/char/boolean/void/<Object_Name>.
    name (str) : The name of the function.
    params (list<str>) : The names of the function parameters.
    types (list<str>) : The types of the function parameters.
    var_decs (list<VarDec>) : The variable declarations in the body of the function.
    statements (Statements) : The statements in the body of the function.
    """
    def __init__(self, tknzr):
        global symbol_indices, symbol_types, index_counters, subroutine_flag, method_flag, constructor_flag, subroutine_types
        symbol_indices['arg'] = {}
        symbol_indices['local'] = {}
        symbol_types['arg'] = []
        symbol_types['local'] = []
        index_counters['arg'] = 0
        index_counters['local'] = 0
        subroutine_flag = True
        self.func_type = tknzr.getCurToken()
        if self.func_type == 'method':
            method_flag = True
            symbol_indices['arg']['this'] = 0
            index_counters['arg'] = 1
        if self.func_type == 'constructor':
            constructor_flag = True
        tknzr.advance()
        if tknzr.getCurToken() in keywords:
            self.ret_val = tknzr.getCurToken()
        else:
            self.ret_val = Identifier(tknzr.getCurToken(), 'class', None, False, None)
        tknzr.advance()
        self.name = Identifier(tknzr.getCurToken(), 'subroutine', None, False, None)
        subroutine_types[tknzr.getCurToken()] = self.func_type
        tknzr.advance()
        tknzr.advance()
        self.params = []
        self.types = []
        while tknzr.getCurToken() != ')':
            if tknzr.getCurToken() in keywords:
                self.types.append(tknzr.getCurToken())
            else:
                self.types.append(Identifier(tknzr.getCurToken(), 'class', None, False, None))
            tknzr.advance()
            self.params.append(Identifier(tknzr.getCurToken(), 'arg', 'declared', False, self.types[-1]))
            tknzr.advance()
            if tknzr.getCurToken() == ',':
                tknzr.advance()
        tknzr.advance()
        tknzr.advance()
        self.var_decs = []
        self.local_size = 0
        while tknzr.getCurToken() == 'var':
            self.var_decs.append(VarDec(tknzr))
            self.local_size += len(self.var_decs[-1].variables)
        self.statements = Statements(tknzr)
        tknzr.advance()
        subroutine_flag = False
        method_flag = False
        constructor_flag = False

    def __str__(self):
        res = '<subroutineDec>\n<keyword> ' + self.func_type + ' </keyword>\n'
        if self.ret_val in keywords:
            res += '<keyword> ' + self.ret_val + ' </keyword>\n'
        else:
            res += str(self.ret_val)
        res += str(self.name) + '<symbol> ( </symbol>\n<parameterList>\n'
        for i in range(len(self.params)):
            if self.types[i] in keywords:
                res += '<keyword> ' + self.types[i] + ' </keyword>\n'
            else:
                res += str(self.types[i])
            res += str(self.params[i])
            if i < len(self.params) - 1:
                res += '<symbol> , </symbol>\n'
        res += '</parameterList>\n<symbol> ) </symbol>\n<subroutineBody>\n<symbol> { </symbol>\n'
        for var_dec in self.var_decs:
            res += str(var_dec)
        res += str(self.statements) + '<symbol> } </symbol>\n</subroutineBody>\n</subroutineDec>\n'
        return res

    def compile(self):
        global constructor_flag, current_class
        constructor_flag = self.func_type == 'constructor'
        res = 'function ' + current_class + '.' + self.name.name + ' ' + str(self.local_size) + '\n'
        if self.func_type == 'constructor':
            res += 'push constant ' + str(class_size[current_class]) + \
                   '\ncall Memory.alloc 1\npop pointer 0\n'
        if self.func_type == 'method':
            res += 'push argument 0\npop pointer 0\n'
        res += self.statements.compile()
        constructor_flag = False
        return res

class ClassVarDec:
    """
    dec_type (str) : field/static.
    var_type (str) : int/char/boolean/<Object_Name>.
    var_type_token (str) : Token classifiction of var_type : keyword/identifier.
    variables (list<str>) : The names of the variables of the declaration.
    """
    def __init__(self, tknzr):
        self.dec_type = tknzr.getCurToken()
        tknzr.advance()
        self.var_type = tknzr.getCurToken()
        if is_identifier(tknzr.getCurToken()):
            self.var_type = Identifier(self.var_type, 'class', None, False, None)
        tknzr.advance()
        self.variables = []
        while tknzr.getCurToken() != ';':
            self.variables.append(Identifier(tknzr.getCurToken(), self.dec_type, 'declared', False, self.var_type))
            tknzr.advance()
            if tknzr.getCurToken() == ',':
                tknzr.advance()
        tknzr.advance()

    def __str__(self):
        res = '<classVarDec>\n<keyword> ' + self.dec_type + ' </keyword>\n'
        if self.var_type in keywords:
            res += '<keyword> ' + self.var_type + ' </keyword>\n'
        else:
            res += str(self.var_type)
        for i in range(len(self.variables)):
            res += str(self.variables[i])
            if i < len(self.variables) - 1:
                res += '<symbol> , </symbol>\n'
        res += '<symbol> ; </symbol>\n</classVarDec>\n'
        return res

class VarDec:
    """
    var_type (str) : int/char/boolean/<Object_Name>.
    var_type_token (str) : Token classifiction of var_type : keyword/identifier.
    variables (list<str>) : The names of the variables of the declaration.
    """
    def __init__(self, tknzr):
        tknzr.advance()
        self.var_type = tknzr.getCurToken()
        if is_identifier(tknzr.getCurToken()):
            self.var_type = Identifier(self.var_type, 'class', None, False, None)
        tknzr.advance()
        self.variables = []
        while tknzr.getCurToken() != ';':
            self.variables.append(Identifier(tknzr.getCurToken(), 'local', 'declared', False, self.var_type))
            tknzr.advance()
            if tknzr.getCurToken() != ';':
                tknzr.advance()
        tknzr.advance()

    def __str__(self):
        res = '<varDec>\n<keyword> var </keyword>\n'
        if self.var_type in keywords:
            res += '<keyword> ' + self.var_type + ' </keyword>\n'
        else:
            res += str(self.var_type)
        for i in range(len(self.variables)):
            res += str(self.variables[i])
            if i < len(self.variables) - 1:
                res += '<symbol> , </symbol>\n'
        res += '<symbol> ; </symbol>\n</varDec>\n'
        return res

class Statements:
    """
    statements (list<LetStatement,IfStatement,WhileStatement,DoStatement,ReturnStatement>) :
        Self explanatory - all the statements in the body of the function.
    """
    def __init__(self, tknzr):
        self.statements = []
        while tknzr.getCurToken() != '}':
            match tknzr.getCurToken():
                case 'let':
                    self.statements.append(LetStatement(tknzr))
                case 'if':
                    self.statements.append(IfStatement(tknzr))
                case 'while':
                    self.statements.append(WhileStatement(tknzr))
                case 'do':
                    self.statements.append(DoStatement(tknzr))
                case 'return':
                    self.statements.append(ReturnStatement(tknzr))

    def __str__(self):
        res = '<statements>\n'
        for statement in self.statements:
            res += str(statement)
        res += '</statements>\n'
        return res

    def compile(self):
        res = ''
        for statement in self.statements:
            res += statement.compile()
        return res

class LetStatement:
    """
    assigned_var (str) : The assignee variable in the statement.
    array_flag (bool) : Denotes if the assignee variable is an array cell.
    index_expr (Expression) : Relevant only if array_flag = True.
        The expression object which represents the index of the assignee array cell.
    expr (Expression) : The expression which should be assigned to the assignee variable.
    """
    def __init__(self, tknzr):
        tknzr.advance()
        self.assigned_var = Identifier(tknzr.getCurToken(), None, 'declared', True, None)
        tknzr.advance()
        if tknzr.getCurToken() == '[':
            index_expr_tokens = []
            tknzr.advance()
            while tknzr.getCurToken() != '=':
                index_expr_tokens.append(tknzr.getCurToken())
                tknzr.advance()
            index_expr_tokens.pop(-1)
            self.index_expr = Expression(index_expr_tokens)
            self.array_flag = True
        else:
            self.array_flag = False
        tknzr.advance()
        expr_tokens = []
        while tknzr.getCurToken() != ';':
            expr_tokens.append(tknzr.getCurToken())
            tknzr.advance()
        self.expr = Expression(expr_tokens)
        tknzr.advance()

    def __str__(self):
        res = '<letStatement>\n<keyword> let </keyword>\n' + str(self.assigned_var)
        if self.array_flag:
            res += '<symbol> [ </symbol>\n' + str(self.index_expr) + '<symbol> ] </symbol>\n'
        res += '<symbol> = </symbol>\n' + str(self.expr) + '<symbol> ; </symbol>\n</letStatement>\n'
        return res

    def compile(self):
        res = self.expr.compile()
        if self.array_flag:
            res += 'push ' + category_to_segment[self.assigned_var.category] + ' ' + str(self.assigned_var.index) + '\n' + \
                self.index_expr.compile() + \
                'add\npop pointer 1\npop that 0\n'
        else:
            res += 'pop ' + category_to_segment[self.assigned_var.category] + ' ' + str(self.assigned_var.index) + '\n'
        return res

class IfStatement:
    """
    bool_expr (Expression) : A boolean expression of the condition of the IfStatement.
    if_statements (Statements) : Contains all the statements in the body of the if statement.
    else_flag (bool) : Denotes if the IfStatement also contains an else part.
    else_statements (Statements) : Contains all the statements in the body of the else part.
    """
    def __init__(self, tknzr):
        tknzr.advance()
        tknzr.advance()
        bool_tokens = []
        count = 1
        while count > 0:
            bool_tokens.append(tknzr.getCurToken())
            if tknzr.getCurToken() == '(':
                count += 1
            if tknzr.getCurToken() == ')':
                count -= 1
            tknzr.advance()
        bool_tokens.pop(-1)
        self.bool_expr = Expression(bool_tokens)
        tknzr.advance()
        self.if_statements = Statements(tknzr)
        tknzr.advance()
        if tknzr.getCurToken() == 'else':
            self.else_flag = True
            tknzr.advance()
            tknzr.advance()
            self.else_statements = Statements(tknzr)
            tknzr.advance()
        else:
            self.else_flag = False

    def __str__(self):
        res = '<ifStatement>\n<keyword> if </keyword>\n<symbol> ( </symbol>\n' + str(self.bool_expr) + \
              '<symbol> ) </symbol>\n<symbol> { </symbol>\n' + str(self.if_statements) + '<symbol> } </symbol>\n'
        if self.else_flag:
            res += '<keyword> else </keyword>\n<symbol> { </symbol>\n' + str(self.else_statements) + '<symbol> } </symbol>\n'
        res += '</ifStatement>\n'
        return res

    def compile(self):
        global labels_counter
        L1 = labels_counter
        labels_counter += 1
        res = self.bool_expr.compile() + 'not\nif-goto L' + str(L1) + '\n' + self.if_statements.compile()
        if self.else_flag:
            L2 = labels_counter
            labels_counter += 1
            res += 'goto L' + str(L2) + '\n'
        res += 'label L' + str(L1) + '\n'
        if self.else_flag:
            res += self.else_statements.compile() + 'label L' + str(L2) + '\n'
        return res

class WhileStatement:
    """
    bool_expr (Expression) : The boolean expression of the condition of the WhileStatement.
    statements (Statements) : The statements in the body of the WhileStatement.
    """
    def __init__(self, tknzr):
        tknzr.advance()
        tknzr.advance()
        bool_tokens = []
        count = 1
        while count > 0:
            bool_tokens.append(tknzr.getCurToken())
            if tknzr.getCurToken() == '(':
                count += 1
            if tknzr.getCurToken() == ')':
                count -= 1
            tknzr.advance()
        bool_tokens.pop(-1)
        self.bool_expr = Expression(bool_tokens)
        tknzr.advance()
        self.statements = Statements(tknzr)
        tknzr.advance()

    def __str__(self):
        return '<whileStatement>\n<keyword> while </keyword>\n<symbol> ( </symbol>\n' + str(self.bool_expr) + \
              '<symbol> ) </symbol>\n<symbol> { </symbol>\n' + str(self.statements) + '<symbol> } </symbol>\n</whileStatement>\n'

    def compile(self):
        global labels_counter
        L1 = labels_counter
        labels_counter += 1
        L2 = labels_counter
        labels_counter += 1
        return 'label L' + str(L1) + '\n' + \
            self.bool_expr.compile() + 'not\nif-goto L' + str(L2) + '\n' + \
            self.statements.compile() + \
            'goto L' + str(L1) + '\nlabel L' + str(L2) + '\n'

class DoStatement:
    """
    func_name_1 (str) : The first name of the function to be called
        (if it has a second name then this name is the class name,
        otherwise this name is the function name).
    second_name_flag (bool) : Indicates whether the function has a second name.
    func_name_2 (str) : The second name of the function to be called
        (relevant only if second_name_flag is True,
        in which case the second name should be the actual function name).
    expr_lst (list<Expression>) : A list of Expressions passed down as arguments to the function.
    """
    def __init__(self, tknzr):
        tknzr.advance()
        self.func_name_1 = tknzr.getCurToken()
        tknzr.advance()
        if tknzr.getCurToken() == '.':
            self.second_name_flag = True
            tknzr.advance()
            self.func_name_2 = tknzr.getCurToken()
            tknzr.advance()
            self.func_name_1 = Identifier(self.func_name_1, 'class', None, True, None)
            self.func_name_2 = Identifier(self.func_name_2, 'subroutine', None, False, None)
        else:
            self.func_name_1 = Identifier(self.func_name_1, 'subroutine', None, False, None)
            self.second_name_flag = False
        tknzr.advance()
        params_tokens = []
        while tknzr.getCurToken() != ';':
            params_tokens.append(tknzr.getCurToken())
            tknzr.advance()
        params_tokens.pop(-1)
        self.expr_lst = []
        i = 0
        while i < len(params_tokens):
            j = i
            while j < len(params_tokens) and params_tokens[j] != ',':
                j += 1
            self.expr_lst.append(Expression(params_tokens[i:j]))
            i = j + 1
        tknzr.advance()

    def __str__(self):
        res = '<doStatement>\n<keyword> do </keyword>\n' + str(self.func_name_1)
        if self.second_name_flag:
            res += '<symbol> . </symbol>\n' + str(self.func_name_2)
        res += '<symbol> ( </symbol>\n<expressionList>\n'
        for i in range(len(self.expr_lst)):
            res += str(self.expr_lst[i])
            if i < len(self.expr_lst) - 1:
                res += '<symbol> , </symbol>\n'
        res += '</expressionList>\n<symbol> ) </symbol>\n<symbol> ; </symbol>\n</doStatement>\n'
        return res

    def compile(self):
        global current_class, subroutine_types
        is_method = False
        if self.second_name_flag:
            if self.func_name_1.category == 'class':
                class_name = self.func_name_1.name
            else:
                class_name = self.func_name_1.var_type.name
                is_method = True
            func_name = class_name + '.' + self.func_name_2.name
        else:
            func_name = current_class + '.' + self.func_name_1.name
            is_method = subroutine_types[self.func_name_1.name] == 'method'
        res = ''
        params_len = len(self.expr_lst)
        if is_method:
            if self.second_name_flag:
                res += 'push ' + category_to_segment[self.func_name_1.category] + ' ' + str(self.func_name_1.index) + '\n'
            else:
                res += 'push pointer 0\n'
            params_len += 1
        for expr in self.expr_lst:
            res += expr.compile()
        res += 'call ' + func_name + ' ' + str(params_len) + '\npop temp 0\n'
        return res

class ReturnStatement:
    """
    expr_flag (bool) : Indicates whether the ReturnStatement return an Expression or not.
    expr (Expression) : Relevant only if expr_flag is True. The Expression to be returned.
    """
    def __init__(self, tknzr):
        tknzr.advance()
        if tknzr.getCurToken() == ';':
            self.expr_flag = False
        else:
            expr_tokens = []
            while tknzr.getCurToken() != ';':
                expr_tokens.append(tknzr.getCurToken())
                tknzr.advance()
            self.expr = Expression(expr_tokens)
            self.expr_flag = True
        tknzr.advance()

    def __str__(self):
        res = '<returnStatement>\n<keyword> return </keyword>\n'
        if self.expr_flag:
            res += str(self.expr)
        res += '<symbol> ; </symbol>\n</returnStatement>\n'
        return res

    def compile(self):
        if constructor_flag:
            return 'push pointer 0\nreturn\n'
        res = self.expr.compile() if self.expr_flag else 'push constant 0\n'
        res += 'return\n'
        return res

class Expression:
    """
    An Expression is typically of the form: <Term>0 <Op>0 ... <Term>n-1 <Op>n-1 <Term>n, thus:
    terms (list<Term>) : List of all the Terms.
    ops (list<str>) : List of all the operands.
    """
    def __init__(self, tokens):
        self.terms = []
        self.ops = []
        i = 0
        while i < len(tokens):
            j = i
            if tokens[j] in {'-', '~', '^', '#'}:
                j += 1
            while j < len(tokens) and tokens[j] not in {'+', '-', '*', '/', '&', '|', '>', '<', '='}:
                if tokens[j] == '(':
                    j += 1
                    count = 1
                    while count > 0:
                        if tokens[j] == '(':
                            count += 1
                        if tokens[j] == ')':
                            count -= 1
                        j += 1
                else:
                    if tokens[j] == '[':
                        j += 1
                        count = 1
                        while count > 0:
                            if tokens[j] == '[':
                                count += 1
                            if tokens[j] == ']':
                                count -= 1
                            j += 1
                    else:
                        j += 1
            self.terms.append(Term(tokens[i:j]))
            if j < len(tokens):
                self.ops.append(tokens[j])
                j += 1
            i = j

    def __str__(self):
        res = '<expression>\n'
        for i in range(len(self.terms)):
            res += str(self.terms[i])
            if i < len(self.ops):
                res += '<symbol> ' + symbol_to_xml[self.ops[i]] + ' </symbol>\n'
        res += '</expression>\n'
        return res

    def compile(self):
        res = self.terms[0].compile()
        for i in range(len(self.ops)):
            res += self.terms[i+1].compile() + bin_ops_to_vm[self.ops[i]] + '\n'
        return res

class Term:
    """
    A Term structure can be one of the following:
        - <integerConstant>
        - <stringConstant>
        - <keyword>
        - <identifier>
        - <keyword> [ <Expression> ]
        - <subroutineCall>
        - ( <Expression )
        - <symbol> <Term> (where symbol in {'~', '-', '^', '#'})
    """
    def __init__(self, tokens):
        global method_flag, constructor_flag
        subroutine_call_or_array = True
        if tokens[0] == '(' and tokens[-1] == ')':
            self.content = ['(', Expression(tokens[1:-1]), ')']
            subroutine_call_or_array = False
        if len(tokens) == 1 or (len(tokens) == 3 and tokens[1] == '.'):
            self.content = tokens
            subroutine_call_or_array = False
        if len(tokens) >= 2 and tokens[0] in {'~', '-', '^', '#'}:
            self.content = [tokens[0], Term(tokens[1:])]
            subroutine_call_or_array = False
        if subroutine_call_or_array:
            self.content = [tokens[0]]
            i = 2
            if len(tokens) >= 2 and tokens[1] == '.':
                self.content += ['.', tokens[2]]
                i = 4
            match tokens[i-1]:
                case '(':
                    self.content.append('(')
                    expr_lst = []
                    count = 1
                    while i < len(tokens) - 1:
                        j = i
                        while count > 0 and tokens[j] != ',':
                            if tokens[j] == '(':
                                count += 1
                            if tokens[j] == ')':
                                count -= 1
                            j += 1
                        if count == 0:
                            j -= 1
                        expr_lst.append(Expression(tokens[i:j]))
                        i = j + 1
                    self.content += [expr_lst, ')']
                case '[':
                    count = 1
                    j = i + 1
                    while count > 0:
                        if tokens[j] == '[':
                            count += 1
                        if tokens[j] == ']':
                            count -= 1
                        j += 1
                    j -= 1
                    self.content += ['[', Expression(tokens[i:j]), ']']
        for i in range(len(self.content)):
            if (type(self.content[i]) == str and is_identifier(self.content[i])) or (self.content[i] == 'this' and (not constructor_flag)):
                category = None
                if i < len(self.content) - 1:
                    if self.content[i+1] == '.':
                        category = 'class'
                    if self.content[i+1] == '(':
                        category = 'subroutine'
                if self.content[i] == 'this' and method_flag:
                        category = 'arg'
                if i > 1 and \
                        type(self.content[i-2]) == Identifier and \
                        self.content[i-2].category == 'this' and \
                        self.content[i-1] == '.' and \
                        category != 'subroutine':
                    category = 'field'
                self.content[i] = Identifier(self.content[i], category, 'used', True, None)

    def __str__(self):
        res  = '<term>\n'
        for component in self.content:
            match type(component):
                case builtins.str:
                    if component in symbols:
                        res += '<symbol> ' + symbol_to_xml[component] + ' </symbol>\n'
                    if component in keywords:
                        res += '<keyword> ' + component + ' </keyword>\n'
                    if component.isdigit():
                        res += '<integerConstant> ' + component + ' </integerConstant>\n'
                    if is_string(component):
                        res += '<stringConstant> ' + component[1:-1] + ' </stringConstant>\n'
                    if is_identifier(component):
                        res += '<identifier> ' + str(component) + ' </identifier>\n'
                case builtins.list:
                    res += '<expressionList>\n'
                    for i in range(len(component)):
                        res += str(component[i])
                        if i < len(component) - 1:
                            res += '<symbol> , </symbol>\n'
                    res += '</expressionList>\n'
                case _:
                    res += str(component)
        res += '</term>\n'
        return res

    def compile(self):
        global current_class, subroutine_types
        if len(self.content) == 1:
            if type(self.content[0]) == str:
                if self.content[0].isdigit():
                    return 'push constant ' + self.content[0] + '\n'
                if self.content[0] in {'true', 'false'}:
                    res = 'push constant 0\n'
                    if self.content[0] == 'true':
                        res += 'not\n'
                    return res
                if self.content[0] == 'null':
                    return 'push constant 0\n'
                res = 'push constant ' + str(len(self.content[0]) - 2) + '\ncall String.new 1\n'
                for c in self.content[0][1:-1]:
                    res += 'push constant ' + str(ord(c)) + '\ncall String.appendChar 2\n'
                return res
            else:
                return 'push ' + category_to_segment[self.content[0].category] + ' ' + str(self.content[0].index) + '\n'
        if len(self.content) == 4 and self.content[1] == '[' and self.content[3] == ']':
            return 'push ' + category_to_segment[self.content[0].category] + ' ' + str(self.content[0].index) + '\n' + \
                self.content[2].compile() + \
                'add\npop pointer 1\npush that 0\n'
        if len(self.content) >= 4 and \
                self.content[-3] == '(' and \
                type(self.content[-2]) == list \
                and self.content[-1] == ')':
            is_method = False
            if len(self.content) == 4:
                func_name = current_class + '.' + self.content[0].name
                is_method = subroutine_types[self.content[0].name] == 'method'
            else:
                if self.content[0].category == 'class':
                    class_name = self.content[0].name
                else:
                    class_name = self.content[0].var_type.name
                    is_method = True
                func_name = class_name + '.' + self.content[2].name
            res = ''
            params_len = len(self.content[-2])
            if is_method:
                if len(self.content) == 4:
                    res += 'push pointer 0\n'
                else:
                    res += 'push ' + category_to_segment[self.content[0].category] + ' ' + str(self.content[0].index) + '\n'
                params_len += 1
            for expr in self.content[-2]:
                res += expr.compile()
            res += 'call ' + func_name + ' ' + str(params_len) + '\n'
            return res
        if len(self.content) == 3:
            if self.content[1] == '.' and self.content[0].name == 'this':
                return 'push ' + category_to_segment[self.content[2].category] + ' ' + str(self.content[2].index) + '\n'
            return self.content[1].compile()
        if len(self.content) == 2 and self.content[0] in {'-', '~', '^', '#'}:
            res = self.content[1].compile()
            res += un_ops_to_vm[self.content[0]] + '\n'
            return res

class Identifier:
    """
    name (str): The name of the identitifier.
    category (str): field/static/local/arg/class/subroutine.
    index (int): a serial number allocated for each identifier.
    usage (str): declared/used.
    var_type (str): Relevant only for variable. The variable type - can be either int/boolean/char or a <class_name> type.
    """
    def __init__(self, name, category, usage, search_symbol_table, var_type):
        global symbol_indices, symbol_types, index_counters, subroutine_flag, categories, subroutine_categories
        self.name = name
        found = False
        if search_symbol_table:
            cat = subroutine_categories if subroutine_flag else categories
            if category == 'field':
                cat = ['field']
            for c in cat:
                if name in symbol_indices[c]:
                    self.category = c
                    self.index = symbol_indices[c][name]
                    found = True
                    break
        if not (search_symbol_table and found):
            self.category = category
            if category in index_counters:
                if name in symbol_indices[category]:
                    self.index = symbol_indices[category][name]
                else:
                    self.index = index_counters[category]
                    index_counters[category] += 1
            else:
                self.index = None
        symbol_indices[self.category][self.name] = self.index
        self.usage = None if self.category in {'class', 'subroutine'} else usage
        if self.category in {'field', 'static', 'local', 'arg'}:
            if self.index < len(symbol_types[self.category]):
                self.var_type = symbol_types[self.category][self.index]
            else:
                self.var_type = var_type
                symbol_types[self.category].append(var_type)

    def __str__(self):
        res = '<identifier>\n<name> ' + self.name + ' </name>\n<category> ' + self.category + ' </category>\n'
        if self.index is not None:
            res += '<index> ' + str(self.index) + ' </index>\n'
        if self.usage is not None:
            res += '<usage> ' + self.usage + ' </usage>\n'
        res += '</identifier>\n'
        return res

def jackAnalyzer(filename):
    global symbol_indices, symbol_types, index_counters, subroutine_types, labels_counter
    if len(filename) > 5 and filename[-5:] == '.jack':
        # Dealing with a single Jack file.
        tknzr = JackTokenizer(filename)
        tknzr.advance()
        output = open(filename[:-4] + 'vm', 'w')
        # Class is the first component in the recursive file hierarchy.
        # Calling c.compile() will recursively trigger the compile method of each component inside Class.
        c = Class(tknzr)
        output.write(c.compile())
        output.close()
    else:
        # Dealing with a directory.
        for sub_file in os.listdir(filename):
            if len(sub_file) > 5 and sub_file[-5:] == '.jack':
                full_sub_file = filename + '//' + sub_file
                symbol_indices = {'field': {}, 'static': {}, 'local': {}, 'arg': {}, 'class' : {}, 'subroutine' : {}}
                symbol_types = {'field': [], 'static': [], 'local': [], 'arg': []}
                index_counters = {'field': 0, 'static': 0, 'local': 0, 'arg': 0}
                subroutine_types = {}
                labels_counter = 0
                tknzr = JackTokenizer(full_sub_file)
                tknzr.advance()
                output = open(full_sub_file[:-4] + 'vm', 'w')
                # Class is the first component in the recursive file hierarchy.
                # Calling c.compile() will recursively trigger the compile method of each component inside Class.
                c = Class(tknzr)
                output.write(c.compile())
                output.close()

jackAnalyzer(sys.argv[1])