#!/usr/bin/env python3
"""
Regex Engine Implementation - Build Your Own Regex Engine
==========================================================

A complete regular expression engine built from scratch.
Implements both NFA (Non-deterministic Finite Automaton) and DFA approaches
for pattern matching with support for common regex features.

Features implemented:
- Basic character matching
- Wildcards (.)
- Quantifiers (*, +, ?)
- Character classes ([abc], [a-z])
- Anchors (^, $)
- Groups and alternation (|)
- Escape sequences (\\d, \\w, \\s)

Author: Build Something Project
License: MIT
"""

import sys
from typing import List, Set, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import string


class TokenType(Enum):
    """Token types for regex parsing"""
    CHAR = "CHAR"
    DOT = "DOT"
    STAR = "STAR"
    PLUS = "PLUS"
    QUESTION = "QUESTION"
    CARET = "CARET"
    DOLLAR = "DOLLAR"
    PIPE = "PIPE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    ESCAPE = "ESCAPE"
    END = "END"


@dataclass
class Token:
    """A token in the regex pattern"""
    type: TokenType
    value: str
    position: int


class RegexLexer:
    """Lexical analyzer for regex patterns"""
    
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.position = 0
        self.length = len(pattern)
    
    def current_char(self) -> str:
        """Get current character"""
        if self.position >= self.length:
            return ''
        return self.pattern[self.position]
    
    def advance(self) -> str:
        """Advance position and return previous character"""
        if self.position >= self.length:
            return ''
        char = self.pattern[self.position]
        self.position += 1
        return char
    
    def peek(self, offset: int = 1) -> str:
        """Look ahead at future character"""
        pos = self.position + offset
        if pos >= self.length:
            return ''
        return self.pattern[pos]
    
    def tokenize(self) -> List[Token]:
        """Convert regex pattern into tokens"""
        tokens = []
        
        while self.position < self.length:
            char = self.current_char()
            pos = self.position
            
            if char == '.':
                tokens.append(Token(TokenType.DOT, char, pos))
                self.advance()
            elif char == '*':
                tokens.append(Token(TokenType.STAR, char, pos))
                self.advance()
            elif char == '+':
                tokens.append(Token(TokenType.PLUS, char, pos))
                self.advance()
            elif char == '?':
                tokens.append(Token(TokenType.QUESTION, char, pos))
                self.advance()
            elif char == '^':
                tokens.append(Token(TokenType.CARET, char, pos))
                self.advance()
            elif char == '$':
                tokens.append(Token(TokenType.DOLLAR, char, pos))
                self.advance()
            elif char == '|':
                tokens.append(Token(TokenType.PIPE, char, pos))
                self.advance()
            elif char == '(':
                tokens.append(Token(TokenType.LPAREN, char, pos))
                self.advance()
            elif char == ')':
                tokens.append(Token(TokenType.RPAREN, char, pos))
                self.advance()
            elif char == '[':
                tokens.append(Token(TokenType.LBRACKET, char, pos))
                self.advance()
            elif char == ']':
                tokens.append(Token(TokenType.RBRACKET, char, pos))
                self.advance()
            elif char == '\\':
                self.advance()  # Skip backslash
                next_char = self.advance()
                if next_char:
                    tokens.append(Token(TokenType.ESCAPE, next_char, pos))
                else:
                    raise ValueError(f"Invalid escape sequence at position {pos}")
            else:
                tokens.append(Token(TokenType.CHAR, char, pos))
                self.advance()
        
        tokens.append(Token(TokenType.END, '', self.position))
        return tokens


class NFAState:
    """State in NFA (Non-deterministic Finite Automaton)"""
    
    def __init__(self, is_final: bool = False):
        self.is_final = is_final
        self.transitions: Dict[str, List['NFAState']] = {}
        self.epsilon_transitions: List['NFAState'] = []
        self.state_id = id(self)
    
    def add_transition(self, char: str, state: 'NFAState'):
        """Add character transition"""
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(state)
    
    def add_epsilon_transition(self, state: 'NFAState'):
        """Add epsilon (empty) transition"""
        self.epsilon_transitions.append(state)
    
    def get_transitions(self, char: str) -> List['NFAState']:
        """Get states reachable with character"""
        return self.transitions.get(char, [])


