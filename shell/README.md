# Build Your Own Shell

Create a command-line shell from scratch and understand how shells work under the hood. You'll implement command parsing, process execution, pipes, redirections, and built-in commands.

## 🎯 What You'll Learn

- How shells parse and execute commands
- Process creation and management with fork/exec
- Inter-process communication with pipes
- File redirection (stdin, stdout, stderr)
- Built-in shell commands vs external programs
- Environment variables and PATH resolution

## 📋 Prerequisites

- Understanding of processes and the operating system
- Basic knowledge of file descriptors and I/O
- Familiarity with command-line interfaces
- Knowledge of system calls (fork, exec, wait)

## 🏗️ Architecture Overview

Our shell consists of these components:

1. **REPL Loop**: Read-Eval-Print Loop for user interaction
2. **Lexer**: Breaks command line into tokens
3. **Parser**: Builds command structure from tokens
4. **Executor**: Runs commands and manages processes
5. **Built-ins**: Implementation of shell built-in commands
6. **Pipeline Handler**: Manages pipes between commands

```
User Input → Lexer → Parser → Executor → Process Management
     ↑                                         ↓
   Display ← Output Capture ← Command Result ← Fork/Exec
```

## 🚀 Implementation Steps

### Step 1: Basic REPL and Command Execution

Let's start with a simple Read-Eval-Print Loop that can execute basic commands.

**Theory**: Shells continuously read user input, parse it into commands, execute those commands, and display results. This is the fundamental REPL cycle.

```python
import os
import sys
import subprocess
import shlex
from pathlib import Path

class MyShell:
    def __init__(self):
        self.running = True
        self.exit_code = 0
        
    def start(self):
        """Start the shell REPL"""
        print("MyShell v1.0 - A simple shell implementation")
        print("Type 'help' for available commands or 'exit' to quit")
        
        while self.running:
            try:
                # Display prompt
                cwd = os.getcwd()
                prompt = f"myshell:{os.path.basename(cwd)}$ "
                
                # Read user input
                command = input(prompt).strip()
                
                if not command:
                    continue
                    
                # Execute command
                self.execute_command(command)
                
            except KeyboardInterrupt:
                print("\n^C")
                continue
            except EOFError:
                print("\nBye!")
                break
        
        return self.exit_code
    
    def execute_command(self, command_line):
        """Execute a single command"""
        try:
            # Simple command parsing (we'll improve this later)
            args = shlex.split(command_line)
            
            if not args:
                return
            
            command = args[0]
            
            # Handle built-in commands
            if command == 'exit':
                self.running = False
                return
            elif command == 'help':
                self.builtin_help()
                return
            elif command == 'cd':
                self.builtin_cd(args[1:])
                return
            elif command == 'pwd':
                print(os.getcwd())
                return
            
            # Execute external command
            self.execute_external(args)
            
        except Exception as e:
            print(f"myshell: error: {e}")
    
    def execute_external(self, args):
        """Execute external command"""
        try:
            result = subprocess.run(args, capture_output=False, text=True)
            self.exit_code = result.returncode
        except FileNotFoundError:
            print(f"myshell: command not found: {args[0]}")
            self.exit_code = 127
        except Exception as e:
            print(f"myshell: execution error: {e}")
            self.exit_code = 1
    
    def builtin_help(self):
        """Display help information"""
        print("""
MyShell Built-in Commands:
  help          Show this help message
  exit          Exit the shell
  cd [dir]      Change directory
  pwd           Print working directory
        """)
    
    def builtin_cd(self, args):
        """Change directory built-in"""
        if not args:
            # cd with no arguments goes to home directory
            target = os.path.expanduser("~")
        else:
            target = args[0]
        
        try:
            os.chdir(target)
        except OSError as e:
            print(f"cd: {e}")

if __name__ == "__main__":
    shell = MyShell()
    sys.exit(shell.start())
```

**Test it**: Run the shell and try basic commands like `ls`, `pwd`, `cd`, `echo hello`.

### Step 2: Advanced Command Parsing

Implement proper tokenization and parsing to handle quotes, escapes, and complex commands.

**Theory**: Shells need to properly parse command lines, handling quotes (single and double), escape characters, and separating commands from arguments.

