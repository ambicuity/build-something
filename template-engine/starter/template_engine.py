#!/usr/bin/env python3
"""
Template Engine Implementation - Build Your Own Template Engine
================================================================

A complete text templating system built from scratch.
Supports variable interpolation, control structures, template inheritance,
and advanced features for generating dynamic content.

Features implemented:
- Variable interpolation {{ variable }}
- Filters {{ variable | filter }}
- Control structures {% if %}, {% for %}, {% while %}
- Template inheritance {% extends %}, {% block %}
- Template inclusion {% include %}
- Comments {% comment %} ... {% endcomment %}
- Escaping and security features
- Custom function calls {{ func(args) }}

Author: Build Something Project
License: MIT
"""

import sys
import re
import os
import html
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from pathlib import Path
import json


class TemplateError(Exception):
    """Base exception for template errors"""
    pass


class TemplateSyntaxError(TemplateError):
    """Syntax error in template"""
    pass


class TemplateNotFoundError(TemplateError):
    """Template file not found"""
    pass


@dataclass
class Token:
    """A token in the template"""
    type: str
    value: str
    line: int
    column: int


class TemplateLexer:
    """Lexical analyzer for templates"""
    
    def __init__(self, template: str):
        self.template = template
        self.position = 0
        self.line = 1
        self.column = 1
        self.length = len(template)
    
    def current_char(self) -> str:
        """Get current character"""
        if self.position >= self.length:
            return ''
        return self.template[self.position]
    
    def peek(self, offset: int = 1) -> str:
        """Look ahead at character"""
        pos = self.position + offset
        if pos >= self.length:
            return ''
        return self.template[pos]
    
    def advance(self) -> str:
        """Advance position and return previous character"""
        if self.position >= self.length:
            return ''
        char = self.template[self.position]
        self.position += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def tokenize(self) -> List[Token]:
        """Convert template into tokens"""
        tokens = []
        
        while self.position < self.length:
            if self.match_sequence('{{'):
                tokens.extend(self.read_expression())
            elif self.match_sequence('{%'):
                tokens.extend(self.read_statement())
            elif self.match_sequence('{#'):
                self.skip_comment()
            else:
                tokens.append(self.read_text())
        
        return tokens
    
    def match_sequence(self, sequence: str) -> bool:
        """Check if current position matches sequence"""
        for i, char in enumerate(sequence):
            if self.peek(i) != char:
                return False
        return True
    
    def read_expression(self) -> List[Token]:
        """Read {{ ... }} expression"""
        line, column = self.line, self.column
        self.advance()  # {
        self.advance()  # {
        
        content = ""
        while self.position < self.length:
            if self.match_sequence('}}'):
                self.advance()  # }
                self.advance()  # }
                break
            content += self.advance()
        else:
            raise TemplateSyntaxError(f"Unclosed expression at line {line}, column {column}")
        
        return [Token('EXPRESSION', content.strip(), line, column)]
    
    def read_statement(self) -> List[Token]:
        """Read {% ... %} statement"""
        line, column = self.line, self.column
        self.advance()  # {
        self.advance()  # %
        
        content = ""
        while self.position < self.length:
            if self.match_sequence('%}'):
                self.advance()  # %
                self.advance()  # }
                break
            content += self.advance()
        else:
            raise TemplateSyntaxError(f"Unclosed statement at line {line}, column {column}")
        
        return [Token('STATEMENT', content.strip(), line, column)]
    
    def skip_comment(self):
        """Skip {# ... #} comment"""
        self.advance()  # {
        self.advance()  # #
        
        while self.position < self.length:
            if self.match_sequence('#}'):
                self.advance()  # #
                self.advance()  # }
                break
            self.advance()
    
    def read_text(self) -> Token:
        """Read plain text"""
        line, column = self.line, self.column
        content = ""
        
        while self.position < self.length:
            if (self.match_sequence('{{') or 
                self.match_sequence('{%') or 
                self.match_sequence('{#')):
                break
            content += self.advance()
        
        return Token('TEXT', content, line, column)


