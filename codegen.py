# calc_eval.py

from byteplay import *
from types import CodeType, FunctionType
import pprint

import scanner
import parser
import ast
import sys
import os
import struct
import time
import marshal

class CodeGenError(Exception):
    """ Code Generator Error """

    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return 'Error at ast node: %s' % (str(self.ast))

class CodeGen(object):

    def __init__(self, tree):
        self.tree = tree
        self.code = []
        self.env = {}
        self.args = []
        self.number = 0

    def generate(self):

        if type(self.tree) is not ast.Program:
            raise CodeGenError(self.tree)

        self.gen_command(self.tree.command)
        self.code.append((LOAD_CONST, None))
        self.code.append((RETURN_VALUE, None))

        pprint.pprint(self.code)

        code_obj = Code(self.code, [], [], False, False, False, 'gencode', '', 0, '')
        code = code_obj.to_code()
        func = FunctionType(code, globals(), 'gencode')
        return func

    def gen_command(self, tree):

        if type(tree) is ast.IfCommand:
            label1 = Label()
            label2 = Label()
            self.gen_expr(tree.expression)
            self.code.append((POP_JUMP_IF_FALSE, label1))
            self.gen_command(tree.command1)
            self.code.append((JUMP_FORWARD,label2))
            self.code.append((label1, None))
            self.gen_command(tree.command2)
            self.code.append((label2, None))

        elif type(tree) is ast.LetCommand:
            self.gen_declaration(tree.declaration)
            self.gen_command(tree.command)

        elif type(tree) is ast.CallCommand:

            if tree.identifier == 'getint':
                self.code.append((LOAD_GLOBAL, 'input'))
                self.code.append((CALL_FUNCTION, 0))
                self.code.append((STORE_FAST, tree.expression.variable.identifier))

            elif tree.identifier == 'putint':
