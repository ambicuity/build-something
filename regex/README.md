# Build Your Own Regex Engine

Create regular expression engines from scratch and understand pattern matching, finite automata, and text processing algorithms.

## 🎯 What You'll Learn

- Finite automata and state machines
- NFA to DFA conversion algorithms  
- Backtracking vs linear time matching
- Lexical analysis and parsing
- Pattern matching algorithms
- Unicode and character class support

## 🚀 Quick Start

```bash
# Navigate to the starter directory
cd regex/starter

# Run tests to verify everything works
python3 regex_engine.py --test

# Use interactive mode to test patterns
python3 regex_engine.py --interactive

# Use in code
python3 -c "
from regex_engine import RegexEngine
engine = RegexEngine(r'\\d+')
print(engine.match('123'))  # True
"
```

## 🛠️ Implementation Features

Our regex engine implements a complete pattern matching system with:

### Core Features
- **NFA Construction**: Non-deterministic Finite Automaton approach
- **Epsilon Transitions**: Efficient state transitions
- **Character Classes**: Support for `[abc]`, `[a-z]`, `[^abc]`
- **Quantifiers**: `*` (zero or more), `+` (one or more), `?` (zero or one)
- **Anchors**: `^` (start), `$` (end) 
- **Alternation**: `|` operator for pattern choices
- **Groups**: `()` for grouping expressions
- **Wildcards**: `.` matches any character

### Escape Sequences
- `\\d` - Digits (0-9)
- `\\w` - Word characters (a-z, A-Z, 0-9, _)
- `\\s` - Whitespace characters
- `\\D` - Non-digits
- `\\W` - Non-word characters  
- `\\S` - Non-whitespace characters

### Pattern Examples

```bash
# Basic patterns
python3 regex_engine.py --interactive
# Enter: abc
# Text: abc def abc  
# Result: Match: Yes, Search: Found abc

# Quantifiers
# Pattern: ab*c
# Text: ac abc abbbbc
# Matches: ac, abc, abbbbc

# Character classes
# Pattern: [a-z]+
# Text: Hello123World
# Matches: ello, orld

# Anchors
# Pattern: ^[A-Z].*
# Text: Hello world
# Matches: Hello world (starts with capital)

# Complex patterns
# Pattern: \\d{2,4}  (simulated with \\d\\d+?)
# Text: 12 345 6789
# Matches: 12, 345, 6789
```

## 🏗️ Architecture

### 1. **Lexer** (`RegexLexer`)
Tokenizes regex patterns into components:
```python
lexer = RegexLexer("ab*c")
tokens = lexer.tokenize()
# [CHAR(a), CHAR(b), STAR(*), CHAR(c), END]
```

### 2. **Parser** (`RegexParser`) 
Builds NFA from tokens using recursive descent:
```python
parser = RegexParser(tokens)
nfa = parser.parse()
```

### 3. **NFA Engine** (`NFA`)
Executes pattern matching:
```python
# State transitions
current_states = nfa.epsilon_closure({start_state})
next_states = nfa.move(current_states, 'a')
```

### 4. **Regex Engine** (`RegexEngine`)
High-level interface:
```python
engine = RegexEngine("pattern")
engine.match("text")     # Full match
engine.search("text")    # Find first match  
engine.findall("text")   # Find all matches
```

## 📊 Test Coverage

The implementation includes 32 comprehensive tests covering:
- ✅ Basic string matching
- ✅ Wildcard patterns (.)
- ✅ All quantifiers (*, +, ?)
- ✅ Character classes ([abc], [a-z])
- ✅ Escape sequences (\\d, \\w, \\s)
- ✅ Anchors (^, $)
- ✅ Alternation (|)
- ✅ Groups and repetition

All tests pass: **32/32** ✅

## 📚 Tutorials by Language

### C
- **[A Regular Expression Matcher](https://www.cs.princeton.edu/courses/archive/spr09/cos333/beautiful.html)** - Elegant regex implementation
- **[Regular Expression Matching Can Be Simple And Fast](https://swtch.com/~rsc/regexp/regexp1.html)** - Efficient regex algorithms

### Go
- **[How to build a regex engine from scratch](https://kean.blog/post/regex-parser)** - Go regex implementation

### JavaScript  
- **[Build a Regex Engine in Less than 40 Lines of Code](https://nickdrane.com/build-your-own-regex/)** - Minimal regex engine
- **[How to implement regular expressions in functional javascript using derivatives](https://matt.might.net/articles/implementation-of-regular-expression-matching-in-scheme-with-derivatives/)** - Advanced techniques
- **[Implementing a Regular Expression Engine](https://deniskyashif.com/implementing-a-regular-expression-engine/)** - Comprehensive guide

### Perl
- **[How Regexes Work](https://perl.plover.com/Regex/article.html)** - Perl regex internals

### Python
- **[Build Your Own Regular Expression Engines](https://build-your-own.org/regex/)** - Multiple implementation approaches

### Scala  
- **[No Magic: Regular Expressions](https://rcoh.me/posts/no-magic-regular-expressions/)** - Demystifying regex

## 🎯 Key Concepts
- Finite automata and state machines
- NFA to DFA conversion algorithms
- Backtracking vs linear time matching
- Unicode and character class support

---

Start with simple pattern matching and evolve into full regex engines!