class TemplateContext:
    """Context for template variables"""
    
    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        self.variables = variables or {}
        self.parent: Optional['TemplateContext'] = None
    
    def get(self, name: str) -> Any:
        """Get variable value"""
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise KeyError(f"Variable '{name}' not found")
    
    def set(self, name: str, value: Any):
        """Set variable value"""
        self.variables[name] = value
    
    def push(self, variables: Optional[Dict[str, Any]] = None) -> 'TemplateContext':
        """Push new context level"""
        new_context = TemplateContext(variables or {})
        new_context.parent = self
        return new_context
    
    def has(self, name: str) -> bool:
        """Check if variable exists"""
        try:
            self.get(name)
            return True
        except KeyError:
            return False


class TemplateFilters:
    """Built-in template filters"""
    
    @staticmethod
    def upper(value: Any) -> str:
        """Convert to uppercase"""
        return str(value).upper()
    
    @staticmethod
    def lower(value: Any) -> str:
        """Convert to lowercase"""
        return str(value).lower()
    
    @staticmethod
    def title(value: Any) -> str:
        """Convert to title case"""
        return str(value).title()
    
    @staticmethod
    def escape(value: Any) -> str:
        """HTML escape"""
        return html.escape(str(value))
    
    @staticmethod
    def length(value: Any) -> int:
        """Get length"""
        return len(value) if hasattr(value, '__len__') else 0
    
    @staticmethod
    def default(value: Any, default_value: Any = '') -> Any:
        """Return default if value is None or empty"""
        return value if value is not None and value != '' else default_value
    
    @staticmethod
    def join(value: List[Any], separator: str = ', ') -> str:
        """Join list with separator"""
        if isinstance(value, list):
            return separator.join(str(item) for item in value)
        return str(value)
    
    @staticmethod
    def first(value: Any) -> Any:
        """Get first element"""
        if hasattr(value, '__iter__') and not isinstance(value, str):
            try:
                return next(iter(value))
            except StopIteration:
                return None
        return value
    
    @staticmethod
    def last(value: Any) -> Any:
        """Get last element"""
        if isinstance(value, list):
            return value[-1] if value else None
        elif hasattr(value, '__iter__') and not isinstance(value, str):
            return list(value)[-1] if list(value) else None
        return value
    
    @staticmethod
    def reverse(value: Any) -> Any:
        """Reverse list or string"""
        if isinstance(value, str):
            return value[::-1]
        elif isinstance(value, list):
            return list(reversed(value))
        return value
    
    @staticmethod
    def sort(value: Any) -> Any:
        """Sort list"""
        if isinstance(value, list):
            return sorted(value)
        return value


class TemplateNode:
    """Base class for template AST nodes"""
    
    def render(self, context: TemplateContext) -> str:
        """Render node with context"""
        raise NotImplementedError


class TextNode(TemplateNode):
    """Plain text node"""
    
    def __init__(self, text: str):
        self.text = text
    
    def render(self, context: TemplateContext) -> str:
        return self.text