```python
import re
from enum import Enum
from typing import List, Dict, Any

class TokenType(Enum):
    WORD = "WORD"
    PIPE = "PIPE"
    REDIRECT_IN = "REDIRECT_IN"
    REDIRECT_OUT = "REDIRECT_OUT"
    REDIRECT_APPEND = "REDIRECT_APPEND"
    SEMICOLON = "SEMICOLON"
    AND = "AND"
    OR = "OR"
    BACKGROUND = "BACKGROUND"

class Token:
    def __init__(self, type: TokenType, value: str, position: int = 0):
        self.type = type
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"

class Lexer:
    """Tokenizes command line input"""
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens = []
    
    def tokenize(self) -> List[Token]:
        """Convert command line into tokens"""
        self.pos = 0
        self.tokens = []
        
        while self.pos < len(self.text):
            self._skip_whitespace()
            
            if self.pos >= len(self.text):
                break
            
            char = self.text[self.pos]
            
            # Handle operators
            if char == '|':
                self.tokens.append(Token(TokenType.PIPE, char, self.pos))
                self.pos += 1
            elif char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, char, self.pos))
                self.pos += 1
            elif char == '&':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '&':
                    self.tokens.append(Token(TokenType.AND, '&&', self.pos))
                    self.pos += 2
                else:
                    self.tokens.append(Token(TokenType.BACKGROUND, '&', self.pos))
                    self.pos += 1
            elif char == '<':
                self.tokens.append(Token(TokenType.REDIRECT_IN, char, self.pos))
                self.pos += 1
            elif char == '>':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '>':
                    self.tokens.append(Token(TokenType.REDIRECT_APPEND, '>>', self.pos))
                    self.pos += 2
                else:
                    self.tokens.append(Token(TokenType.REDIRECT_OUT, char, self.pos))
                    self.pos += 1
            else:
                # Handle words (including quoted strings)
                word = self._read_word()
                if word:
                    self.tokens.append(Token(TokenType.WORD, word, self.pos))
        
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
    
    def _read_word(self) -> str:
        """Read a word, handling quotes and escapes"""
        start_pos = self.pos
        result = ""
        
        while self.pos < len(self.text):
            char = self.text[self.pos]
            
            # Break on operators and whitespace
            if char in '|;&<>' or char.isspace():
                break
            
            # Handle quotes
            if char == '"':
                self.pos += 1
                result += self._read_quoted_string('"')
            elif char == "'":
                self.pos += 1
                result += self._read_quoted_string("'")
            elif char == '\\':
                # Handle escape sequences
                self.pos += 1
                if self.pos < len(self.text):
                    result += self.text[self.pos]
                    self.pos += 1
            else:
                result += char
                self.pos += 1
        
        return result
    
    def _read_quoted_string(self, quote_char: str) -> str:
        """Read a quoted string"""
        result = ""
        
        while self.pos < len(self.text):
            char = self.text[self.pos]
            
            if char == quote_char:
                self.pos += 1  # Skip closing quote
                break
            elif char == '\\' and quote_char == '"':
                # Handle escapes in double quotes
                self.pos += 1
                if self.pos < len(self.text):
                    next_char = self.text[self.pos]
                    if next_char in '\\$"`\n':
                        result += next_char
                    else:
                        result += '\\' + next_char
                    self.pos += 1
            else:
                result += char
                self.pos += 1
        
        return result

class Command:
    """Represents a parsed command"""
    
    def __init__(self):
        self.args = []
        self.input_redirect = None
        self.output_redirect = None
        self.append_redirect = None
        self.background = False

class Pipeline:
    """Represents a pipeline of commands"""
    
    def __init__(self):
        self.commands = []

class Parser:
    """Parses tokens into command structures"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> List[Pipeline]:
        """Parse tokens into pipelines"""
        pipelines = []
        
        while self.pos < len(self.tokens):
            pipeline = self._parse_pipeline()
            if pipeline and pipeline.commands:
                pipelines.append(pipeline)
            
            # Skip semicolons
            if self._current_token() and self._current_token().type == TokenType.SEMICOLON:
                self.pos += 1
        
        return pipelines
    
    def _parse_pipeline(self) -> Pipeline:
        """Parse a single pipeline"""
        pipeline = Pipeline()
        
        # Parse first command
        command = self._parse_command()
        if command:
            pipeline.commands.append(command)
        
        # Parse additional commands connected by pipes
        while self._current_token() and self._current_token().type == TokenType.PIPE:
            self.pos += 1  # Skip pipe
            command = self._parse_command()
            if command:
                pipeline.commands.append(command)
        
        return pipeline
    
    def _parse_command(self) -> Command:
        """Parse a single command"""
        command = Command()
        
        while self.pos < len(self.tokens):
            token = self._current_token()
            if not token:
                break
            
            if token.type == TokenType.WORD:
                command.args.append(token.value)
                self.pos += 1
            elif token.type == TokenType.REDIRECT_IN:
                self.pos += 1
                if self._current_token() and self._current_token().type == TokenType.WORD:
                    command.input_redirect = self._current_token().value
                    self.pos += 1
            elif token.type == TokenType.REDIRECT_OUT:
                self.pos += 1
                if self._current_token() and self._current_token().type == TokenType.WORD:
                    command.output_redirect = self._current_token().value
                    self.pos += 1
            elif token.type == TokenType.REDIRECT_APPEND:
                self.pos += 1
                if self._current_token() and self._current_token().type == TokenType.WORD:
                    command.append_redirect = self._current_token().value
                    self.pos += 1
            elif token.type == TokenType.BACKGROUND:
                command.background = True
                self.pos += 1
                break
            else:
                # Break on pipe, semicolon, etc.
                break
        
        return command
    
    def _current_token(self) -> Token:
        """Get current token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