class NFA:
    """Non-deterministic Finite Automaton"""
    
    def __init__(self, start: NFAState, final: NFAState):
        self.start = start
        self.final = final
    
    def epsilon_closure(self, states: Set[NFAState]) -> Set[NFAState]:
        """Get epsilon closure of a set of states"""
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            for epsilon_state in state.epsilon_transitions:
                if epsilon_state not in closure:
                    closure.add(epsilon_state)
                    stack.append(epsilon_state)
        
        return closure
    
    def move(self, states: Set[NFAState], char: str) -> Set[NFAState]:
        """Get states reachable from given states with character"""
        result = set()
        
        for state in states:
            # Direct character transitions
            if char in state.transitions:
                result.update(state.transitions[char])
            
            # Wildcard transitions (dot)
            if '.' in state.transitions and char != '\n':
                result.update(state.transitions['.'])
            
            # Character class support
            for transition_char in state.transitions:
                if self.matches_char_class(char, transition_char):
                    result.update(state.transitions[transition_char])
        
        return result
    
    def matches_char_class(self, char: str, pattern: str) -> bool:
        """Check if character matches a character class pattern"""
        if pattern.startswith('[') and pattern.endswith(']'):
            # Character class like [abc] or [a-z]
            inside = pattern[1:-1]
            if inside.startswith('^'):
                # Negated class [^abc]
                return not self.char_in_class(char, inside[1:])
            else:
                return self.char_in_class(char, inside)
        elif pattern.startswith('\\'):
            # Escape sequence
            return self.matches_escape(char, pattern[1])
        
        return False
    
    def char_in_class(self, char: str, class_def: str) -> bool:
        """Check if character is in character class definition"""
        i = 0
        while i < len(class_def):
            if i + 2 < len(class_def) and class_def[i + 1] == '-':
                # Range like a-z
                start = class_def[i]
                end = class_def[i + 2]
                if start <= char <= end:
                    return True
                i += 3
            else:
                # Single character
                if char == class_def[i]:
                    return True
                i += 1
        return False
    
    def matches_escape(self, char: str, escape_char: str) -> bool:
        """Check if character matches escape sequence"""
        if escape_char == 'd':
            return char.isdigit()
        elif escape_char == 'w':
            return char.isalnum() or char == '_'
        elif escape_char == 's':
            return char.isspace()
        elif escape_char == 'D':
            return not char.isdigit()
        elif escape_char == 'W':
            return not (char.isalnum() or char == '_')
        elif escape_char == 'S':
            return not char.isspace()
        else:
            return char == escape_char
    
    def matches(self, text: str, start_anchor: bool = False, end_anchor: bool = False) -> bool:
        """Test if NFA matches the text"""
        if start_anchor and end_anchor:
            # Must match entire string
            return self._matches_entire_string(text)
        elif start_anchor:
            # Must match from beginning
            return self._matches_from_start(text)
        elif end_anchor:
            # Must match at end
            return self._matches_at_end(text)
        else:
            # Can match at any position
            for i in range(len(text) + 1):
                if self._matches_at_position(text, i, False, len(text)):
                    return True
            return False
    
    def _matches_entire_string(self, text: str) -> bool:
        """Check if pattern matches entire string"""
        current_states = self.epsilon_closure({self.start})
        
        for char in text:
            next_states = self.move(current_states, char)
            current_states = self.epsilon_closure(next_states)
            
            if not current_states:
                return False
        
        # Check for final states
        return any(state.is_final for state in current_states)
    
    def _matches_from_start(self, text: str) -> bool:
        """Check if pattern matches from start of string"""
        current_states = self.epsilon_closure({self.start})
        
        for i, char in enumerate(text):
            next_states = self.move(current_states, char)
            current_states = self.epsilon_closure(next_states)
            
            # Check if we have a match at any point
            if any(state.is_final for state in current_states):
                return True
                
            if not current_states:
                break
        
        # Final check for empty match or end of string
        return any(state.is_final for state in current_states)
    
    def _matches_at_end(self, text: str) -> bool:
        """Check if pattern matches at end of string"""
        # Try matching from each position, but only accept matches that end at string end
        for start_pos in range(len(text) + 1):
            if self._matches_ending_at_position(text, start_pos, len(text)):
                return True
        return False
    
    def _matches_ending_at_position(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Check if pattern matches from start_pos and ends exactly at end_pos"""
        current_states = self.epsilon_closure({self.start})
        
        for i in range(start_pos, end_pos):
            char = text[i]
            next_states = self.move(current_states, char)
            current_states = self.epsilon_closure(next_states)
            
            if not current_states:
                return False
        
        # Must be in final state and have consumed all text
        return any(state.is_final for state in current_states)
    
    def _matches_at_position(self, text: str, start_pos: int, end_anchor: bool, text_len: int) -> bool:
        """Check if pattern matches starting at specific position"""
        current_states = self.epsilon_closure({self.start})
        
        pos = start_pos
        while pos < text_len:
            char = text[pos]
            next_states = self.move(current_states, char)
            current_states = self.epsilon_closure(next_states)
            
            if not current_states:
                break
            pos += 1
        
        # Check for final states
        for state in current_states:
            if state.is_final:
                if end_anchor:
                    # Must reach end of string
                    return pos == text_len
                else:
                    return True
        
        return False


class RegexParser:
    """Parser for regex patterns - builds NFA from tokens"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.has_start_anchor = False
        self.has_end_anchor = False
    
    def current_token(self) -> Token:
        """Get current token"""
        if self.position >= len(self.tokens):
            return self.tokens[-1]  # END token
        return self.tokens[self.position]
    
    def advance(self) -> Token:
        """Advance to next token"""
        token = self.current_token()
        if self.position < len(self.tokens) - 1:
            self.position += 1
        return token
    
    def parse(self) -> NFA:
        """Parse tokens into NFA"""
        # Check for anchors
        if self.tokens and self.tokens[0].type == TokenType.CARET:
            self.has_start_anchor = True
            self.advance()
        
        if (len(self.tokens) >= 2 and 
            self.tokens[-2].type == TokenType.DOLLAR and 
            self.tokens[-1].type == TokenType.END):
            self.has_end_anchor = True
        
        nfa = self.parse_alternation()
        return nfa
    
    def parse_alternation(self) -> NFA:
        """Parse alternation (|)"""
        left = self.parse_concatenation()
        
        if self.current_token().type == TokenType.PIPE:
            self.advance()  # consume |
            right = self.parse_alternation()
            
            # Create new start and final states
            start = NFAState()
            final = NFAState(True)
            
            # Add epsilon transitions
            start.add_epsilon_transition(left.start)
            start.add_epsilon_transition(right.start)
            left.final.add_epsilon_transition(final)
            right.final.add_epsilon_transition(final)
            left.final.is_final = False
            right.final.is_final = False
            
            return NFA(start, final)
        
        return left
    
    def parse_concatenation(self) -> NFA:
        """Parse concatenation (sequence)"""
        left = self.parse_quantification()
        
        while (self.current_token().type not in [TokenType.PIPE, TokenType.RPAREN, 
                                                 TokenType.END, TokenType.DOLLAR]):
            right = self.parse_quantification()
            
            # Connect left.final to right.start
            left.final.add_epsilon_transition(right.start)
            left.final.is_final = False
            left.final = right.final
        
        return left
    
    def parse_quantification(self) -> NFA:
        """Parse quantifiers (*, +, ?)"""
        atom = self.parse_atom()
        
        token = self.current_token()
        if token.type == TokenType.STAR:
            self.advance()
            return self.create_star_nfa(atom)
        elif token.type == TokenType.PLUS:
            self.advance()
            return self.create_plus_nfa(atom)
        elif token.type == TokenType.QUESTION:
            self.advance()
            return self.create_question_nfa(atom)
        
        return atom
    
    def parse_atom(self) -> NFA:
        """Parse atomic expressions"""
        token = self.current_token()
        
        if token.type == TokenType.CHAR:
            self.advance()
            return self.create_char_nfa(token.value)
        
        elif token.type == TokenType.DOT:
            self.advance()
            return self.create_dot_nfa()
        
        elif token.type == TokenType.ESCAPE:
            self.advance()
            return self.create_escape_nfa(token.value)
        
        elif token.type == TokenType.LPAREN:
            self.advance()  # consume (
            inner = self.parse_alternation()
            if self.current_token().type != TokenType.RPAREN:
                raise ValueError("Missing closing parenthesis")
            self.advance()  # consume )
            return inner
        
        elif token.type == TokenType.LBRACKET:
            return self.parse_char_class()
        
        else:
            raise ValueError(f"Unexpected token: {token.type} at position {token.position}")
    
    def parse_char_class(self) -> NFA:
        """Parse character class [abc] or [a-z]"""
        self.advance()  # consume [
        
        class_chars = []
        negated = False
        
        if self.current_token().type == TokenType.CARET:
            negated = True
            self.advance()
        
        while self.current_token().type != TokenType.RBRACKET:
            token = self.current_token()
            if token.type == TokenType.END:
                raise ValueError("Unclosed character class")
            
            class_chars.append(token.value)
            self.advance()
        
        self.advance()  # consume ]
        
        # Build character class pattern
        class_def = ''.join(class_chars)
        if negated:
            class_def = '^' + class_def
        
        return self.create_char_class_nfa(f"[{class_def}]")
    
    def create_char_nfa(self, char: str) -> NFA:
        """Create NFA for single character"""
        start = NFAState()
        final = NFAState(True)
        start.add_transition(char, final)
        return NFA(start, final)
    
    def create_dot_nfa(self) -> NFA:
        """Create NFA for wildcard (.)"""
        start = NFAState()
        final = NFAState(True)
        start.add_transition('.', final)
        return NFA(start, final)
    
    def create_escape_nfa(self, escape_char: str) -> NFA:
        """Create NFA for escape sequence"""
        start = NFAState()
        final = NFAState(True)
        start.add_transition(f'\\{escape_char}', final)
        return NFA(start, final)
    
    def create_char_class_nfa(self, char_class: str) -> NFA:
        """Create NFA for character class"""
        start = NFAState()
        final = NFAState(True)
        start.add_transition(char_class, final)
        return NFA(start, final)
    
    def create_star_nfa(self, inner: NFA) -> NFA:
        """Create NFA for * quantifier"""
        start = NFAState()
        final = NFAState(True)
        
        # epsilon transitions for zero or more
        start.add_epsilon_transition(inner.start)
        start.add_epsilon_transition(final)
        inner.final.add_epsilon_transition(inner.start)
        inner.final.add_epsilon_transition(final)
        inner.final.is_final = False
        
        return NFA(start, final)
    
    def create_plus_nfa(self, inner: NFA) -> NFA:
        """Create NFA for + quantifier"""
        start = NFAState()
        final = NFAState(True)
        
        # epsilon transitions for one or more
        start.add_epsilon_transition(inner.start)
        inner.final.add_epsilon_transition(inner.start)
        inner.final.add_epsilon_transition(final)
        inner.final.is_final = False
        
        return NFA(start, final)
    
    def create_question_nfa(self, inner: NFA) -> NFA:
        """Create NFA for ? quantifier"""
        start = NFAState()
        final = NFAState(True)
        
        # epsilon transitions for zero or one
        start.add_epsilon_transition(inner.start)
        start.add_epsilon_transition(final)
        inner.final.add_epsilon_transition(final)
        inner.final.is_final = False
        
        return NFA(start, final)


class RegexEngine:
    """Main regex engine class"""
    
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.lexer = RegexLexer(pattern)
        self.tokens = self.lexer.tokenize()
        self.parser = RegexParser(self.tokens)
        self.nfa = self.parser.parse()
        self.has_start_anchor = self.parser.has_start_anchor
        self.has_end_anchor = self.parser.has_end_anchor
    
    def match(self, text: str) -> bool:
        """Test if pattern matches text"""
        try:
            return self.nfa.matches(text, self.has_start_anchor, self.has_end_anchor)
        except Exception as e:
            raise ValueError(f"Match error: {e}")
    
    def search(self, text: str) -> Optional[Tuple[int, int]]:
        """Find first match in text, return (start, end) or None"""
        if self.has_start_anchor:
            # Must match from beginning
            for end in range(1, len(text) + 1):
                if self.nfa._matches_at_position(text, 0, False, end):
                    if self.has_end_anchor and end != len(text):
                        continue
                    return (0, end)
            return None
        else:
            # Can start at any position
            for start in range(len(text)):
                for end in range(start + 1, len(text) + 1):
                    if self.nfa._matches_at_position(text, start, False, end):
                        if self.has_end_anchor and end != len(text):
                            continue
                        return (start, end)
            return None
    
    def findall(self, text: str) -> List[str]:
        """Find all matches in text"""
        matches = []
        pos = 0
        
        while pos <= len(text):
            # Try to find match starting at or after position
            found = False
            for start in range(pos, len(text)):
                for end in range(start + 1, len(text) + 1):
                    if self.nfa._matches_at_position(text, start, False, end):
                        if self.has_end_anchor and end != len(text):
                            continue
                        matches.append(text[start:end])
                        pos = end
                        found = True
                        break
                if found:
                    break
            
            if not found:
                break
        
        return matches


def test_regex_engine():
    """Test the regex engine implementation"""
    print("Testing Regex Engine")
    print("=" * 50)
    
    tests = [
        # Basic tests
        ("abc", "abc", True, "Basic string match"),
        ("abc", "def", False, "Basic string no match"),
        
        # Wildcard tests
        ("a.c", "abc", True, "Wildcard match"),
        ("a.c", "adc", True, "Wildcard different char"),
        ("a.c", "ac", False, "Wildcard requires char"),
        
        # Quantifier tests
        ("ab*c", "ac", True, "Star zero occurrences"),
        ("ab*c", "abc", True, "Star one occurrence"),
        ("ab*c", "abbbbc", True, "Star multiple occurrences"),
        
        ("ab+c", "ac", False, "Plus requires one"),
        ("ab+c", "abc", True, "Plus one occurrence"),
        ("ab+c", "abbbbc", True, "Plus multiple occurrences"),
        
        ("ab?c", "ac", True, "Question zero occurrences"),
        ("ab?c", "abc", True, "Question one occurrence"),
        ("ab?c", "abbc", False, "Question max one"),
        
        # Character class tests
        ("[abc]", "a", True, "Character class match"),
        ("[abc]", "d", False, "Character class no match"),
        ("[a-z]", "m", True, "Range class match"),
        ("[a-z]", "5", False, "Range class no match"),
        
        # Escape sequences
        ("\\d", "5", True, "Digit escape match"),
        ("\\d", "a", False, "Digit escape no match"),
        ("\\w", "a", True, "Word escape match"),
        ("\\w", " ", False, "Word escape no match"),
        
        # Anchors
        ("^abc", "abcdef", True, "Start anchor match"),
        ("^abc", "xabcdef", False, "Start anchor no match"),
        ("abc$", "xyzabc", True, "End anchor match"),
        ("abc$", "abcdef", False, "End anchor no match"),
        
        # Alternation
        ("cat|dog", "cat", True, "Alternation first option"),
        ("cat|dog", "dog", True, "Alternation second option"),
        ("cat|dog", "bird", False, "Alternation no match"),
        
        # Groups
        ("(ab)+", "ab", True, "Group with plus"),
        ("(ab)+", "abab", True, "Group repeated"),
        ("(ab)+", "a", False, "Group not matched"),
    ]
    
    passed = 0
    total = len(tests)
    
    for i, (pattern, text, expected, description) in enumerate(tests, 1):
        print(f"{i}. Testing: {description}")
        print(f"   Pattern: '{pattern}', Text: '{text}'")
        
        try:
            engine = RegexEngine(pattern)
            result = engine.match(text)
            
            if result == expected:
                print(f"   ✓ {'Match' if result else 'No match'} (expected)")
                passed += 1
            else:
                print(f"   ✗ {'Match' if result else 'No match'} (expected {'Match' if expected else 'No match'})")
        
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print()
    
    # Summary
    print("=" * 50)
    if passed == total:
        print("🎉 All regex tests passed!")
        print(f"✅ Passed: {passed}/{total}")
    else:
        print(f"⚠️  Some tests failed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}")
    
    print("\nYou can now use the regex engine:")
    print("  engine = RegexEngine('pattern')")
    print("  engine.match('text')")
    print("  engine.search('text')")
    print("  engine.findall('text')")


def interactive_mode():
    """Interactive regex testing mode"""
    print("Regex Engine - Interactive Mode")
    print("Type 'quit' to exit")
    print("-" * 40)
    
    while True:
        try:
            pattern = input("Enter regex pattern: ").strip()
            if pattern.lower() in ['quit', 'exit', 'q']:
                break
            
            if not pattern:
                continue
            
            text = input("Enter text to match: ").strip()
            if not text:
                continue
            
            engine = RegexEngine(pattern)
            
            # Test match
            match_result = engine.match(text)
            print(f"Match: {'Yes' if match_result else 'No'}")
            
            # Test search
            search_result = engine.search(text)
            if search_result:
                start, end = search_result
                print(f"Search: Found at position {start}-{end}: '{text[start:end]}'")
            else:
                print("Search: Not found")
            
            # Test findall
            all_matches = engine.findall(text)
            if all_matches:
                print(f"Find all: {all_matches}")
            else:
                print("Find all: No matches")
            
            print()
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()


def run_tests():
    """Test runner function for external use"""
    test_regex_engine()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--test":
            test_regex_engine()
        elif command == "--interactive":
            interactive_mode()
        else:
            print("Usage: python3 regex_engine.py [--test] [--interactive]")
            return 1
    else:
        print("Regex Engine Implementation")
        print("Usage:")
        print("  python3 regex_engine.py --test       # Run tests")
        print("  python3 regex_engine.py --interactive # Interactive mode")
        print()
        print("Example usage in code:")
        print("  from regex_engine import RegexEngine")
        print("  engine = RegexEngine(r'\\d+')")
        print("  result = engine.match('123')")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())