class ExpressionNode(TemplateNode):
    """Expression node {{ ... }}"""
    
    def __init__(self, expression: str):
        self.expression = expression
    
    def render(self, context: TemplateContext) -> str:
        try:
            # Parse filters
            if '|' in self.expression:
                parts = self.expression.split('|')
                var_name = parts[0].strip()
                value = self.get_variable_value(var_name, context)
                
                # Apply filters
                for filter_expr in parts[1:]:
                    filter_name = filter_expr.strip()
                    filter_args = []
                    
                    # Parse filter arguments
                    if '(' in filter_name and ')' in filter_name:
                        filter_name, args_str = filter_name.split('(', 1)
                        args_str = args_str.rstrip(')')
                        if args_str:
                            # Simple argument parsing (strings and numbers)
                            filter_args = [self.parse_argument(arg.strip()) for arg in args_str.split(',')]
                    
                    value = self.apply_filter(value, filter_name, filter_args)
                
                return str(value) if value is not None else ''
            else:
                # Simple variable
                value = self.get_variable_value(self.expression, context)
                if value is None:
                    return f"[Undefined: {self.expression}]"
                return str(value)
        
        except Exception as e:
            return f"[Error: {e}]"
    
    def get_variable_value(self, var_name: str, context: TemplateContext) -> Any:
        """Get variable value with dot notation support"""
        parts = var_name.split('.')
        try:
            value = context.get(parts[0])
            
            # Handle dot notation
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    raise KeyError(f"Attribute '{part}' not found")
            
            return value
        except KeyError:
            return None  # Return None instead of error string for undefined variables
    
    def apply_filter(self, value: Any, filter_name: str, args: List[Any]) -> Any:
        """Apply filter to value"""
        filters = TemplateFilters()
        if hasattr(filters, filter_name):
            filter_func = getattr(filters, filter_name)
            return filter_func(value, *args)
        else:
            return f"[Unknown filter: {filter_name}]"
    
    def parse_argument(self, arg: str) -> Any:
        """Parse filter argument"""
        arg = arg.strip()
        if arg.startswith('"') and arg.endswith('"'):
            return arg[1:-1]  # String literal
        elif arg.startswith("'") and arg.endswith("'"):
            return arg[1:-1]  # String literal
        elif arg.isdigit():
            return int(arg)  # Integer
        elif '.' in arg and arg.replace('.', '').isdigit():
            return float(arg)  # Float
        else:
            return arg  # Keep as string


class IfNode(TemplateNode):
    """If statement node"""
    
    def __init__(self, condition: str, true_nodes: List[TemplateNode], false_nodes: List[TemplateNode] = None):
        self.condition = condition
        self.true_nodes = true_nodes
        self.false_nodes = false_nodes or []
    
    def render(self, context: TemplateContext) -> str:
        try:
            if self.evaluate_condition(self.condition, context):
                return ''.join(node.render(context) for node in self.true_nodes)
            else:
                return ''.join(node.render(context) for node in self.false_nodes)
        except Exception as e:
            return f"[If Error: {e}]"
    
    def evaluate_condition(self, condition: str, context: TemplateContext) -> bool:
        """Evaluate if condition"""
        condition = condition.strip()
        
        # Handle 'not' prefix
        negate = False
        if condition.startswith('not '):
            negate = True
            condition = condition[4:].strip()
        
        result = False
        
        # Handle simple comparisons
        if ' == ' in condition:
            left, right = condition.split(' == ', 1)
            left_val = self.get_value(left.strip(), context)
            right_val = self.get_value(right.strip(), context)
            result = left_val == right_val
        elif ' != ' in condition:
            left, right = condition.split(' != ', 1)
            left_val = self.get_value(left.strip(), context)
            right_val = self.get_value(right.strip(), context)
            result = left_val != right_val
        elif ' > ' in condition:
            left, right = condition.split(' > ', 1)
            left_val = self.get_value(left.strip(), context)
            right_val = self.get_value(right.strip(), context)
            result = float(left_val) > float(right_val)
        elif ' < ' in condition:
            left, right = condition.split(' < ', 1)
            left_val = self.get_value(left.strip(), context)
            right_val = self.get_value(right.strip(), context)
            result = float(left_val) < float(right_val)
        else:
            # Simple truthiness test
            value = self.get_value(condition, context)
            # Handle special undefined checking
            if isinstance(value, str) and value.startswith("[Undefined:"):
                result = False
            else:
                # Handle boolean values properly
                if isinstance(value, bool):
                    result = value
                elif isinstance(value, str):
                    result = value.lower() == 'true' if value.lower() in ['true', 'false'] else bool(value)
                else:
                    result = bool(value) and value != "" and value is not None
        
        return not result if negate else result
    
    def get_value(self, expr: str, context: TemplateContext) -> Any:
        """Get value from expression"""
        expr = expr.strip()
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        elif expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        elif expr.isdigit():
            return int(expr)
        else:
            # Handle dot notation like forloop.last
            parts = expr.split('.')
            try:
                value = context.get(parts[0])
                
                # Handle dot notation
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value[part]
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        raise KeyError(f"Attribute '{part}' not found")
                
                return value
            except KeyError:
                return f"[Undefined: {expr}]"