# Update MyShell to use the new parser
class MyShell:
    def __init__(self):
        self.running = True
        self.exit_code = 0
        self.background_jobs = []
    
    def execute_command(self, command_line):
        """Execute command line with proper parsing"""
        try:
            # Tokenize and parse
            lexer = Lexer(command_line)
            tokens = lexer.tokenize()
            
            if not tokens:
                return
            
            parser = Parser(tokens)
            pipelines = parser.parse()
            
            for pipeline in pipelines:
                self.execute_pipeline(pipeline)
                
        except Exception as e:
            print(f"myshell: error: {e}")
    
    def execute_pipeline(self, pipeline: Pipeline):
        """Execute a pipeline of commands"""
        if not pipeline.commands:
            return
        
        # Handle single command
        if len(pipeline.commands) == 1:
            self.execute_single_command(pipeline.commands[0])
            return
        
        # Handle pipeline with multiple commands
        processes = []
        pipes = []
        
        for i, command in enumerate(pipeline.commands):
            # Create pipe for communication between commands
            if i < len(pipeline.commands) - 1:
                read_fd, write_fd = os.pipe()
                pipes.append((read_fd, write_fd))
        
        for i, command in enumerate(pipeline.commands):
            # Handle built-ins in pipeline (simplified)
            if command.args and self.is_builtin(command.args[0]):
                print("myshell: built-ins in pipelines not fully supported yet")
                continue
            
            try:
                # Setup pipes
                stdin = None
                stdout = None
                
                if i > 0:  # Not first command
                    stdin = pipes[i-1][0]
                if i < len(pipeline.commands) - 1:  # Not last command
                    stdout = pipes[i][1]
                
                # Handle redirections
                if command.input_redirect and i == 0:
                    stdin = open(command.input_redirect, 'r')
                if command.output_redirect and i == len(pipeline.commands) - 1:
                    stdout = open(command.output_redirect, 'w')
                if command.append_redirect and i == len(pipeline.commands) - 1:
                    stdout = open(command.append_redirect, 'a')
                
                # Start process
                process = subprocess.Popen(
                    command.args,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.PIPE
                )
                processes.append(process)
                
            except Exception as e:
                print(f"myshell: pipeline error: {e}")
        
        # Close pipes in parent process
        for read_fd, write_fd in pipes:
            os.close(read_fd)
            os.close(write_fd)
        
        # Wait for all processes to complete
        for process in processes:
            try:
                process.wait()
            except:
                pass
    
    def execute_single_command(self, command: Command):
        """Execute a single command with redirections"""
        if not command.args:
            return
        
        cmd = command.args[0]
        
        # Handle built-in commands
        if self.is_builtin(cmd):
            self.execute_builtin(command)
            return
        
        # Execute external command
        try:
            stdin = None
            stdout = None
            stderr = None
            
            # Handle input redirection
            if command.input_redirect:
                stdin = open(command.input_redirect, 'r')
            
            # Handle output redirection
            if command.output_redirect:
                stdout = open(command.output_redirect, 'w')
            elif command.append_redirect:
                stdout = open(command.append_redirect, 'a')
            
            # Start process
            process = subprocess.Popen(
                command.args,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr
            )
            
            if command.background:
                print(f"[{len(self.background_jobs) + 1}] {process.pid}")
                self.background_jobs.append(process)
            else:
                # Wait for foreground process
                try:
                    process.wait()
                    self.exit_code = process.returncode
                except KeyboardInterrupt:
                    process.terminate()
                    print("\n^C")
            
            # Close file handles
            if stdin:
                stdin.close()
            if stdout:
                stdout.close()
                
        except FileNotFoundError:
            print(f"myshell: command not found: {cmd}")
            self.exit_code = 127
        except Exception as e:
            print(f"myshell: error: {e}")
            self.exit_code = 1
    
    def is_builtin(self, command):
        """Check if command is a built-in"""
        return command in ['exit', 'help', 'cd', 'pwd', 'echo', 'env', 'export']
    
    def execute_builtin(self, command: Command):
        """Execute built-in command"""
        cmd = command.args[0]
        args = command.args[1:]
        
        if cmd == 'exit':
            self.running = False
        elif cmd == 'help':
            self.builtin_help()
        elif cmd == 'cd':
            self.builtin_cd(args)
        elif cmd == 'pwd':
            print(os.getcwd())
        elif cmd == 'echo':
            print(' '.join(args))
        elif cmd == 'env':
            for key, value in os.environ.items():
                print(f"{key}={value}")
        elif cmd == 'export':
            self.builtin_export(args)
    
    def builtin_export(self, args):
        """Export environment variable"""
        for arg in args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                os.environ[key] = value
            else:
                print(f"export: {arg}: not a valid identifier")
