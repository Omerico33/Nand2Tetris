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

class JackTokenizer:
    def __init__(self, filename):
        f = open(filename)
        lines = f.readlines()
        f.close()
        i = 0
        # Firstly get rid of all the comments in the code.
        while i < len(lines):
            comment_index = lines[i].find('//')
            if comment_index != -1:
                lines[i] = lines[i][:comment_index]
            else:
                comment_start_index = lines[i].find('/*')
                if comment_start_index != -1:
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
                    if comment_start_index != -1:
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
        tknzr.advance()
        self.name = tknzr.getCurToken()
        self.components = []
        tknzr.advance()
        tknzr.advance()
        while tknzr.getCurToken() != '}':
            if tknzr.getCurToken() in {'constructor', 'function', 'method'}:
                self.components.append(Subroutine(tknzr))
            if tknzr.getCurToken() in {'field', 'static'}:
                self.components.append(ClassVarDec(tknzr))

    def __str__(self):
        res = '<class>\n<keyword> class </keyword>\n<identifier> ' + self.name + ' </identifier>\n<symbol> { </symbol>\n'
        for component in self.components:
            res += str(component)
        res += '<symbol> } </symbol>\n</class>\n'
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
        self.func_type = tknzr.getCurToken()
        tknzr.advance()
        self.ret_val = tknzr.getCurToken()
        tknzr.advance()
        self.name = tknzr.getCurToken()
        tknzr.advance()
        tknzr.advance()
        self.params = []
        self.types = []
        while tknzr.getCurToken() != ')':
            self.types.append(tknzr.getCurToken())
            tknzr.advance()
            self.params.append(tknzr.getCurToken())
            tknzr.advance()
            if tknzr.getCurToken() == ',':
                tknzr.advance()
        tknzr.advance()
        tknzr.advance()
        self.var_decs = []
        while tknzr.getCurToken() == 'var':
            self.var_decs.append(VarDec(tknzr))
        self.statements = Statements(tknzr)
        tknzr.advance()

    def __str__(self):
        res = '<subroutineDec>\n<keyword> ' + self.func_type + ' </keyword>\n'
        if self.ret_val in keywords:
            res += '<keyword> ' + self.ret_val + ' </keyword>\n'
        else:
            res += '<identifier> ' + self.ret_val + ' </identifier>\n'
        res += '<identifier> ' + self.name + ' </identifier>\n<symbol> ( </symbol>\n<parameterList>\n'
        for i in range(len(self.params)):
            if self.types[i] in keywords:
                res += '<keyword> ' + self.types[i] + ' </keyword>\n'
            else:
                res += '<identifier> ' + self.types[i] + ' </identifier>\n'
            res += '<identifier> ' + self.params[i] + ' </identifier>\n'
            if i < len(self.params) - 1:
                res += '<symbol> , </symbol>\n'
        res += '</parameterList>\n<symbol> ) </symbol>\n<subroutineBody>\n<symbol> { </symbol>\n'
        for var_dec in self.var_decs:
            res += str(var_dec)
        res += str(self.statements) + '<symbol> } </symbol>\n</subroutineBody>\n</subroutineDec>\n'
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
        self.var_type_token = tknzr.tokenType()
        tknzr.advance()
        self.variables = []
        while tknzr.getCurToken() != ';':
            self.variables.append(tknzr.getCurToken())
            tknzr.advance()
            if tknzr.getCurToken() == ',':
                tknzr.advance()
        tknzr.advance()

    def __str__(self):
        res = '<classVarDec>\n<keyword> ' + self.dec_type + ' </keyword>\n<' + self.var_type_token + '> ' + self.var_type + ' </' + self.var_type_token + '>\n'
        for i in range(len(self.variables)):
            res += '<identifier> ' + self.variables[i] + ' </identifier>\n'
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
        self.var_type_token = tknzr.tokenType()
        tknzr.advance()
        self.variables = []
        while tknzr.getCurToken() != ';':
            self.variables.append(tknzr.getCurToken())
            tknzr.advance()
            if tknzr.getCurToken() != ';':
                tknzr.advance()
        tknzr.advance()

    def __str__(self):
        res = '<varDec>\n<keyword> var </keyword>\n<' + self.var_type_token + '> ' + self.var_type + ' </' + self.var_type_token + '>\n'
        for i in range(len(self.variables)):
            res += '<identifier> ' + self.variables[i] + ' </identifier>\n'
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
        self.assigned_var = tknzr.getCurToken()
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
        res = '<letStatement>\n<keyword> let </keyword>\n<identifier> ' + self.assigned_var + ' </identifier>\n'
        if self.array_flag:
            res += '<symbol> [ </symbol>\n' + str(self.index_expr) + '<symbol> ] </symbol>\n'
        res += '<symbol> = </symbol>\n' + str(self.expr) + '<symbol> ; </symbol>\n</letStatement>\n'
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
        else:
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
        res = '<doStatement>\n<keyword> do </keyword>\n<identifier> ' + self.func_name_1 + ' </identifier>\n'
        if self.second_name_flag:
            res += '<symbol> . </symbol>\n<identifier> ' + self.func_name_2 + ' </identifier>\n'
        res += '<symbol> ( </symbol>\n<expressionList>\n'
        for i in range(len(self.expr_lst)):
            res += str(self.expr_lst[i])
            if i < len(self.expr_lst) - 1:
                res += '<symbol> , </symbol>\n'
        res += '</expressionList>\n<symbol> ) </symbol>\n<symbol> ; </symbol>\n</doStatement>\n'
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
                        res += '<identifier> ' + component + ' </identifier>\n'
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

def jackAnalyzer(filename):
    if len(filename) > 5 and filename[-5:] == '.jack':
        # Dealing with a single Jack file.
        tknzr = JackTokenizer(filename)
        tknzr.advance()
        output = open(filename[:-4] + 'xml', 'w')
        # Class is the first component in the recursive file hierarchy.
        # Calling str(c) will recursively trigger the __str__ method of each component inside Class.
        c = Class(tknzr)
        output.write(str(c))
        output.close()
    else:
        # Dealing with a directory.
        for sub_file in os.listdir(filename):
            if len(sub_file) > 5 and sub_file[-5:] == '.jack':
                full_sub_file = filename + '//' + sub_file
                tknzr = JackTokenizer(full_sub_file)
                tknzr.advance()
                output = open(full_sub_file[:-4] + 'xml', 'w')
                # Class is the first component in the recursive file hierarchy.
                # Calling str(c) will recursively trigger the __str__ method of each component inside Class.
                c = Class(tknzr)
                output.write(str(c))
                output.close()

jackAnalyzer(sys.argv[1])