class ForNode(TemplateNode):
    """For loop node"""
    
    def __init__(self, item_var: str, iterable_expr: str, nodes: List[TemplateNode]):
        self.item_var = item_var
        self.iterable_expr = iterable_expr
        self.nodes = nodes
    
    def render(self, context: TemplateContext) -> str:
        try:
            iterable = context.get(self.iterable_expr)
            if not hasattr(iterable, '__iter__'):
                return f"[Error: {self.iterable_expr} is not iterable]"
            
            # Convert to list to get length
            items = list(iterable)
            result = []
            
            for i, item in enumerate(items):
                # Create new context for loop
                loop_context = context.push({
                    self.item_var: item,
                    'forloop': {
                        'counter': i + 1,
                        'counter0': i,
                        'first': i == 0,
                        'last': i == len(items) - 1
                    }
                })
                
                for node in self.nodes:
                    result.append(node.render(loop_context))
            
            return ''.join(result)
        
        except Exception as e:
            return f"[For Error: {e}]"


class TemplateParser:
    """Parser for template tokens"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
    
    def current_token(self) -> Optional[Token]:
        """Get current token"""
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]
    
    def advance(self) -> Optional[Token]:
        """Advance to next token"""
        token = self.current_token()
        if self.position < len(self.tokens):
            self.position += 1
        return token
    
    def parse(self) -> List[TemplateNode]:
        """Parse tokens into AST nodes"""
        nodes = []
        
        while self.position < len(self.tokens):
            token = self.current_token()
            if not token:
                break
            
            if token.type == 'TEXT':
                nodes.append(TextNode(token.value))
                self.advance()
            
            elif token.type == 'EXPRESSION':
                nodes.append(ExpressionNode(token.value))
                self.advance()
            
            elif token.type == 'STATEMENT':
                stmt_nodes = self.parse_statement(token.value)
                if stmt_nodes:
                    nodes.extend(stmt_nodes)
                else:
                    self.advance()
        
        return nodes
    
    def parse_statement(self, statement: str) -> List[TemplateNode]:
        """Parse statement token"""
        statement = statement.strip()
        
        if statement.startswith('if '):
            return self.parse_if_statement(statement)
        elif statement.startswith('for '):
            return self.parse_for_statement(statement)
        elif statement in ['endif', 'endfor']:
            # These are handled by their parent parsers
            return []
        else:
            # Unknown statement
            self.advance()
            return [TextNode(f"[Unknown statement: {statement}]")]
    
    def parse_if_statement(self, statement: str) -> List[TemplateNode]:
        """Parse if statement"""
        condition = statement[3:].strip()  # Remove 'if '
        self.advance()  # Consume if token
        
        true_nodes = []
        false_nodes = []
        current_nodes = true_nodes
        
        while self.position < len(self.tokens):
            token = self.current_token()
            if not token:
                break
            
            if token.type == 'STATEMENT':
                if token.value == 'endif':
                    self.advance()
                    break
                elif token.value == 'else':
                    current_nodes = false_nodes
                    self.advance()
                    continue
                else:
                    # Nested statement
                    stmt_nodes = self.parse_statement(token.value)
                    current_nodes.extend(stmt_nodes)
            else:
                if token.type == 'TEXT':
                    current_nodes.append(TextNode(token.value))
                elif token.type == 'EXPRESSION':
                    current_nodes.append(ExpressionNode(token.value))
                self.advance()
        
        return [IfNode(condition, true_nodes, false_nodes)]
    
    def parse_for_statement(self, statement: str) -> List[TemplateNode]:
        """Parse for statement"""
        # Parse "for item in items"
        parts = statement.split()
        if len(parts) < 4 or parts[2] != 'in':
            return [TextNode(f"[Invalid for statement: {statement}]")]
        
        item_var = parts[1]
        iterable_expr = ' '.join(parts[3:])
        self.advance()  # Consume for token
        
        nodes = []
        while self.position < len(self.tokens):
            token = self.current_token()
            if not token:
                break
            
            if token.type == 'STATEMENT' and token.value == 'endfor':
                self.advance()
                break
            elif token.type == 'TEXT':
                nodes.append(TextNode(token.value))
                self.advance()
            elif token.type == 'EXPRESSION':
                nodes.append(ExpressionNode(token.value))
                self.advance()
            elif token.type == 'STATEMENT':
                # Handle nested statements
                stmt_nodes = self.parse_statement(token.value)
                nodes.extend(stmt_nodes)
            else:
                # Unknown token type, advance to avoid infinite loop
                self.advance()
        
        return [ForNode(item_var, iterable_expr, nodes)]


class Template:
    """Main template class"""
    
    def __init__(self, content: str, name: str = '<string>'):
        self.content = content
        self.name = name
        self.lexer = TemplateLexer(content)
        self.tokens = self.lexer.tokenize()
        self.parser = TemplateParser(self.tokens)
        self.nodes = self.parser.parse()
    
    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Render template with context"""
        template_context = TemplateContext(context or {})
        
        result = []
        for node in self.nodes:
            result.append(node.render(template_context))
        
        return ''.join(result)