```

**Test it**: Try complex commands like:
- `echo "hello world" | grep hello`
- `ls -la > output.txt`
- `cat < input.txt | sort | uniq`

### Step 3: Environment Variables and PATH Resolution

Add support for environment variables and command resolution through PATH.

```python
class MyShell:
    # ... previous code ...
    
    def find_command(self, command):
        """Find command in PATH"""
        # If command contains slash, use as-is
        if '/' in command:
            if os.path.isfile(command) and os.access(command, os.X_OK):
                return command
            return None
        
        # Search in PATH
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        
        for directory in path_dirs:
            if not directory:
                continue
                
            full_path = os.path.join(directory, command)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        
        return None
    
    def expand_variables(self, text):
        """Expand environment variables in text"""
        # Simple variable expansion (improve for production use)
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, '')
        
        # Handle $VAR and ${VAR} syntax
        text = re.sub(r'\$\{([^}]+)\}', replace_var, text)
        text = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, text)
        
        return text
    
    def execute_single_command(self, command: Command):
        """Execute single command with PATH resolution and variable expansion"""
        if not command.args:
            return
        
        # Expand variables in all arguments
        expanded_args = []
        for arg in command.args:
            expanded_args.append(self.expand_variables(arg))
        
        command.args = expanded_args
        cmd = command.args[0]
        
        # Handle built-ins
        if self.is_builtin(cmd):
            self.execute_builtin(command)
            return
        
        # Find command in PATH
        cmd_path = self.find_command(cmd)
        if not cmd_path:
            print(f"myshell: command not found: {cmd}")
            self.exit_code = 127
            return
        
        # Replace command with full path
        command.args[0] = cmd_path
        
        # Execute with the updated logic from previous step
        # ... (rest of execute_single_command implementation)
```

## 🧪 Testing Your Implementation

Create comprehensive tests:

```python
def test_shell():
    """Test shell functionality"""
    import tempfile
    import os
    
    # Test lexer
    lexer = Lexer('echo "hello world" | grep hello > output.txt')
    tokens = lexer.tokenize()
    assert len(tokens) == 7  # echo, "hello world", |, grep, hello, >, output.txt
    
    # Test parser
    parser = Parser(tokens)
    pipelines = parser.parse()
    assert len(pipelines) == 1
    assert len(pipelines[0].commands) == 2
    
    # Test command execution (in controlled environment)
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        shell = MyShell()
        
        # Test basic command
        shell.execute_command('echo "test" > test.txt')
        assert os.path.exists('test.txt')
        
        # Test pipeline
        shell.execute_command('echo "line1\nline2" | sort')
        
        print("Shell tests passed!")

if __name__ == "__main__":
    test_shell()
```

## 🎯 Challenges to Extend Your Implementation

1. **Job Control**: Implement `jobs`, `fg`, `bg` commands
2. **History**: Add command history with up/down arrows
3. **Tab Completion**: Implement filename and command completion
4. **Aliases**: Add support for command aliases
5. **Functions**: Support shell function definitions
6. **Conditionals**: Add `if`, `while`, `for` constructs
7. **Globbing**: Implement filename expansion (*, ?, [])

## 📚 Key Concepts Learned

- **Process Management**: Creating and managing child processes
- **Inter-Process Communication**: Using pipes for data flow
- **File Descriptors**: Redirecting input/output streams
- **Signal Handling**: Managing process lifecycle
- **Environment Variables**: Variable expansion and export
- **Parsing**: Tokenization and syntax analysis

---

**Congratulations!** You've built a functional shell that understands the core concepts of command-line interfaces and process management.