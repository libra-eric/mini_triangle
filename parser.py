#!/usr/bin/env python
#
# Scanner for a calculator interpreter

import scanner as scanner
import ast as ast


class ParserError(Exception):
    """Parser error exception.

    pos: position in the input token stream where the error occurred.
    type: bad token type
    """

    def __init__(self, pos, type):
        self.pos = pos
        self.type = type

    def __str__(self):
        return '(Found bad token %s at %d)' % (scanner.TOKENS[self.type], self.pos)


class Parser(object):
    """Implement a parser for the following grammar:

    Program            ::=  Command EOT

    Command            ::=  single-Command (';' single-Command)*

    single-Command     ::=  Identifier ( ':=' Expression | '(' Expression ')')
                        |   if Expression then single-Command
                            else single-Command
                        |   while Expression do single-Command
                        |   let Declaration in single-Command
                        |   begin Command end
                        |   return Expression  ';'

    Expression         ::=  primary-Expression (Operator primary-Expression)*

    primary-Expression ::=  Integer-Literal
                        |   Identifier ( *empyt* | '(' Expression ')' )
                        |   Operator primary-Expression
                        |   '(' Expression ')'

    Declaration        ::=  single-Declaration (';' single-Declaration)*

    single-Declaration ::=  const Identifier ~ Expression ';'
                        |   var Identifier : Type-denoter ';'
                        |   func Identifier '(' Identifier ':' Identifier ')' ':' Identifier single-Command

    Type-denoter       ::=  Identifier

    Operator           ::=  '+' | '-' | '*' | '/' | '<' | '>' | '=' | '\'

    Identifier         ::=  Letter | Identifier Letter | Identifier Digit

    Integer-Literal    ::=  Digit | Integer-Literal Digit

    Comment            ::=  ! Graphic* <eol>
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.curindex = 0
        self.curtoken = tokens[0]

    def parse(self):
        return self.parse_program()

    def parse_program(self):
        """ Program ::=  Command EOT """

        command = self.parse_command()
        self.token_accept(scanner.TK_EOT)
        return ast.Program(command)

    def parse_command(self):
        """ Command ::=  single-Command (';' single-Command)*  """

        sc1 = self.parse_single_command()
        t = True
        while t:
            try:
                sc2 = self.parse_single_command()
            except Exception, e:
                t = False
            if t:
                sc1 = ast.SequentialCommand(sc1, sc2)
        return sc1

    def parse_single_command(self):
        """single-Command ::=  Identifier ( ':=' Expression | '(' Expression ')')
                           |   if Expression then single-Command
                               else single-Command
                           |   while Expression do single-Command
                           |   let Declaration in single-Command
                           |   begin Command end
                           |   return Expression
        """

        token = self.token_current()

        if token.type == scanner.TK_IDENTIFIER:
            self.token_accept_any()
            token_next = self.token_current()
            if token_next.type == scanner.TK_BECOMES:
                self.token_accept_any()
                expr = self.parse_expression()
                cmd = ast.AssignCommand(ast.Vname(token.val), expr)
            elif token_next.type == scanner.TK_LPAREN:
                self.token_accept_any()
                expr = self.parse_arg_expr()
                self.token_accept(scanner.TK_RPAREN)
                cmd = ast.CallCommand(token.val, expr)
            self.token_accept(scanner.TK_SEMICOLON)
        elif token.type == scanner.TK_IF:
            self.token_accept_any()
            expr = self.parse_expression()
            self.token_accept(scanner.TK_THEN)
            sc1 = self.parse_single_command()
            self.token_accept(scanner.TK_ELSE)
            sc2 = self.parse_single_command()
            cmd = ast.IfCommand(expr, sc1, sc2)
        elif token.type == scanner.TK_WHILE:
            self.token_accept_any()
            expr = self.parse_expression()
            self.token_accept(scanner.TK_DO)
            sc1 = self.parse_single_command()
            cmd = ast.WhileCommand(expr, sc1)
        elif token.type == scanner.TK_LET:
            self.token_accept_any()
            decl = self.parse_declaration()
            self.token_accept(scanner.TK_IN)
            sc1 = self.parse_single_command()
            cmd = ast.LetCommand(decl, sc1)
        elif token.type == scanner.TK_BEGIN:
            self.token_accept_any()
            cmd = self.parse_command()
            self.token_accept(scanner.TK_END)
        elif token.type == scanner.TK_RETURN:
            self.token_accept_any()
            expr = self.parse_expression()
            cmd = ast.ReturnCommand(expr)
            self.token_accept(scanner.TK_SEMICOLON)
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)
        return cmd

    def parse_expression(self):
        """ Expression ::=  primary-Expression (Operator primary-Expression)* """

        e1 = self.parse_add_expression()
        token = self.token_current()
        while token.type == scanner.TK_OPERATOR and token.val in ['<','=','>']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_add_expression()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_add_expression(self):
        e1 = self.parse_mul_expression()
        token = self.token_current()

        while token.type == scanner.TK_OPERATOR and token.val in ['+','-']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_mul_expression()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_mul_expression(self):
        e1 = self.parse_primary_expression()
        token = self.token_current()

        while token.type == scanner.TK_OPERATOR and token.val in ['*','/','\\']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_primary_expression()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_primary_expression(self):
        """ primary-Expression ::=  Integer-Literal
                                |   Identifier ( *empty* | '(' Expression ')' )
                                |   Operator primary-Expression
                                |   '(' Expression ')' 
        """

        token = self.token_current()
        if token.type == scanner.TK_INTLITERAL:

            self.token_accept_any()
            expr = ast.IntegerExpression(token.val)

        elif token.type == scanner.TK_IDENTIFIER:
            self.token_accept_any()
            next = self.token_current()
            if next.type == scanner.TK_LPAREN:
                ident = token.val
                self.token_accept_any()
                expr = self.parse_arg_expr()
                self.token_accept(scanner.TK_RPAREN)
                expr = ast.CallExpression(ident, expr)
            else:
                expr = ast.VnameExpression(ast.Vname(token.val))
        elif token.type == scanner.TK_OPERATOR:
            oper = token.val
            self.token_accept_any()
            expr = self.parse_primary_expression()
            expr = ast.UnaryExpression(oper, expr)
        elif token.type == scanner.TK_LPAREN:
            self.token_accept_any()
            expr = self.parse_expression()
            self.token_accept(scanner.TK_RPAREN)
            return expr
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)

        return expr

    def parse_arg_expr(self):
        are1 = self.parse_primary_expression()
        while self.token_current().type == scanner.TK_COMMA:
            self.token_accept_any()
            are2 = self.parse_primary_expression()
            are1 = ast.ArgrExpression(are1, are2)
        return are1

    def parse_declaration(self):
        """ single-Declaration ::=  single-Declaration (';' single-Declaration)* """
        sd1 = self.parse_single_declaration()
        if self.token_lookprev().type != scanner.TK_END:
            self.token_accept(scanner.TK_SEMICOLON)
        t = True
        while t:
            try:
                sd2 = self.parse_single_declaration()
            except Exception, e:
                t = False
            if t:
                if self.token_lookprev().type != scanner.TK_END:
                    self.token_accept(scanner.TK_SEMICOLON)
                sd1 = ast.SequentialDeclaration(sd1, sd2)

        return sd1

    def parse_single_declaration(self):
        """ single-Declaration ::=  const Identifier ~ Expression
                                |   var Identifier : Type-denoter
                                |   func Identifier '(' Identifier ':' Type-denoter ',*)' ':' Type-denoter single-Command
        """

        token = self.token_current()
        if token.type == scanner.TK_CONST:
            self.token_accept_any()
            token = self.token_current()
            self.token_accept(scanner.TK_IDENTIFIER)
            ident = token.val
            self.token_accept(scanner.TK_IS)
            expr = self.parse_expression()
            decl = ast.ConstDeclaration(ident, expr)
        elif token.type == scanner.TK_VAR:
            self.token_accept_any()
            token = self.token_current()
            self.token_accept(scanner.TK_IDENTIFIER)
            ident = token.val
            self.token_accept(scanner.TK_COLON)
            type_denoter = self.parse_type_denoter()
            decl = ast.VarDeclaration(ident, type_denoter)
        elif token.type == scanner.TK_FUNCDEF:
            self.token_accept_any()
            tk_ident = self.token_current()
            self.token_accept(scanner.TK_IDENTIFIER)
            self.token_accept(scanner.TK_LPAREN)
            if self.token_current != scanner.TK_RPAREN :
                argrs = self.parse_argr()
            else:
                argrs = ''

            self.token_accept(scanner.TK_RPAREN)
            self.token_accept(scanner.TK_COLON)
            func_type = self.parse_type_denoter()
            command = self.parse_single_command()
            #decl = ast.FunctionDeclaration(tk_ident.val, tk_argident.val, arg_type, func_type, command)
            decl = ast.FunctionDeclaration(tk_ident.val, argrs, func_type, command)
        else:
            raise ParserError(self.curtoken.pos, self.curtoken.type)

        return decl
    def parse_argr(self):
        ar1 = self.parse_single_argr()
        while self.token_current().type == scanner.TK_COMMA:
            self.token_accept_any()
            ar2 = self.parse_single_argr()
            ar1 = ast.SequentialArgr(ar1, ar2)
        return ar1

    def parse_single_argr(self):
        tk_argident = self.token_current()
        tk_argident_val = tk_argident.val
        self.token_accept(scanner.TK_IDENTIFIER)
        self.token_accept(scanner.TK_COLON)
        arg_type = self.parse_type_denoter()
        tk = ast.SingleArgr(tk_argident_val, arg_type)
        return tk

    def parse_type_denoter(self):
        """ Type-denoter ::=  Identifier """

        token = self.token_current()
        self.token_accept(scanner.TK_IDENTIFIER)
        return ast.TypeDenoter(token.val)

    def token_current(self):
        return self.curtoken

    def token_lookahead(self):
        return self.tokens[self.curindex + 1]

    def token_lookprev(self):
        return self.tokens[self.curindex - 1]

    def token_accept_any(self):
        # Do not increment curindex if curtoken is TK_EOT.
        if self.curtoken.type != scanner.TK_EOT:
            self.curindex += 1
            self.curtoken = self.tokens[self.curindex]

    def token_accept(self, type):
        if self.curtoken.type != type:
            raise ParserError(self.curtoken.pos, self.curtoken.type)

        self.token_accept_any()


if __name__ == '__main__':
    exprs = [ """
let
    var fact1: Integer;
    var fact2: Integer;
    func abc(a:Integer, b:Integer, c:Integer):Integer
        begin
            return a+b+c;
        end
in
    begin
        getint(x);
        fact1 := abc(1,2,3);
        fact1 := fact1 + x;
        fact2 := abc(4,6,7);
        putint(fact1);
    end
    """]

    for exp in exprs:
        print '=============='
        print exp

        s = scanner.Scanner(exp)

        try:
            tokens = s.scan()
            print tokens
        except scanner.ScannerError as e:
            print e
            continue

        p = Parser(tokens)

        try:
            tree = p.parse()
            print tree
        except ParserError as e:
            print e
            print 'Not Parsed!'
            continue

        print 'Parsed!'