#                self.code.append((LOAD_GLOBAL, 'print'))
#                self.code.append((CALL_FUNCTION, 1))
                self.gen_expr(tree.expression)
                self.code.append((PRINT_ITEM, None))
                self.code.append((PRINT_NEWLINE, None))
            else:
                self.code.append((LOAD_GLOBAL, tree.identifier))

        elif type(tree) is ast.WhileCommand:
            label3 = Label()
            label4 = Label()
            label5 = Label()
            self.code.append((SETUP_LOOP, label5))
            self.code.append((label3, None))
            self.gen_expr(tree.expression)

            self.code.append((POP_JUMP_IF_FALSE, label4))
            self.gen_command(tree.command)
            self.code.append((JUMP_ABSOLUTE, label3))
            self.code.append((label4, None))
            self.code.append((POP_BLOCK, None))
            self.code.append((label5, None))

        elif type(tree) is ast.AssignCommand:
            self.gen_expr(tree.expression)
            self.code.append((STORE_FAST, tree.variable.identifier))

        elif type(tree) is ast.SequentialCommand:
            self.gen_command(tree.command1)
            self.gen_command(tree.command2)

        elif type(tree) is ast.ReturnCommand:
            self.gen_expr(tree.expression)
            self.code.append((RETURN_VALUE, None))
        else:
            raise CodeGenError(tree)

    def gen_expr(self, tree):

        if type(tree) is ast.VnameExpression:
            self.code.append((LOAD_FAST, tree.variable.identifier))

        elif type(tree) is ast.IntegerExpression:
            self.code.append((LOAD_CONST, int(tree.value)))

        elif type(tree) is ast.CallExpression:
            self.code.append((LOAD_FAST, tree.identifier))
            self.gen_expr(tree.expression)
            self.code.append((CALL_FUNCTION, self.number))

        elif type(tree) is ast.ArgrExpression:
            self.number = 1
            self.gen_expr(tree.argument1)
            self.gen_expr(tree.argument2)
            self.number += 1

        elif type(tree) is ast.BinaryExpression:
            self.gen_expr(tree.expr1)
            self.gen_expr(tree.expr2)
            op = tree.oper
            if op == '+':
                self.code.append((BINARY_ADD, None))
            elif op == '-':
                self.code.append((BINARY_SUBTRACT, None))
            elif op == '*':
                self.code.append((BINARY_MULTIPLY, None))
            elif op == '/':
                self.code.append((BINARY_DIVIDE, None))
            elif op == '<':
                self.code.append((COMPARE_OP, '<'))
            elif op == '>':
                self.code.append((COMPARE_OP, '>'))
            elif op == '=':
                self.code.append((COMPARE_OP, '=='))
            elif op == '\\':
                self.code.append((BINARY_MODULO, None))

        elif type(tree) is ast.UnaryExpression:
            self.gen_expr(tree.expr)
            op = tree.oper
            if op == '+':
                self.code.append((BINARY_ADD, None))
            elif op == '-':
                self.code.append((BINARY_SUBTRACT, None))
            elif op == '*':
                self.code.append((BINARY_MULTIPLY, None))
            elif op == '/':
                self.code.append((BINARY_DIVIDE, None))
            elif op == '<':
                self.code.append((COMPARE_OP, '<'))
            elif op == '>':
                self.code.append((COMPARE_OP, '>'))
            elif op == '=':
                self.code.append((COMPARE_OP, '=='))
            elif op == '\\':
                self.code.append((BINARY_MODULO, None))

        else:
            raise CodeGenError(tree)

    def gen_arguments(self, tree):
        if type(tree) is ast.SingleArgr:
            self.args.append(tree.name)
        elif type(tree) is ast.SequentialArgr:
            self.gen_arguments(tree.argr1)
            self.gen_arguments(tree.argr2)

    def gen_func(self, comm):
        cg = CodeGen(comm.command)
        cg.gen_command(comm.command)
        self.args = []
        if comm.args != '':
            self.gen_arguments(comm.args)
        code_obj = Code(cg.code, [], self.args, False, False, True, comm.name, '', 0, '')
        return code_obj

    def gen_declaration(self, tree):
        if type(tree) is ast.ConstDeclaration:
#            self.code.append((LOAD_FAST, tree.identifier))
#            self.gen_expr(tree.expression)
            pass

        if type(tree) is ast.VarDeclaration:
#            self.code.append((LOAD_FAST, tree.identifier))
#            self.code.append((LOAD_FAST, tree.type_denoter))
            pass

        if type(tree) is ast.SequentialDeclaration:
            self.gen_declaration(tree.decl1)
            self.gen_declaration(tree.decl2)


        elif type(tree) is ast.FunctionDeclaration:

            func = self.gen_func(tree)
            self.code.append((LOAD_CONST, func))
            self.code.append((MAKE_FUNCTION, 0))
            self.code.append((STORE_FAST, tree.name))



def write_pyc_file(code, name):
    pyc_file = name + '.pyc'
    print pyc_file
    with open(pyc_file,'wb') as pyc_f:
        magic = 0x03f30d0a
        pyc_f.write(struct.pack(">L",magic))
        pyc_f.write(struct.pack(">L",time.time()))
        marshal.dump(code.func_code, pyc_f)



if __name__ == '__main__':


    if len(sys.argv) < 2:
        print "============="
        exit(1)
    fn = sys.argv[1]

    if not os.path.isfile(fn):
        print "input file not exist"
        exit(1)
    fh = open(fn)
    data = fh.read();
    scan = scanner.Scanner(data)

    try:
        tokens = scan.scan()
        print tokens
    except scanner.ScannerError as e:
        print e

    parse = parser.Parser(tokens)

    try:
        tree = parse.parse()
        print tree
    except parser.ParserError as e:
        print e
        print 'Not Parsed!'

    cg = CodeGen(tree)
    code = cg.generate()
    print code()
    name = fn.split('.')[0]
    write_pyc_file(code, name)