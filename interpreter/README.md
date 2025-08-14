# Build Your Own Interpreter

Create programming language interpreters from scratch and understand how languages are executed. Learn lexical analysis, parsing, abstract syntax trees, and expression evaluation.

## 🎯 What You'll Learn

- Lexical analysis and tokenization techniques
- Parsing theory and recursive descent parsers
- Abstract syntax tree (AST) construction and traversal
- Expression evaluation and statement execution
- Variable binding and scope management
- Function calls and recursion handling

## 📋 Prerequisites

- Understanding of programming language concepts
- Knowledge of recursive data structures and algorithms
- Familiarity with formal grammars and BNF notation
- Basic understanding of compiler theory

## 🏗️ Architecture Overview

Our interpreter consists of these core components:

1. **Lexer**: Breaks source code into tokens
2. **Parser**: Builds abstract syntax tree from tokens
3. **AST Nodes**: Represent language constructs
4. **Evaluator**: Executes AST nodes and manages state
5. **Environment**: Handles variable and function scoping
6. **Built-ins**: Provides standard library functions

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Source Code  │───▶│    Lexer     │───▶│     Tokens      │
│"x = 5 + 3"  │    │ (Tokenizer)  │    │ [ID,EQ,NUM,...]│
└─────────────┘    └──────────────┘    └─────────────────┘
                                                 │
┌─────────────┐    ┌──────────────┐              ▼
│   Result    │◄───│  Evaluator   │    ┌─────────────────┐
│     8       │    │ (Executor)   │    │     Parser      │
└─────────────┘    └──────────────┘    │ (AST Builder)   │
                          ▲             └─────────────────┘
┌─────────────┐           │                       │
│ Environment │───────────┘                       ▼
│ (Variables) │                         ┌─────────────────┐
└─────────────┘                         │  AST Nodes      │
                                        │ (Assignment,    │
                                        │  Binary Op)     │
                                        └─────────────────┘
```

## 🚀 Implementation Steps

### Step 1: Lexical Analysis (Tokenizer)

Start by breaking source code into meaningful tokens.

```python
import re
from enum import Enum, auto
from typing import List, NamedTuple, Optional, Iterator

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    IDENTIFIER = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    
    # Comparison
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    
    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Assignment
    ASSIGN = auto()
    
    # Delimiters
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()
    
    # Keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    FUNCTION = auto()
    RETURN = auto()
    LET = auto()
    CONST = auto()
    
    # Special
    EOF = auto()
    NEWLINE = auto()

