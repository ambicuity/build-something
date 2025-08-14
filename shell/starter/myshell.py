#!/usr/bin/env python3
"""
MyShell - A command-line shell implementation from scratch

This shell demonstrates key operating system concepts:
- Process creation and management
- Inter-process communication with pipes
- File redirection and I/O handling
- Command parsing and tokenization
- Environment variable management
"""

import os
import sys
import subprocess
import shlex
import signal
import re
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


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
    """Tokenizes command line input into structured tokens"""
    
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
    """Represents a parsed command with arguments and redirections"""
    
    def __init__(self):
        self.args = []
        self.input_redirect = None
        self.output_redirect = None
        self.append_redirect = None
        self.background = False
    
    def __repr__(self):
        return f"Command({self.args}, bg={self.background})"


class Pipeline:
    """Represents a pipeline of commands connected by pipes"""
    
    def __init__(self):
        self.commands = []
    
    def __repr__(self):
        return f"Pipeline({self.commands})"


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
    
    def _current_token(self) -> Optional[Token]:
        """Get current token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None


class Job:
    """Represents a background job"""
    
    def __init__(self, job_id: int, process: subprocess.Popen, command: str):
        self.job_id = job_id
        self.process = process
        self.command = command
        self.status = "Running"
    
    def is_running(self) -> bool:
        """Check if job is still running"""
        if self.process.poll() is None:
            return True
        else:
            self.status = f"Done ({self.process.returncode})"
            return False


class MyShell:
    """A complete shell implementation with advanced features"""
    
    def __init__(self):
        self.running = True
        self.exit_code = 0
        self.background_jobs: List[Job] = []
        self.job_counter = 0
        self.aliases = {}
        
        # Set up signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTSTP, self._signal_handler)
    
    def start(self):
        """Start the shell REPL"""
        self._print_banner()
        
        while self.running:
            try:
                # Clean up finished background jobs
                self._cleanup_jobs()
                
                # Display prompt
                prompt = self._get_prompt()
                
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
            except Exception as e:
                print(f"myshell: unexpected error: {e}")
        
        # Wait for background jobs to complete
        self._wait_for_jobs()
        return self.exit_code
    
    def _print_banner(self):
        """Print shell startup banner"""
        print("╭─────────────────────────────────────────╮")
        print("│           MyShell v1.0                  │")
        print("│     A Shell Built From Scratch         │")
        print("├─────────────────────────────────────────┤")
        print("│  Features:                              │")
        print("│  • Command parsing & execution          │")
        print("│  • Pipes and redirections               │")
        print("│  • Background processes                 │")
        print("│  • Environment variables                │")
        print("│  • Built-in commands                    │")
        print("│                                         │")
        print("│  Type 'help' for commands or 'exit'    │")
        print("╰─────────────────────────────────────────╯")
    
    def _get_prompt(self) -> str:
        """Generate shell prompt"""
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        
        # Replace home directory with ~
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        
        # Show only last directory if path is too long
        if len(cwd) > 20:
            cwd = "..." + cwd[-17:]
        
        return f"\033[1;34mmyshell\033[0m:\033[1;32m{cwd}\033[0m$ "
    
    def _signal_handler(self, signum, frame):
        """Handle signals (Ctrl+C, Ctrl+Z)"""
        if signum == signal.SIGINT:
            # Ctrl+C - handled by main loop
            pass
        elif signum == signal.SIGTSTP:
            # Ctrl+Z - suspend (simplified)
            print("\n^Z (job control not fully implemented)")
    
    def execute_command(self, command_line: str):
        """Execute command line with full parsing"""
        try:
            # Handle aliases
            command_line = self._expand_aliases(command_line)
            
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
    
    def _expand_aliases(self, command_line: str) -> str:
        """Expand command aliases"""
        words = command_line.split()
        if words and words[0] in self.aliases:
            words[0] = self.aliases[words[0]]
            return ' '.join(words)
        return command_line
    
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
        
        try:
            # Create pipes for inter-process communication
            for i in range(len(pipeline.commands) - 1):
                read_fd, write_fd = os.pipe()
                pipes.append((read_fd, write_fd))
            
            for i, command in enumerate(pipeline.commands):
                # Handle built-ins in pipeline (simplified approach)
                if command.args and self.is_builtin(command.args[0]):
                    print("myshell: warning: built-ins in pipelines have limited support")
                    continue
                
                # Find command
                cmd_path = self.find_command(command.args[0])
                if not cmd_path:
                    print(f"myshell: command not found: {command.args[0]}")
                    continue
                
                # Set up file descriptors
                stdin_fd = None
                stdout_fd = None
                
                # Input: from previous pipe or file redirection
                if i > 0:  # Not first command
                    stdin_fd = pipes[i-1][0]
                elif command.input_redirect:
                    try:
                        stdin_fd = os.open(command.input_redirect, os.O_RDONLY)
                    except OSError as e:
                        print(f"myshell: {command.input_redirect}: {e}")
                        continue
                
                # Output: to next pipe or file redirection
                if i < len(pipeline.commands) - 1:  # Not last command
                    stdout_fd = pipes[i][1]
                elif command.output_redirect:
                    try:
                        stdout_fd = os.open(command.output_redirect, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                    except OSError as e:
                        print(f"myshell: {command.output_redirect}: {e}")
                        continue
                elif command.append_redirect:
                    try:
                        stdout_fd = os.open(command.append_redirect, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                    except OSError as e:
                        print(f"myshell: {command.append_redirect}: {e}")
                        continue
                
                # Expand variables
                expanded_args = [self.expand_variables(arg) for arg in command.args]
                expanded_args[0] = cmd_path
                
                # Start process
                process = subprocess.Popen(
                    expanded_args,
                    stdin=stdin_fd,
                    stdout=stdout_fd,
                    stderr=subprocess.PIPE
                )
                processes.append(process)
                
                # Close file descriptors in parent
                if stdin_fd is not None and stdin_fd not in [0, 1, 2]:
                    os.close(stdin_fd)
                if stdout_fd is not None and stdout_fd not in [0, 1, 2]:
                    os.close(stdout_fd)
            
            # Close all pipes in parent process
            for read_fd, write_fd in pipes:
                try:
                    os.close(read_fd)
                    os.close(write_fd)
                except:
                    pass
            
            # Wait for all processes
            for process in processes:
                try:
                    process.wait()
                except KeyboardInterrupt:
                    process.terminate()
                    print("\n^C")
                    break
            
        except Exception as e:
            print(f"myshell: pipeline error: {e}")
    
    def execute_single_command(self, command: Command):
        """Execute a single command with redirections"""
        if not command.args:
            return
        
        # Expand variables in arguments
        expanded_args = [self.expand_variables(arg) for arg in command.args]
        command.args = expanded_args
        
        cmd = command.args[0]
        
        # Handle built-in commands
        if self.is_builtin(cmd):
            self.execute_builtin(command)
            return
        
        # Find external command
        cmd_path = self.find_command(cmd)
        if not cmd_path:
            print(f"myshell: command not found: {cmd}")
            self.exit_code = 127
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
            
            # Replace command name with full path
            command.args[0] = cmd_path
            
            # Start process
            process = subprocess.Popen(
                command.args,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr
            )
            
            if command.background:
                # Background process
                self.job_counter += 1
                job = Job(self.job_counter, process, ' '.join(command.args))
                self.background_jobs.append(job)
                print(f"[{job.job_id}] {process.pid}")
            else:
                # Foreground process
                try:
                    process.wait()
                    self.exit_code = process.returncode
                except KeyboardInterrupt:
                    process.terminate()
                    print("\n^C")
            
            # Close file handles
            if stdin and stdin != sys.stdin:
                stdin.close()
            if stdout and stdout != sys.stdout:
                stdout.close()
                
        except Exception as e:
            print(f"myshell: error: {e}")
            self.exit_code = 1
    
    def find_command(self, command: str) -> Optional[str]:
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
    
    def expand_variables(self, text: str) -> str:
        """Expand environment variables in text"""
        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, '')
        
        # Handle $VAR and ${VAR} syntax
        text = re.sub(r'\$\{([^}]+)\}', replace_var, text)
        text = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, text)
        
        return text
    
    def is_builtin(self, command: str) -> bool:
        """Check if command is a built-in"""
        return command in [
            'exit', 'help', 'cd', 'pwd', 'echo', 'env', 'export', 
            'jobs', 'alias', 'unalias', 'history', 'type'
        ]
    
    def execute_builtin(self, command: Command):
        """Execute built-in command"""
        cmd = command.args[0]
        args = command.args[1:]
        
        if cmd == 'exit':
            if args:
                try:
                    self.exit_code = int(args[0])
                except ValueError:
                    print("exit: numeric argument required")
                    self.exit_code = 2
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
            self.builtin_env(args)
        elif cmd == 'export':
            self.builtin_export(args)
        elif cmd == 'jobs':
            self.builtin_jobs()
        elif cmd == 'alias':
            self.builtin_alias(args)
        elif cmd == 'unalias':
            self.builtin_unalias(args)
        elif cmd == 'type':
            self.builtin_type(args)
    
    def builtin_help(self):
        """Display help information"""
        print("""
