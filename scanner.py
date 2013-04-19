#!/usr/bin/env python
#
# Scanner for Mini Triangle

import cStringIO as StringIO
import string

# Token Constants

TK_IDENTIFIER = 0
TK_INTLITERAL = 1
TK_OPERATOR   = 2
TK_BEGIN      = 3  # begin
TK_CONST      = 4  # const
TK_DO         = 5  # do
TK_ELSE       = 6  # else
TK_END        = 7  # end
TK_IF         = 8  # if
TK_IN         = 9  # in
TK_LET        = 10 # let
TK_THEN       = 11 # then
TK_VAR        = 12 # var
TK_WHILE      = 13 # while
TK_SEMICOLON  = 14 # ;
TK_COLON      = 15 # :
TK_BECOMES    = 16 # :=
TK_IS         = 17 # ~
TK_LPAREN     = 18 # (
TK_RPAREN     = 19 # )
TK_EOT        = 20 # end of text
TK_FUNCDEF    = 21 # func
TK_RETURN     = 22 # return
TK_COMMA      = 23 # ,

TOKENS = {TK_IDENTIFIER: 'IDENTIFIER',
          TK_INTLITERAL: 'INTLITERAL',
          TK_OPERATOR:   'OPERATOR',
          TK_BEGIN:      'BEGIN',
          TK_CONST:      'CONST',
          TK_DO:         'DO',
          TK_ELSE:       'ELSE',
          TK_END:        'END',
          TK_IF:         'IF',
          TK_IN:         'IN',
          TK_LET:        'LET',
          TK_THEN:       'THEN',
          TK_VAR:        'VAR',
          TK_WHILE:      'WHILE',
          TK_SEMICOLON:  'SEMICOLON',
          TK_COLON:      'COLON',
          TK_BECOMES:    'BECOMES',
          TK_IS:         'IS',
          TK_LPAREN:     'LPAREN',
          TK_RPAREN:     'RPAREN',
          TK_EOT:        'EOT',
          TK_FUNCDEF:    'FUNCDEF',
          TK_RETURN:     'RETURN',
          TK_COMMA:      'COMMA'}

class Token(object):
    """ A simple Token structure.
        
        Contains the token type, value and position. 
    """
    def __init__(self, type, val, pos):
        self.type = type
        self.val = val
        self.pos = pos

    def __str__(self):
        return '(%s(%s) at %s)' % (TOKENS[self.type], self.val, self.pos)

    def __repr__(self):
        return self.__str__()


class ScannerError(Exception):
    """ Scanner error exception.

        pos: position in the input text where the error occurred.
    """
    def __init__(self, pos, char):
        self.pos = pos
        self.char = char

    def __str__(self):
        return 'ScannerError at pos = %d, char = %s' % (self.pos, self.char)

class Scanner(object):
    """Implement a scanner for the following token grammar
    
    Token     ::=  Letter (Letter | Digit)* | Digit Digit* |
                   '+' | '-' | '*' | '/' | '<' | '>' | '=' | '\'
                   ':' ('=' | <empty>) | ';' | '~' | '(' | ')' | <eot>

    Separator ::=  '!' Graphic* <eol> | <space> | <eol> 
    """

    operators = ['+', '-', '*', '/', '<', '>', '=', '\\']

    keywords = {'begin' : TK_BEGIN,
                'const' : TK_CONST,
                'do'    : TK_DO,
                'else'  : TK_ELSE,
                'end'   : TK_END,
                'if'    : TK_IF,
                'in'    : TK_IN,
                'let'   : TK_LET,
                'then'  : TK_THEN,
                'var'   : TK_VAR,
                'while' : TK_WHILE,
                'func'  : TK_FUNCDEF,
                'return': TK_RETURN }

    def __init__(self, input):
        # Use StringIO to treat input string like a file.
        self.inputstr = StringIO.StringIO(input)
        self.eot = False   # Are we at the end of the input text?
        self.pos = 0       # Position in the input text
        self.char = ''     # The current character from the input text
        self.char_take()   # Fill self.char with the first character

    def scan(self):
        """Main entry point to scanner object.

        Return a list of Tokens.
        """

        self.tokens = []
        while True:
            token = self.scan_token()
            self.tokens.append(token)
            if token.type == TK_EOT:
                break
        return self.tokens

    def scan_token(self):
        """Scan a single token from input text."""

        c = self.char_current()
        token = None

        while not self.char_eot():
            if c.isspace():
                self.char_take()
                c = self.char_current()
                continue
            elif c == '!':
                self.char_take()
                while self.char_current() != '\n':
                    self.char_take()
                self.char_take()
                c = self.char_current()
                continue
            elif c.isalpha():
                token = self.scan_ident_keyword()
                break
            elif c.isdigit():
                token = self.scan_intliteral()
                break
            elif c in Scanner.operators:
                token = Token(TK_OPERATOR, c, self.char_pos())
                self.char_take()
                break
            elif c == ':':
                pos = self.char_pos()
                self.char_take()
                if self.char_current() == '=':
                    token = Token(TK_BECOMES, 0, pos)
                    self.char_take()
                else:
                    token = Token(TK_COLON, 0, pos)
                break
            elif c == ';':
                token = Token(TK_SEMICOLON, 0, self.char_pos())
                self.char_take()
                break
            elif c == '~':
                token = Token(TK_IS, 0, self.char_pos())
                self.char_take()
                break
            elif c == '(':
                token = Token(TK_LPAREN, 0, self.char_pos())
                self.char_take()
                break
            elif c == ')':
                token = Token(TK_RPAREN, 0, self.char_pos())
                self.char_take()
                break
            elif c == ',':
                token = Token(TK_COMMA, 0, self.char_pos())
                self.char_take()
                break

            return token

        if token is not None:
            return token

        if self.char_eot():
            return(Token(TK_EOT, 0, self.char_pos()))

    def scan_ident_keyword(self):
        pos = self.char_pos()
        chars = [self.char_take()]
        while self.char_current().isalnum():
            chars.append(self.char_take())
        ident = ''.join(chars)

        if ident in Scanner.keywords:
            return Token(Scanner.keywords[ident], 0, pos)
        else:
            return Token(TK_IDENTIFIER, ident, pos)

    def scan_intliteral(self):
        pos = self.char_pos()
        numlist = [self.char_take()]

        while self.char_current().isdigit():
            numlist.append(self.char_take())

        return Token(TK_INTLITERAL, ''.join(numlist), pos)


    def char_current(self):
        """Return in the current input character."""

        return self.char

    def char_take(self):
        """Consume the current character and read the next character 
        from the input text.

        Update self.char, self.eot, and self.pos
        """

        char_prev = self.char

        self.char = self.inputstr.read(1)
        if self.char == '':
            self.eot = True

        self.pos += 1

        return char_prev

    def char_pos(self):
        """Return the position of the *current* character in the input text."""

        return self.pos - 1

    def char_eot(self):
        """Determine if we are at the end of the input text."""

        return self.eot


if __name__ == '__main__':
    src1 = """! A test program
              let var x: Integer;
        var y: Integer;
        var z: Integer;
        var s: Integer

    in
     begin
        x := 1;
        y := 2;
        z := 3;
        s := x + y*z;
        putint(s)
     end"""

    src_list = [src1, "let var x: Integer in x := 0"]

    for src in src_list:
        print '=============='
        scanner = Scanner(src)
        try:
            tokens = scanner.scan()
            print tokens
        except ScannerError as e:
            print e