class Token(NamedTuple):
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        
        # Keyword mapping
        self.keywords = {
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'for': TokenType.FOR,
            'function': TokenType.FUNCTION,
            'return': TokenType.RETURN,
            'let': TokenType.LET,
            'const': TokenType.CONST,
            'true': TokenType.BOOLEAN,
            'false': TokenType.BOOLEAN,
            'and': TokenType.AND,
            'or': TokenType.OR,
            'not': TokenType.NOT,
        }
        
        # Operator patterns
        self.token_patterns = [
            (r'\d+(\.\d+)?', TokenType.NUMBER),
            (r'"[^"]*"', TokenType.STRING),
            (r"'[^']*'", TokenType.STRING),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
            (r'==', TokenType.EQUAL),
            (r'!=', TokenType.NOT_EQUAL),
            (r'<=', TokenType.LESS_EQUAL),
            (r'>=', TokenType.GREATER_EQUAL),
            (r'\*\*', TokenType.POWER),
            (r'\+', TokenType.PLUS),
            (r'-', TokenType.MINUS),
            (r'\*', TokenType.MULTIPLY),
            (r'/', TokenType.DIVIDE),
            (r'%', TokenType.MODULO),
            (r'<', TokenType.LESS),
            (r'>', TokenType.GREATER),
            (r'=', TokenType.ASSIGN),
            (r'\(', TokenType.LEFT_PAREN),
            (r'\)', TokenType.RIGHT_PAREN),
            (r'\{', TokenType.LEFT_BRACE),
            (r'\}', TokenType.RIGHT_BRACE),
            (r',', TokenType.COMMA),
            (r';', TokenType.SEMICOLON),
            (r'\n', TokenType.NEWLINE),
        ]
        
        self.compiled_patterns = [(re.compile(pattern), token_type) 
                                 for pattern, token_type in self.token_patterns]
    
    def current_char(self) -> str:
        """Get current character or empty string if at end"""
        if self.position >= len(self.source):
            return ''
        return self.source[self.position]
    
    def peek_char(self, offset: int = 1) -> str:
        """Peek at character ahead"""
        pos = self.position + offset
        if pos >= len(self.source):
            return ''
        return self.source[pos]
    
    def advance(self) -> str:
        """Move to next character and return it"""
        char = self.current_char()
        self.position += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self):
        """Skip whitespace characters except newlines"""
        while self.current_char() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """Skip single-line comments"""
        if self.current_char() == '#':
            while self.current_char() and self.current_char() != '\n':
                self.advance()
    
    def read_number(self) -> Token:
        """Read a number (integer or float)"""
        start_column = self.column
        number_str = ""
        
        while self.current_char().isdigit():
            number_str += self.advance()
        
        # Check for decimal point
        if self.current_char() == '.' and self.peek_char().isdigit():
            number_str += self.advance()  # consume '.'
            while self.current_char().isdigit():
                number_str += self.advance()
        
        return Token(TokenType.NUMBER, number_str, self.line, start_column)
    
    def read_string(self, quote_char: str) -> Token:
        """Read a string literal"""
        start_column = self.column
        string_value = ""
        self.advance()  # consume opening quote
        
        while self.current_char() and self.current_char() != quote_char:
            char = self.advance()
            if char == '\\':  # Handle escape sequences
                next_char = self.advance()
                if next_char == 'n':
                    string_value += '\n'
                elif next_char == 't':
                    string_value += '\t'
                elif next_char == 'r':
                    string_value += '\r'
                elif next_char == '\\':
                    string_value += '\\'
                elif next_char == quote_char:
                    string_value += quote_char
                else:
                    string_value += next_char
            else:
                string_value += char
        
        if self.current_char() == quote_char:
            self.advance()  # consume closing quote
        
        return Token(TokenType.STRING, string_value, self.line, start_column)
    
    def read_identifier(self) -> Token:
        """Read identifier or keyword"""
        start_column = self.column
        identifier = ""
        
        while (self.current_char().isalnum() or 
               self.current_char() == '_'):
            identifier += self.advance()
        
        # Check if it's a keyword
        token_type = self.keywords.get(identifier, TokenType.IDENTIFIER)
        return Token(token_type, identifier, self.line, start_column)
    
    def tokenize(self) -> List[Token]:
        """Convert source code into list of tokens"""
        tokens = []
        
        while self.position < len(self.source):
            self.skip_whitespace()
            self.skip_comment()
            
            if self.position >= len(self.source):
                break
            
            char = self.current_char()
            
            # Numbers
            if char.isdigit():
                tokens.append(self.read_number())
            
            # Strings
            elif char in '"\'':
                tokens.append(self.read_string(char))
            
            # Identifiers and keywords
            elif char.isalpha() or char == '_':
                tokens.append(self.read_identifier())
            
            # Try pattern matching for operators and punctuation
            else:
                matched = False
                remaining_source = self.source[self.position:]
                
                for pattern, token_type in self.compiled_patterns:
                    match = pattern.match(remaining_source)
                    if match:
                        value = match.group()
                        tokens.append(Token(token_type, value, self.line, self.column))
                        
                        # Advance position by length of matched text
                        for _ in range(len(value)):
                            self.advance()
                        
                        matched = True
                        break
                
                if not matched:
                    # Unknown character, skip it or raise error
                    print(f"Warning: Unknown character '{char}' at line {self.line}, column {self.column}")
                    self.advance()
        
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
```

### Step 2: Abstract Syntax Tree Nodes

Define the AST node types for different language constructs.

```python
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict

class ASTNode(ABC):
    """Base class for all AST nodes"""
    @abstractmethod
    def accept(self, visitor):
        pass

# Expressions (have values)
class Expression(ASTNode):
    pass

class Literal(Expression):
    def __init__(self, value: Any):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_literal(self)