MyShell Built-in Commands:
  help              Show this help message
  exit [code]       Exit the shell with optional exit code
  cd [dir]          Change directory (default: home directory)
  pwd               Print working directory
  echo [args...]    Display arguments
  env [var]         Show environment variables
  export var=value  Set environment variable
  jobs              List background jobs
  alias [name=cmd]  Create command alias
  unalias name      Remove alias
  type command      Show command type and location
  
Shell Features:
  • Pipes: cmd1 | cmd2
  • Redirections: cmd > file, cmd < file, cmd >> file
  • Background: cmd &
  • Variables: $VAR or ${VAR}
  • Quotes: "text" or 'text'
        """)
    
    def builtin_cd(self, args: List[str]):
        """Change directory built-in"""
        if not args:
            # cd with no arguments goes to home directory
            target = os.path.expanduser("~")
        elif args[0] == '-':
            # cd - goes to previous directory (simplified)
            target = os.environ.get('OLDPWD', os.path.expanduser("~"))
        else:
            target = args[0]
        
        # Expand variables
        target = self.expand_variables(target)
        
        try:
            old_pwd = os.getcwd()
            os.chdir(target)
            os.environ['OLDPWD'] = old_pwd
            os.environ['PWD'] = os.getcwd()
        except OSError as e:
            print(f"cd: {e}")
            self.exit_code = 1
    
    def builtin_env(self, args: List[str]):
        """Environment variables built-in"""
        if not args:
            # Show all environment variables
            for key, value in sorted(os.environ.items()):
                print(f"{key}={value}")
        else:
            # Show specific variable
            for var in args:
                value = os.environ.get(var)
                if value is not None:
                    print(f"{var}={value}")
                else:
                    print(f"env: {var}: not found")
    
    def builtin_export(self, args: List[str]):
        """Export environment variable"""
        for arg in args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                value = self.expand_variables(value)
                os.environ[key] = value
            else:
                # Show exported variable
                value = os.environ.get(arg)
                if value is not None:
                    print(f"export {arg}={value}")
                else:
                    print(f"export: {arg}: not found")
    
    def builtin_jobs(self):
        """List background jobs"""
        if not self.background_jobs:
            return
        
        for job in self.background_jobs[:]:  # Copy list to avoid modification during iteration
            status = "Running" if job.is_running() else job.status
            print(f"[{job.job_id}]  {status}\t{job.command}")
    
    def builtin_alias(self, args: List[str]):
        """Create or show aliases"""
        if not args:
            # Show all aliases
            for name, command in self.aliases.items():
                print(f"alias {name}='{command}'")
        else:
            for arg in args:
                if '=' in arg:
                    name, command = arg.split('=', 1)
                    self.aliases[name] = command
                else:
                    # Show specific alias
                    if arg in self.aliases:
                        print(f"alias {arg}='{self.aliases[arg]}'")
                    else:
                        print(f"alias: {arg}: not found")
    
    def builtin_unalias(self, args: List[str]):
        """Remove aliases"""
        for arg in args:
            if arg in self.aliases:
                del self.aliases[arg]
            else:
                print(f"unalias: {arg}: not found")
    
    def builtin_type(self, args: List[str]):
        """Show command type"""
        for arg in args:
            if self.is_builtin(arg):
                print(f"{arg} is a shell builtin")
            elif arg in self.aliases:
                print(f"{arg} is aliased to `{self.aliases[arg]}'")
            else:
                cmd_path = self.find_command(arg)
                if cmd_path:
                    print(f"{arg} is {cmd_path}")
                else:
                    print(f"{arg}: not found")
    
    def _cleanup_jobs(self):
        """Clean up finished background jobs"""
        finished_jobs = []
        for job in self.background_jobs[:]:
            if not job.is_running():
                print(f"[{job.job_id}]  Done\t{job.command}")
                finished_jobs.append(job)
        
        for job in finished_jobs:
            self.background_jobs.remove(job)
    
    def _wait_for_jobs(self):
        """Wait for all background jobs to complete"""
        if self.background_jobs:
            print("Waiting for background jobs to complete...")
            for job in self.background_jobs:
                try:
                    job.process.wait()
                except:
                    pass


def main():
    """Main entry point"""
    shell = MyShell()
    return shell.start()


if __name__ == "__main__":
    sys.exit(main())