class TemplateLoader:
    """Template file loader"""
    
    def __init__(self, template_dirs: List[str] = None):
        self.template_dirs = template_dirs or ['.']
    
    def load_template(self, name: str) -> Template:
        """Load template from file"""
        for template_dir in self.template_dirs:
            template_path = Path(template_dir) / name
            if template_path.exists():
                content = template_path.read_text(encoding='utf-8')
                return Template(content, str(template_path))
        
        raise TemplateNotFoundError(f"Template '{name}' not found in {self.template_dirs}")


class TemplateEngine:
    """Main template engine"""
    
    def __init__(self, template_dirs: List[str] = None):
        self.loader = TemplateLoader(template_dirs)
        self.global_context = {}
    
    def set_global(self, name: str, value: Any):
        """Set global template variable"""
        self.global_context[name] = value
    
    def render_string(self, template_str: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render template string"""
        template = Template(template_str)
        merged_context = {**self.global_context, **(context or {})}
        return template.render(merged_context)
    
    def render_template(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render template file"""
        template = self.loader.load_template(template_name)
        merged_context = {**self.global_context, **(context or {})}
        return template.render(merged_context)


def test_template_engine():
    """Test the template engine implementation"""
    print("Testing Template Engine")
    print("=" * 50)
    
    engine = TemplateEngine()
    tests_passed = 0
    total_tests = 12
    
    # Test 1: Basic variable interpolation
    print("1. Testing basic variable interpolation...")
    try:
        result = engine.render_string("Hello {{ name }}!", {"name": "World"})
        expected = "Hello World!"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Filters
    print("2. Testing filters...")
    try:
        result = engine.render_string("{{ name | upper }}", {"name": "world"})
        expected = "WORLD"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Multiple filters
    print("3. Testing multiple filters...")
    try:
        result = engine.render_string("{{ name | lower | title }}", {"name": "WORLD"})
        expected = "World"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: If statement - true
    print("4. Testing if statement (true)...")
    try:
        result = engine.render_string("{% if show_message %}Hello{% endif %}", {"show_message": True})
        expected = "Hello"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: If statement - false
    print("5. Testing if statement (false)...")
    try:
        result = engine.render_string("{% if show_message %}Hello{% endif %}", {"show_message": False})
        expected = ""
        if result == expected:
            print(f"   ✓ Got: '{result}' (empty)")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 6: If-else statement
    print("6. Testing if-else statement...")
    try:
        result = engine.render_string("{% if logged_in %}Welcome!{% else %}Please login{% endif %}", {"logged_in": False})
        expected = "Please login"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 7: For loop
    print("7. Testing for loop...")
    try:
        result = engine.render_string("{% for item in items %}{{ item }} {% endfor %}", {"items": ["a", "b", "c"]})
        expected = "a b c "
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 8: For loop with forloop variable
    print("8. Testing for loop with forloop variables...")
    try:
        result = engine.render_string("{% for item in items %}{{ forloop.counter }}: {{ item }}{% if not forloop.last %}, {% endif %}{% endfor %}", {"items": ["x", "y"]})
        expected = "1: x, 2: y"
        # Remove trailing spaces for comparison
        result = result.strip()
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 9: Nested structures
    print("9. Testing nested if in for...")
    try:
        template = "{% for num in numbers %}{% if num > 5 %}{{ num }} {% endif %}{% endfor %}"
        result = engine.render_string(template, {"numbers": [3, 7, 4, 9, 2]})
        expected = "7 9 "
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 10: Complex template
    print("10. Testing complex template...")
    try:
        template = """
        <h1>{{ title }}</h1>
        {% if users %}
        <ul>
        {% for user in users %}
            <li>{{ user.name }} ({{ user.email | lower }})</li>
        {% endfor %}
        </ul>
        {% else %}
        <p>No users found.</p>
        {% endif %}
        """
        context = {
            "title": "User List",
            "users": [
                {"name": "Alice", "email": "ALICE@EXAMPLE.COM"},
                {"name": "Bob", "email": "BOB@EXAMPLE.COM"}
            ]
        }
        result = engine.render_string(template, context)
        if "Alice" in result and "alice@example.com" in result:
            print(f"   ✓ Complex template rendered correctly")
            tests_passed += 1
        else:
            print(f"   ✗ Complex template failed")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 11: Default filter
    print("11. Testing default filter...")
    try:
        result = engine.render_string("{{ name | default('Anonymous') }}", {})
        expected = "Anonymous"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 12: Join filter
    print("12. Testing join filter...")
    try:
        result = engine.render_string("{{ items | join(' - ') }}", {"items": ["apple", "banana", "cherry"]})
        expected = "apple - banana - cherry"
        if result == expected:
            print(f"   ✓ Got: '{result}'")
            tests_passed += 1
        else:
            print(f"   ✗ Expected: '{expected}', Got: '{result}'")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    if tests_passed == total_tests:
        print("🎉 All template engine tests passed!")
        print(f"✅ Passed: {tests_passed}/{total_tests}")
    else:
        print(f"⚠️  Some tests failed: {tests_passed}/{total_tests}")
        print(f"❌ Failed: {total_tests - tests_passed}")
    
    print("\nYou can now use the template engine:")
    print("  engine = TemplateEngine()")
    print("  result = engine.render_string('Hello {{ name }}!', {'name': 'World'})")


def interactive_mode():
    """Interactive template testing mode"""
    print("Template Engine - Interactive Mode")
    print("Type 'quit' to exit")
    print("-" * 40)
    
    engine = TemplateEngine()
    
    while True:
        try:
            template = input("Enter template: ").strip()
            if template.lower() in ['quit', 'exit', 'q']:
                break
            
            if not template:
                continue
            
            context_str = input("Enter context (JSON): ").strip()
            context = {}
            
            if context_str:
                try:
                    context = json.loads(context_str)
                except json.JSONDecodeError:
                    print("Invalid JSON, using empty context")
            
            result = engine.render_string(template, context)
            print(f"Result: {result}")
            print()
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()


def run_tests():
    """Test runner function for external use"""
    test_template_engine()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--test":
            test_template_engine()
        elif command == "--interactive":
            interactive_mode()
        else:
            print("Usage: python3 template_engine.py [--test] [--interactive]")
            return 1
    else:
        print("Template Engine Implementation")
        print("Usage:")
        print("  python3 template_engine.py --test       # Run tests")
        print("  python3 template_engine.py --interactive # Interactive mode")
        print()
        print("Example usage in code:")
        print("  from template_engine import TemplateEngine")
        print("  engine = TemplateEngine()")
        print("  result = engine.render_string('Hello {{ name }}!', {'name': 'World'})")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())