class Identifier(Expression):
    def __init__(self, name: str):
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_identifier(self)

class BinaryOp(Expression):
    def __init__(self, left: Expression, operator: Token, right: Expression):
        self.left = left
        self.operator = operator
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_binary_op(self)

class UnaryOp(Expression):
    def __init__(self, operator: Token, operand: Expression):
        self.operator = operator
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_unary_op(self)

class FunctionCall(Expression):
    def __init__(self, callee: Expression, arguments: List[Expression]):
        self.callee = callee
        self.arguments = arguments
    
    def accept(self, visitor):
        return visitor.visit_function_call(self)

# Statements (perform actions)
class Statement(ASTNode):
    pass

class ExpressionStatement(Statement):
    def __init__(self, expression: Expression):
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_expression_statement(self)

class Assignment(Statement):
    def __init__(self, name: Token, value: Expression):
        self.name = name
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_assignment(self)

class Block(Statement):
    def __init__(self, statements: List[Statement]):
        self.statements = statements
    
    def accept(self, visitor):
        return visitor.visit_block(self)

class IfStatement(Statement):
    def __init__(self, condition: Expression, then_branch: Statement, 
                 else_branch: Optional[Statement] = None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
    
    def accept(self, visitor):
        return visitor.visit_if_statement(self)

class WhileStatement(Statement):
    def __init__(self, condition: Expression, body: Statement):
        self.condition = condition
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_while_statement(self)

class FunctionDeclaration(Statement):
    def __init__(self, name: Token, parameters: List[Token], body: List[Statement]):
        self.name = name
        self.parameters = parameters
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_function_declaration(self)

class ReturnStatement(Statement):
    def __init__(self, value: Optional[Expression] = None):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_return_statement(self)

class Program(ASTNode):
    def __init__(self, statements: List[Statement]):
        self.statements = statements
    
    def accept(self, visitor):
        return visitor.visit_program(self)
```

### Step 3: Recursive Descent Parser

Build a parser that constructs AST from tokens.

```python
from typing import List, Optional, Union

class ParseError(Exception):
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message
        super().__init__(f"Line {token.line}: {message}")

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
    
    def current_token(self) -> Token:
        """Get current token"""
        if self.current >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.current]
    
    def previous_token(self) -> Token:
        """Get previous token"""
        return self.tokens[self.current - 1]
    
    def advance(self) -> Token:
        """Consume current token and return it"""
        if not self.is_at_end():
            self.current += 1
        return self.previous_token()
    
    def is_at_end(self) -> bool:
        """Check if at end of token stream"""
        return self.current_token().type == TokenType.EOF
    
    def check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type"""
        if self.is_at_end():
            return False
        return self.current_token().type == token_type
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types"""
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of expected type or raise error"""
        if self.check(token_type):
            return self.advance()
        
        current = self.current_token()
        raise ParseError(current, message)
    
    def synchronize(self):
        """Skip tokens until we find a statement boundary"""
        self.advance()
        
        while not self.is_at_end():
            if self.previous_token().type == TokenType.SEMICOLON:
                return
            
            if self.current_token().type in [TokenType.IF, TokenType.FOR, 
                                           TokenType.WHILE, TokenType.FUNCTION,
                                           TokenType.LET, TokenType.RETURN]:
                return
            
            self.advance()
    
    def parse(self) -> Program:
        """Parse tokens into AST"""
        statements = []
        
        while not self.is_at_end():
            try:
                if self.match(TokenType.NEWLINE):
                    continue  # Skip newlines
                    
                stmt = self.declaration()
                if stmt:
                    statements.append(stmt)
            except ParseError as error:
                print(f"Parse error: {error}")
                self.synchronize()
        
        return Program(statements)
    
    def declaration(self) -> Optional[Statement]:
        """Parse declarations (variables, functions)"""
        try:
            if self.match(TokenType.FUNCTION):
                return self.function_declaration()
            if self.match(TokenType.LET, TokenType.CONST):
                return self.variable_declaration()
            
            return self.statement()
        
        except ParseError:
            self.synchronize()
            return None
    
    def function_declaration(self) -> FunctionDeclaration:
        """Parse function declaration"""
        name = self.consume(TokenType.IDENTIFIER, "Expected function name")
        
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after function name")
        
        parameters = []
        if not self.check(TokenType.RIGHT_PAREN):
            parameters.append(self.consume(TokenType.IDENTIFIER, 
                                         "Expected parameter name"))
            while self.match(TokenType.COMMA):
                parameters.append(self.consume(TokenType.IDENTIFIER, 
                                             "Expected parameter name"))
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body")
        
        body = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            stmt = self.declaration()
            if stmt:
                body.append(stmt)
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after function body")
        
        return FunctionDeclaration(name, parameters, body)
    
    def variable_declaration(self) -> Assignment:
        """Parse variable declaration"""
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        
        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.expression()
        
        if initializer is None:
            # Default to null/undefined
            initializer = Literal(None)
        
        return Assignment(name, initializer)
    
    def statement(self) -> Statement:
        """Parse statements"""
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        
        return self.expression_statement()
    
    def if_statement(self) -> IfStatement:
        """Parse if statement"""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after if condition")
        
        then_branch = self.statement()
        else_branch = None
        
        if self.match(TokenType.ELSE):
            else_branch = self.statement()
        
        return IfStatement(condition, then_branch, else_branch)
    
    def while_statement(self) -> WhileStatement:
        """Parse while statement"""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after while condition")
        
        body = self.statement()
        return WhileStatement(condition, body)
    
    def return_statement(self) -> ReturnStatement:
        """Parse return statement"""
        value = None
        if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.NEWLINE):
            value = self.expression()
        
        return ReturnStatement(value)
    
    def block(self) -> List[Statement]:
        """Parse block of statements"""
        statements = []
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after block")
        return statements
    
    def expression_statement(self) -> Statement:
        """Parse expression statement"""
        expr = self.expression()
        
        # Check for assignment
        if isinstance(expr, Identifier) and self.match(TokenType.ASSIGN):
            value = self.expression()
            return Assignment(Token(TokenType.IDENTIFIER, expr.name, 0, 0), value)
        
        return ExpressionStatement(expr)
    
    # Expression parsing (operator precedence)
    def expression(self) -> Expression:
        """Parse expression"""
        return self.logical_or()
    
    def logical_or(self) -> Expression:
        """Parse logical OR expression"""
        expr = self.logical_and()
        
        while self.match(TokenType.OR):
            operator = self.previous_token()
            right = self.logical_and()
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def logical_and(self) -> Expression:
        """Parse logical AND expression"""
        expr = self.equality()
        
        while self.match(TokenType.AND):
            operator = self.previous_token()
            right = self.equality()
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def equality(self) -> Expression:
        """Parse equality expression"""
        expr = self.comparison()
        
        while self.match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator = self.previous_token()
            right = self.comparison()
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def comparison(self) -> Expression:
        """Parse comparison expression"""
        expr = self.term()
        
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                         TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous_token()
            right = self.term()
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def term(self) -> Expression:
        """Parse addition and subtraction"""
        expr = self.factor()
        
        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous_token()
            right = self.factor()
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def factor(self) -> Expression:
        """Parse multiplication and division"""
        expr = self.power()
        
        while self.match(TokenType.DIVIDE, TokenType.MULTIPLY, TokenType.MODULO):
            operator = self.previous_token()
            right = self.power()
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def power(self) -> Expression:
        """Parse power expression (right associative)"""
        expr = self.unary()
        
        if self.match(TokenType.POWER):
            operator = self.previous_token()
            right = self.power()  # Right associative
            expr = BinaryOp(expr, operator, right)
        
        return expr
    
    def unary(self) -> Expression:
        """Parse unary expressions"""
        if self.match(TokenType.NOT, TokenType.MINUS):
            operator = self.previous_token()
            right = self.unary()
            return UnaryOp(operator, right)
        
        return self.call()
    
    def call(self) -> Expression:
        """Parse function calls"""
        expr = self.primary()
        
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            else:
                break
        
        return expr
    
    def finish_call(self, callee: Expression) -> FunctionCall:
        """Parse function call arguments"""
        arguments = []
        
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                arguments.append(self.expression())
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
        return FunctionCall(callee, arguments)
    
    def primary(self) -> Expression:
        """Parse primary expressions"""
        if self.match(TokenType.BOOLEAN):
            value = self.previous_token().value == "true"
            return Literal(value)
        
        if self.match(TokenType.NUMBER):
            value = self.previous_token().value
            return Literal(float(value) if '.' in value else int(value))
        
        if self.match(TokenType.STRING):
            return Literal(self.previous_token().value)
        
        if self.match(TokenType.IDENTIFIER):
            return Identifier(self.previous_token().value)
        
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return expr
        
        raise ParseError(self.current_token(), "Expected expression")
```

### Step 4: Environment and Scoping

Implement variable and function scoping.

```python
from typing import Any, Dict, Optional

class Environment:
    def __init__(self, enclosing: Optional['Environment'] = None):
        self.enclosing = enclosing
        self.values: Dict[str, Any] = {}
    
    def define(self, name: str, value: Any):
        """Define a variable in current scope"""
        self.values[name] = value
    
    def get(self, name: str) -> Any:
        """Get variable value, checking parent scopes"""
        if name in self.values:
            return self.values[name]
        
        if self.enclosing:
            return self.enclosing.get(name)
        
        raise RuntimeError(f"Undefined variable '{name}'")
    
    def assign(self, name: str, value: Any):
        """Assign to existing variable"""
        if name in self.values:
            self.values[name] = value
            return
        
        if self.enclosing:
            self.enclosing.assign(name, value)
            return
        
        raise RuntimeError(f"Undefined variable '{name}'")

class Function:
    def __init__(self, declaration: FunctionDeclaration, closure: Environment):
        self.declaration = declaration
        self.closure = closure  # Lexical scoping
    
    def call(self, interpreter, arguments: List[Any]) -> Any:
        # Create new environment for function execution
        environment = Environment(self.closure)
        
        # Bind parameters to arguments
        for i, param in enumerate(self.declaration.parameters):
            if i < len(arguments):
                environment.define(param.value, arguments[i])
            else:
                environment.define(param.value, None)  # Default value
        
        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as return_value:
            return return_value.value
        
        return None  # Functions return None by default

class ReturnException(Exception):
    """Exception used to implement return statements"""
    def __init__(self, value: Any):
        self.value = value
        super().__init__()
```

### Step 5: Interpreter/Evaluator

Implement the visitor pattern to execute AST nodes.

```python
import operator
from typing import Any, List

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        
        # Built-in functions
        self.define_built_ins()
    
    def define_built_ins(self):
        """Define built-in functions"""
        def builtin_print(*args):
            output = " ".join(str(arg) for arg in args)
            print(output)
            return None
        
        def builtin_input(prompt=""):
            return input(str(prompt))
        
        def builtin_len(obj):
            if isinstance(obj, str):
                return len(obj)
            elif isinstance(obj, list):
                return len(obj)
            else:
                raise RuntimeError("len() requires string or list")
        
        def builtin_str(obj):
            return str(obj)
        
        def builtin_int(obj):
            try:
                return int(obj)
            except ValueError:
                raise RuntimeError(f"Cannot convert {obj} to integer")
        
        def builtin_float(obj):
            try:
                return float(obj)
            except ValueError:
                raise RuntimeError(f"Cannot convert {obj} to float")
        
        # Register built-ins
        self.globals.define("print", builtin_print)
        self.globals.define("input", builtin_input)
        self.globals.define("len", builtin_len)
        self.globals.define("str", builtin_str)
        self.globals.define("int", builtin_int)
        self.globals.define("float", builtin_float)
    
    def interpret(self, program: Program) -> Any:
        """Interpret a program"""
        try:
            return self.visit_program(program)
        except RuntimeError as error:
            print(f"Runtime error: {error}")
            return None
    
    def visit_program(self, program: Program) -> Any:
        """Execute program statements"""
        result = None
        for statement in program.statements:
            result = statement.accept(self)
        return result
    
    def visit_literal(self, literal: Literal) -> Any:
        return literal.value
    
    def visit_identifier(self, identifier: Identifier) -> Any:
        return self.environment.get(identifier.name)
    
    def visit_binary_op(self, binary_op: BinaryOp) -> Any:
        left = binary_op.left.accept(self)
        right = binary_op.right.accept(self)
        
        op_map = {
            TokenType.PLUS: operator.add,
            TokenType.MINUS: operator.sub,
            TokenType.MULTIPLY: operator.mul,
            TokenType.DIVIDE: operator.truediv,
            TokenType.MODULO: operator.mod,
            TokenType.POWER: operator.pow,
            TokenType.EQUAL: operator.eq,
            TokenType.NOT_EQUAL: operator.ne,
            TokenType.LESS: operator.lt,
            TokenType.LESS_EQUAL: operator.le,
            TokenType.GREATER: operator.gt,
            TokenType.GREATER_EQUAL: operator.ge,
        }
        
        op_func = op_map.get(binary_op.operator.type)
        if op_func:
            try:
                return op_func(left, right)
            except Exception as e:
                raise RuntimeError(f"Error in operation: {e}")
        
        # Logical operators
        if binary_op.operator.type == TokenType.AND:
            return self.is_truthy(left) and self.is_truthy(right)
        elif binary_op.operator.type == TokenType.OR:
            return self.is_truthy(left) or self.is_truthy(right)
        
        raise RuntimeError(f"Unknown binary operator: {binary_op.operator.value}")
    
    def visit_unary_op(self, unary_op: UnaryOp) -> Any:
        operand = unary_op.operand.accept(self)
        
        if unary_op.operator.type == TokenType.MINUS:
            if isinstance(operand, (int, float)):
                return -operand
            else:
                raise RuntimeError("Unary minus requires number")
        
        elif unary_op.operator.type == TokenType.NOT:
            return not self.is_truthy(operand)
        
        raise RuntimeError(f"Unknown unary operator: {unary_op.operator.value}")
    
    def visit_function_call(self, func_call: FunctionCall) -> Any:
        callee = func_call.callee.accept(self)
        
        arguments = []
        for arg in func_call.arguments:
            arguments.append(arg.accept(self))
        
        if callable(callee):
            # Built-in function
            try:
                return callee(*arguments)
            except Exception as e:
                raise RuntimeError(f"Error calling function: {e}")
        elif isinstance(callee, Function):
            # User-defined function
            if len(arguments) != len(callee.declaration.parameters):
                raise RuntimeError(f"Expected {len(callee.declaration.parameters)} arguments but got {len(arguments)}")
            return callee.call(self, arguments)
        else:
            raise RuntimeError("Only functions can be called")
    
    def visit_expression_statement(self, expr_stmt: ExpressionStatement) -> Any:
        return expr_stmt.expression.accept(self)
    
    def visit_assignment(self, assignment: Assignment) -> Any:
        value = assignment.value.accept(self)
        
        # Check if variable exists (for assignment)
        try:
            self.environment.assign(assignment.name.value, value)
        except RuntimeError:
            # Variable doesn't exist, define it
            self.environment.define(assignment.name.value, value)
        
        return value
    
    def visit_block(self, block: Block) -> Any:
        return self.execute_block(block.statements, Environment(self.environment))
    
    def execute_block(self, statements: List[Statement], environment: Environment) -> Any:
        """Execute block with new environment"""
        previous = self.environment
        result = None
        
        try:
            self.environment = environment
            
            for statement in statements:
                result = statement.accept(self)
        finally:
            self.environment = previous
        
        return result
    
    def visit_if_statement(self, if_stmt: IfStatement) -> Any:
        condition_value = if_stmt.condition.accept(self)
        
        if self.is_truthy(condition_value):
            return if_stmt.then_branch.accept(self)
        elif if_stmt.else_branch:
            return if_stmt.else_branch.accept(self)
        
        return None
    
    def visit_while_statement(self, while_stmt: WhileStatement) -> Any:
        result = None
        while self.is_truthy(while_stmt.condition.accept(self)):
            result = while_stmt.body.accept(self)
        return result
    
    def visit_function_declaration(self, func_decl: FunctionDeclaration) -> Any:
        function = Function(func_decl, self.environment)
        self.environment.define(func_decl.name.value, function)
        return None
    
    def visit_return_statement(self, return_stmt: ReturnStatement) -> Any:
        value = None
        if return_stmt.value:
            value = return_stmt.value.accept(self)
        
        raise ReturnException(value)
    
    def is_truthy(self, obj: Any) -> bool:
        """Determine if object is truthy"""
        if obj is None:
            return False
        if isinstance(obj, bool):
            return obj
        return True

# Example usage
def run_interpreter(source_code: str):
    """Run interpreter on source code"""
    try:
        # Lexical analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        
        # Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Interpretation
        interpreter = Interpreter()
        result = interpreter.interpret(ast)
        
        return result
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test the interpreter
if __name__ == "__main__":
    test_code = """
    let x = 10
    let y = 20
    
    function add(a, b) {
        return a + b
    }
    
    function factorial(n) {
        if (n <= 1) {
            return 1
        } else {
            return n * factorial(n - 1)
        }
    }
    
    print("x =", x)
    print("y =", y)
    print("x + y =", add(x, y))
    print("factorial(5) =", factorial(5))
    
    let i = 1
    while (i <= 3) {
        print("i =", i)
        i = i + 1
    }
    """
    
    run_interpreter(test_code)
```

## 📚 Tutorials by Language

### Python
- **[Let's Build A Simple Interpreter](https://ruslanspivak.com/lsbasi-part1/)** - Comprehensive series on building interpreters
- **[Crafting Interpreters](https://craftinginterpreters.com/)** - Complete book on language implementation
- **[Build Your Own Lisp in Python](http://norvig.com/lispy.html)** - Peter Norvig's Lisp interpreter
- **[Writing a Language in Python](https://blog.usejournal.com/writing-your-own-programming-language-and-compiler-with-python-a468970ae6df)** - Modern Python tutorial

### JavaScript
- **[The Super Tiny Compiler](https://github.com/jamiebuilds/the-super-tiny-compiler)** - Minimal compiler tutorial
- **[Build a JavaScript Interpreter](https://lisperator.net/pltut/)** - JavaScript interpreter tutorial
- **[Writing an Interpreter in JavaScript](https://www.freecodecamp.org/news/the-programming-language-pipeline-91d3f449c919/)** - Step-by-step guide

### Go
- **[Writing An Interpreter In Go](https://interpreterbook.com/)** - Complete Go interpreter book
- **[Monkey Language](https://github.com/skx/monkey)** - Go interpreter implementation
- **[Build a Programming Language](https://medium.com/@bnoordhuis/writing-a-programming-language-in-go-6cd11e8d3b1a)** - Go language tutorial

### C
- **[Build Your Own Lisp](http://www.buildyourownlisp.com/)** - C implementation tutorial
- **[Crafting Interpreters (C)](https://craftinginterpreters.com/a-bytecode-virtual-machine.html)** - C virtual machine implementation
- **[Simple C Interpreter](https://github.com/lotabout/write-a-C-interpreter)** - C interpreter for C subset

### Java
- **[Java Interpreter Tutorial](https://www.baeldung.com/java-interpreter-pattern)** - Interpreter pattern in Java
- **[Building a Simple Programming Language](https://medium.com/@rahul77349/building-a-simple-programming-language-interpreter-in-java-22b5d8b8b816)** - Java implementation

### Rust
- **[Rust Interpreter](https://github.com/rust-lang/rust/tree/master/src/librustc_mir/interpret)** - Understanding Rust's interpreter
- **[Build a Language with Rust](https://createlang.rs/)** - Rust language implementation tutorial

### C++
- **[C++ Interpreter Development](https://www.codeproject.com/Articles/11191/How-to-build-your-own-C-interpreter)** - C++ interpreter tutorial
- **[Expression Evaluator](https://www.strchr.com/expression_evaluator)** - C++ expression parsing

### Haskell
- **[Write Yourself a Scheme](https://en.wikibooks.org/wiki/Write_Yourself_a_Scheme_in_48_Hours)** - Haskell Scheme interpreter
- **[Functional Language Implementation](https://github.com/sdiehl/write-you-a-haskell)** - Haskell language tutorial

## 🏗️ Project Ideas

### Beginner Projects
1. **Calculator Language** - Mathematical expression evaluator
2. **Simple Scripting Language** - Variables and basic operations  
3. **Logo Turtle Graphics** - Simple graphics programming language

### Intermediate Projects
1. **Functional Language** - Lambda calculus-based language
2. **Object-Oriented Language** - Classes and inheritance
3. **Stack-Based Language** - Forth-like stack operations

### Advanced Projects
1. **Lisp Interpreter** - Fully functional Lisp implementation
2. **Prolog Engine** - Logic programming language
3. **SQL Query Engine** - Database query language interpreter

## ⚙️ Core Concepts

### Parsing Techniques
- **Recursive Descent**: Top-down parsing with recursive functions
- **LR Parsing**: Bottom-up shift-reduce parsing
- **Parser Combinators**: Compositional parsing approach
- **PEG Parsing**: Parsing Expression Grammar technique

### AST Design
- **Visitor Pattern**: Separating operations from data structure
- **Node Types**: Expression vs statement distinction
- **Tree Walking**: Depth-first traversal strategies
- **AST Optimization**: Constant folding and dead code elimination

### Runtime Systems
- **Environment Chains**: Lexical scoping implementation
- **Call Stack**: Function call management
- **Memory Management**: Variable lifetime tracking
- **Error Handling**: Exception propagation and recovery

## 🚀 Performance Optimization

### Parsing Optimization
- **Memoization**: Caching parse results
- **Left Recursion**: Elimination techniques
- **Look-ahead**: Reducing backtracking
- **Error Recovery**: Graceful failure handling

### Execution Optimization
- **Tail Call Optimization**: Converting recursion to iteration
- **Constant Folding**: Compile-time expression evaluation
- **Variable Hoisting**: Scope analysis optimization
- **Inline Expansion**: Function call elimination

### Advanced Techniques
- **Bytecode Generation**: Intermediate representation
- **Just-In-Time Compilation**: Runtime optimization
- **Garbage Collection**: Automatic memory management
- **Profile-Guided Optimization**: Runtime feedback

## 🧪 Testing Strategies

### Unit Testing
- **Lexer Tests**: Token generation verification
- **Parser Tests**: AST construction validation
- **Evaluator Tests**: Expression evaluation correctness
- **Environment Tests**: Scoping behavior verification

### Integration Testing
- **End-to-End Programs**: Complete language feature testing
- **Error Handling**: Exception and error message validation
- **Performance Tests**: Execution speed benchmarking
- **Memory Tests**: Resource usage monitoring

### Language Testing
- **Syntax Validation**: Valid and invalid program testing
- **Semantic Analysis**: Type checking and scope validation
- **Runtime Behavior**: Program execution correctness
- **Edge Cases**: Boundary condition testing

## 🔗 Additional Resources

### Books
- [Crafting Interpreters](https://craftinginterpreters.com/) - Complete interpreter implementation guide
- [Programming Language Pragmatics](https://www.cs.rochester.edu/~scott/pragmatics/) - Language design principles
- [Types and Programming Languages](https://www.cis.upenn.edu/~bcpierce/tapl/) - Type system theory
- [Structure and Interpretation of Computer Programs](https://mitpress.mit.edu/sites/default/files/sicp/index.html) - Classic CS textbook

### Online Resources
- [Programming Languages: Application and Interpretation](http://papl.cs.brown.edu/2020/) - Brown University course
- [Language Implementation Patterns](https://pragprog.com/titles/tpdsl/language-implementation-patterns/) - Practical techniques
- [Dragon Book](https://suif.stanford.edu/dragonbook/) - Compiler design classic
- [Modern Compiler Implementation](https://www.cs.princeton.edu/~appel/modern/) - Advanced compiler techniques

### Development Communities
- [/r/ProgrammingLanguages](https://www.reddit.com/r/ProgrammingLanguages/) - Language design discussions
- [Language Design Stack Exchange](https://cs.stackexchange.com/questions/tagged/programming-languages) - Q&A community
- [LLVM Community](https://llvm.org/community/) - Compiler infrastructure project
- [Programming Language Theory](https://github.com/steshaw/plt) - Theory and implementation resources

---

**Ready to interpret?** Start with a simple expression evaluator and build up to a full programming language!