#!/usr/bin/env python3
"""
CLI Tools Implementation - Build Your Own Command-Line Tools
=============================================================

A collection of common command-line tools implemented from scratch.
Demonstrates argument parsing, file processing, and terminal interaction.

Tools implemented:
- myecho: Enhanced echo command with formatting
- myls: Directory listing with custom options  
- wc: Word, line, and character counter
- mytail: Display last N lines of files
- mygrep: Pattern searching in files
- mycat: Display file contents

Author: Build Something Project
License: MIT
"""

import os
import sys
import re
import argparse
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Iterator


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'


class MyEcho:
    """Enhanced echo command with formatting options"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='myecho',
            description='Display text with formatting options'
        )
        self.parser.add_argument('text', nargs='*', help='Text to display')
        self.parser.add_argument('-n', '--no-newline', action='store_true',
                                 help='Do not output trailing newline')
        self.parser.add_argument('-e', '--enable-interpretation', action='store_true',
                                 help='Enable interpretation of backslash escapes')
        self.parser.add_argument('-c', '--color', choices=['red', 'green', 'blue', 'yellow'],
                                 help='Output text in color')
        self.parser.add_argument('-b', '--bold', action='store_true',
                                 help='Output bold text')
    
    def interpret_escapes(self, text: str) -> str:
        """Interpret backslash escape sequences"""
        escapes = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            '\\b': '\b',
            '\\a': '\a',
            '\\f': '\f',
            '\\v': '\v',
            '\\\\': '\\',
        }
        
        for escape, char in escapes.items():
            text = text.replace(escape, char)
        return text
    
    def run(self, args: List[str]) -> int:
        """Run the echo command"""
        try:
            parsed = self.parser.parse_args(args)
            text = ' '.join(parsed.text) if parsed.text else ''
            
            if parsed.enable_interpretation:
                text = self.interpret_escapes(text)
            
            # Apply formatting
            output = text
            if parsed.bold:
                output = Colors.BOLD + output + Colors.RESET
            
            if parsed.color:
                color_map = {
                    'red': Colors.RED,
                    'green': Colors.GREEN,
                    'blue': Colors.BLUE,
                    'yellow': Colors.YELLOW
                }
                output = color_map[parsed.color] + output + Colors.RESET
            
            # Output text
            if parsed.no_newline:
                print(output, end='')
            else:
                print(output)
            
            return 0
            
        except SystemExit as e:
            return e.code if e.code else 1
        except Exception as e:
            print(f"myecho: error: {e}", file=sys.stderr)
            return 1


class MyLs:
    """Directory listing with custom formatting"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='myls',
            description='List directory contents with custom formatting'
        )
        self.parser.add_argument('paths', nargs='*', default=['.'],
                                help='Directories or files to list')
        self.parser.add_argument('-l', '--long', action='store_true',
                                help='Use long listing format')
        self.parser.add_argument('-a', '--all', action='store_true',
                                help='Show hidden files')
        self.parser.add_argument('-H', '--human-readable', action='store_true',
                                help='Human readable file sizes')
        self.parser.add_argument('-t', '--time', action='store_true',
                                help='Sort by modification time')
        self.parser.add_argument('-r', '--reverse', action='store_true',
                                help='Reverse order while sorting')
        self.parser.add_argument('-c', '--color', action='store_true',
                                help='Colorize output')
    
    def format_size(self, size: int, human_readable: bool = False) -> str:
        """Format file size"""
        if not human_readable:
            return str(size)
        
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size < 1024:
                return f"{size:.1f}{unit}".rstrip('0').rstrip('.')
            size /= 1024
        return f"{size:.1f}P"
    
    def format_permissions(self, mode: int) -> str:
        """Format file permissions"""
        perms = ['-'] * 10
        
        # File type
        if stat.S_ISDIR(mode):
            perms[0] = 'd'
        elif stat.S_ISLNK(mode):
            perms[0] = 'l'
        
        # Owner permissions
        if mode & stat.S_IRUSR:
            perms[1] = 'r'
        if mode & stat.S_IWUSR:
            perms[2] = 'w'
        if mode & stat.S_IXUSR:
            perms[3] = 'x'
        
        # Group permissions
        if mode & stat.S_IRGRP:
            perms[4] = 'r'
        if mode & stat.S_IWGRP:
            perms[5] = 'w'
        if mode & stat.S_IXGRP:
            perms[6] = 'x'
        
        # Other permissions
        if mode & stat.S_IROTH:
            perms[7] = 'r'
        if mode & stat.S_IWOTH:
            perms[8] = 'w'
        if mode & stat.S_IXOTH:
            perms[9] = 'x'
        
        return ''.join(perms)
    
    def get_color_for_file(self, path: Path) -> str:
        """Get color code for file type"""
        if not path.exists():
            return Colors.RED
        
        if path.is_dir():
            return Colors.BLUE + Colors.BOLD
        elif path.is_symlink():
            return Colors.CYAN
        elif os.access(path, os.X_OK):
            return Colors.GREEN
        elif path.suffix in {'.txt', '.md', '.rst'}:
            return Colors.WHITE
        elif path.suffix in {'.py', '.js', '.c', '.cpp', '.h'}:
            return Colors.YELLOW
        else:
            return Colors.RESET
    
    def list_directory(self, dir_path: Path, args) -> List[Path]:
        """List and sort directory contents"""
        try:
            if dir_path.is_file():
                return [dir_path]
            
            items = []
            for item in dir_path.iterdir():
                if not args.all and item.name.startswith('.'):
                    continue
                items.append(item)
            
            # Sort items
            if args.time:
                items.sort(key=lambda x: x.stat().st_mtime, reverse=not args.reverse)
            else:
                items.sort(key=lambda x: x.name.lower(), reverse=args.reverse)
            
            return items
            
        except PermissionError:
            print(f"myls: cannot access '{dir_path}': Permission denied", file=sys.stderr)
            return []
        except FileNotFoundError:
            print(f"myls: cannot access '{dir_path}': No such file or directory", file=sys.stderr)
            return []
    
    def run(self, args: List[str]) -> int:
        """Run the ls command"""
        try:
            parsed = self.parser.parse_args(args)
            
            for path_str in parsed.paths:
                path = Path(path_str)
                items = self.list_directory(path, parsed)
                
                if not items:
                    continue
                
                if len(parsed.paths) > 1:
                    print(f"\n{path}:")
                
                # Output items
                for item in items:
                    try:
                        stat_info = item.stat()
                        
                        if parsed.long:
                            # Long format
                            perms = self.format_permissions(stat_info.st_mode)
                            size = self.format_size(stat_info.st_size, parsed.human_readable)
                            mtime = datetime.fromtimestamp(stat_info.st_mtime)
                            time_str = mtime.strftime('%b %d %H:%M')
                            
                            name = item.name
                            if parsed.color:
                                color = self.get_color_for_file(item)
                                name = color + name + Colors.RESET
                            
                            print(f"{perms} {stat_info.st_nlink:3} {stat_info.st_uid:8} {stat_info.st_gid:8} {size:>8} {time_str} {name}")
                        else:
                            # Short format
                            name = item.name
                            if parsed.color:
                                color = self.get_color_for_file(item)
                                name = color + name + Colors.RESET
                            print(name, end='  ')
                    
                    except OSError:
                        print(f"myls: cannot access '{item}': Permission denied", file=sys.stderr)
                
                if not parsed.long:
                    print()  # New line after short format
            
            return 0
            
        except SystemExit as e:
            return e.code if e.code else 1
        except Exception as e:
            print(f"myls: error: {e}", file=sys.stderr)
            return 1


class WordCount:
    """Word, line, and character counter"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='wc',
            description='Count lines, words, and characters in files'
        )
        self.parser.add_argument('files', nargs='*', 
                                help='Files to process (default: stdin)')
        self.parser.add_argument('-l', '--lines', action='store_true',
                                help='Count lines only')
        self.parser.add_argument('-w', '--words', action='store_true',
                                help='Count words only')
        self.parser.add_argument('-c', '--characters', action='store_true',
                                help='Count characters only')
    
    def count_file(self, file_path: Optional[Path] = None) -> tuple:
        """Count lines, words, and characters in a file or stdin"""
        try:
            if file_path:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                content = sys.stdin.read()
            
            lines = len(content.splitlines())
            words = len(content.split())
            chars = len(content)
            
            return lines, words, chars
            
        except FileNotFoundError:
            print(f"wc: {file_path}: No such file or directory", file=sys.stderr)
            return 0, 0, 0
        except PermissionError:
            print(f"wc: {file_path}: Permission denied", file=sys.stderr)
            return 0, 0, 0
    
    def run(self, args: List[str]) -> int:
        """Run the word count command"""
        try:
            parsed = self.parser.parse_args(args)
            
            total_lines, total_words, total_chars = 0, 0, 0
            
            # If no specific flags, show all counts
            show_all = not (parsed.lines or parsed.words or parsed.characters)
            
            files_to_process = parsed.files if parsed.files else [None]
            
            for file_str in files_to_process:
                file_path = Path(file_str) if file_str else None
                lines, words, chars = self.count_file(file_path)
                
                total_lines += lines
                total_words += words
                total_chars += chars
                
                # Format output
                output_parts = []
                if show_all or parsed.lines:
                    output_parts.append(f"{lines:8}")
                if show_all or parsed.words:
                    output_parts.append(f"{words:8}")
                if show_all or parsed.characters:
                    output_parts.append(f"{chars:8}")
                
                output = ' '.join(output_parts)
                filename = file_str if file_str else ''
                print(f"{output} {filename}".strip())
            
            # Show totals if multiple files
            if len(files_to_process) > 1:
                output_parts = []
                if show_all or parsed.lines:
                    output_parts.append(f"{total_lines:8}")
                if show_all or parsed.words:
                    output_parts.append(f"{total_words:8}")
                if show_all or parsed.characters:
                    output_parts.append(f"{total_chars:8}")
                
                output = ' '.join(output_parts)
                print(f"{output} total")
            
            return 0
            
        except SystemExit as e:
            return e.code if e.code else 1
        except Exception as e:
            print(f"wc: error: {e}", file=sys.stderr)
            return 1


class MyTail:
    """Display last N lines of files"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='mytail',
            description='Display last lines of files'
        )
        self.parser.add_argument('files', nargs='*',
                                help='Files to process (default: stdin)')
        self.parser.add_argument('-n', '--lines', type=int, default=10,
                                help='Number of lines to show (default: 10)')
        self.parser.add_argument('-f', '--follow', action='store_true',
                                help='Follow file as it grows')
    
    def tail_file(self, file_path: Optional[Path], num_lines: int) -> List[str]:
        """Get last N lines from file"""
        try:
            if file_path:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            else:
                lines = sys.stdin.readlines()
            
            return lines[-num_lines:] if len(lines) > num_lines else lines
            
        except FileNotFoundError:
            print(f"mytail: {file_path}: No such file or directory", file=sys.stderr)
            return []
        except PermissionError:
            print(f"mytail: {file_path}: Permission denied", file=sys.stderr)
            return []
    
    def run(self, args: List[str]) -> int:
        """Run the tail command"""
        try:
            parsed = self.parser.parse_args(args)
            
            files_to_process = parsed.files if parsed.files else [None]
            
            for i, file_str in enumerate(files_to_process):
                file_path = Path(file_str) if file_str else None
                
                if len(files_to_process) > 1:
                    if i > 0:
                        print()
                    print(f"==> {file_str if file_str else 'standard input'} <==")
                
                lines = self.tail_file(file_path, parsed.lines)
                for line in lines:
                    print(line, end='')
            
            return 0
            
        except SystemExit as e:
            return e.code if e.code else 1
        except Exception as e:
            print(f"mytail: error: {e}", file=sys.stderr)
            return 1


class MyGrep:
    """Pattern searching in files"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='mygrep',
            description='Search for patterns in files'
        )
        self.parser.add_argument('pattern', help='Pattern to search for')
        self.parser.add_argument('files', nargs='*',
                                help='Files to search (default: stdin)')
        self.parser.add_argument('-i', '--ignore-case', action='store_true',
                                help='Ignore case distinctions')
        self.parser.add_argument('-n', '--line-number', action='store_true',
                                help='Show line numbers')
        self.parser.add_argument('-v', '--invert-match', action='store_true',
                                help='Invert match (show non-matching lines)')
        self.parser.add_argument('-c', '--count', action='store_true',
                                help='Count matching lines only')
        self.parser.add_argument('-r', '--regex', action='store_true',
                                help='Use regular expressions')
    
    def search_file(self, file_path: Optional[Path], pattern: str, args) -> tuple:
        """Search for pattern in file"""
        try:
            if file_path:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            else:
                lines = sys.stdin.readlines()
            
            matches = []
            flags = re.IGNORECASE if args.ignore_case else 0
            
            for i, line in enumerate(lines, 1):
                line_content = line.rstrip('\n')
                
                if args.regex:
                    match = re.search(pattern, line_content, flags)
                    found = match is not None
                else:
                    if args.ignore_case:
                        found = pattern.lower() in line_content.lower()
                    else:
                        found = pattern in line_content
                
                if found != args.invert_match:  # XOR for invert logic
                    matches.append((i, line_content))
            
            return matches, len(lines)
            
        except FileNotFoundError:
            print(f"mygrep: {file_path}: No such file or directory", file=sys.stderr)
            return [], 0
        except PermissionError:
            print(f"mygrep: {file_path}: Permission denied", file=sys.stderr)
            return [], 0
        except re.error as e:
            print(f"mygrep: invalid regex: {e}", file=sys.stderr)
            return [], 0
    
    def run(self, args: List[str]) -> int:
        """Run the grep command"""
        try:
            parsed = self.parser.parse_args(args)
            
            files_to_process = parsed.files if parsed.files else [None]
            total_matches = 0
            
            for file_str in files_to_process:
                file_path = Path(file_str) if file_str else None
                matches, total_lines = self.search_file(file_path, parsed.pattern, parsed)
                
                total_matches += len(matches)
                
                if parsed.count:
                    # Just show count
                    filename_prefix = f"{file_str}:" if len(files_to_process) > 1 else ""
                    print(f"{filename_prefix}{len(matches)}")
                else:
                    # Show matching lines
                    for line_num, line_content in matches:
                        parts = []
                        
                        if len(files_to_process) > 1:
                            parts.append(file_str if file_str else "(standard input)")
                        
                        if parsed.line_number:
                            parts.append(str(line_num))
                        
                        parts.append(line_content)
                        print(':'.join(parts))
            
            # Return 0 if matches found, 1 if no matches
            return 0 if total_matches > 0 else 1
            
        except SystemExit as e:
            return e.code if e.code else 1
        except Exception as e:
            print(f"mygrep: error: {e}", file=sys.stderr)
            return 1


class MyCat:
    """Display file contents"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='mycat',
            description='Display file contents'
        )
        self.parser.add_argument('files', nargs='*',
                                help='Files to display (default: stdin)')
        self.parser.add_argument('-n', '--number', action='store_true',
                                help='Number all output lines')
        self.parser.add_argument('-b', '--number-nonblank', action='store_true',
                                help='Number non-empty output lines')
        self.parser.add_argument('-s', '--squeeze-blank', action='store_true',
                                help='Squeeze multiple blank lines')
    
    def cat_file(self, file_path: Optional[Path], args) -> bool:
        """Display contents of a file"""
        try:
            if file_path:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            else:
                lines = sys.stdin.readlines()
            
            line_num = 1
            prev_blank = False
            
            for line in lines:
                line_content = line.rstrip('\n')
                is_blank = len(line_content.strip()) == 0
                
                # Handle squeeze blank lines
                if args.squeeze_blank and is_blank and prev_blank:
                    continue
                
                # Handle line numbering
                prefix = ""
                if args.number:
                    prefix = f"{line_num:6}  "
                    line_num += 1
                elif args.number_nonblank and not is_blank:
                    prefix = f"{line_num:6}  "
                    line_num += 1
                
                print(f"{prefix}{line_content}")
                prev_blank = is_blank
            
            return True
            
        except FileNotFoundError:
            print(f"mycat: {file_path}: No such file or directory", file=sys.stderr)
            return False
        except PermissionError:
            print(f"mycat: {file_path}: Permission denied", file=sys.stderr)
            return False
    
    def run(self, args: List[str]) -> int:
        """Run the cat command"""
        try:
            parsed = self.parser.parse_args(args)
            
            files_to_process = parsed.files if parsed.files else [None]
            success = True
            
            for file_str in files_to_process:
                file_path = Path(file_str) if file_str else None
                if not self.cat_file(file_path, parsed):
                    success = False
            
            return 0 if success else 1
            
        except SystemExit as e:
            return e.code if e.code else 1
        except Exception as e:
            print(f"mycat: error: {e}", file=sys.stderr)
            return 1


class CLIToolsRunner:
    """Main runner for CLI tools"""
    
    def __init__(self):
        self.tools = {
            'myecho': MyEcho(),
            'myls': MyLs(),
            'wc': WordCount(),
            'mytail': MyTail(),
            'mygrep': MyGrep(),
            'mycat': MyCat(),
        }
    
    def run_tool(self, tool_name: str, args: List[str]) -> int:
        """Run a specific tool"""
        if tool_name not in self.tools:
            print(f"Unknown tool: {tool_name}", file=sys.stderr)
            print(f"Available tools: {', '.join(self.tools.keys())}", file=sys.stderr)
            return 1
        
        return self.tools[tool_name].run(args)
    
    def list_tools(self):
        """List available tools"""
        print("Available CLI Tools:")
        print("===================")
        for name, tool in self.tools.items():
            doc = tool.__class__.__doc__ or "No description available"
            print(f"  {name:12} - {doc}")
    
    def run_tests(self):
        """Run tests for CLI tools"""
        print("Testing CLI Tools")
        print("=" * 50)
        
        # Test data setup
        test_dir = Path('/tmp/cli_test')
        test_dir.mkdir(exist_ok=True)
        
        # Create test files
        (test_dir / 'test1.txt').write_text("Hello World\nThis is line 2\nThis is line 3\n")
        (test_dir / 'test2.txt').write_text("Python\nJavaScript\nGo\nRust\n")
        (test_dir / 'empty.txt').write_text("")
        
        tests_passed = 0
        total_tests = 6
        
        # Test myecho
        print("1. Testing myecho...")
        try:
            result = self.run_tool('myecho', ['Hello', 'World'])
            if result == 0:
                print("   ✓ Basic echo works")
                tests_passed += 1
            else:
                print("   ✗ Basic echo failed")
        except Exception as e:
            print(f"   ✗ Echo test error: {e}")
        
        # Test myls
        print("2. Testing myls...")
        try:
            result = self.run_tool('myls', [str(test_dir)])
            if result == 0:
                print("   ✓ Directory listing works")
                tests_passed += 1
            else:
                print("   ✗ Directory listing failed")
        except Exception as e:
            print(f"   ✗ ls test error: {e}")
        
        # Test wc
        print("3. Testing wc...")
        try:
            result = self.run_tool('wc', [str(test_dir / 'test1.txt')])
            if result == 0:
                print("   ✓ Word count works")
                tests_passed += 1
            else:
                print("   ✗ Word count failed")
        except Exception as e:
            print(f"   ✗ wc test error: {e}")
        
        # Test mytail
        print("4. Testing mytail...")
        try:
            result = self.run_tool('mytail', ['-n', '2', str(test_dir / 'test1.txt')])
            if result == 0:
                print("   ✓ Tail command works")
                tests_passed += 1
            else:
                print("   ✗ Tail command failed")
        except Exception as e:
            print(f"   ✗ tail test error: {e}")
        
        # Test mygrep
        print("5. Testing mygrep...")
        try:
            result = self.run_tool('mygrep', ['line', str(test_dir / 'test1.txt')])
            if result == 0:
                print("   ✓ Grep search works")
                tests_passed += 1
            else:
                print("   ✗ Grep search failed")
        except Exception as e:
            print(f"   ✗ grep test error: {e}")
        
        # Test mycat
        print("6. Testing mycat...")
        try:
            result = self.run_tool('mycat', [str(test_dir / 'test2.txt')])
            if result == 0:
                print("   ✓ Cat display works")
                tests_passed += 1
            else:
                print("   ✗ Cat display failed")
        except Exception as e:
            print(f"   ✗ cat test error: {e}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        # Summary
        print("\n" + "=" * 50)
        if tests_passed == total_tests:
            print("🎉 All CLI tool tests passed!")
            print(f"✅ Passed: {tests_passed}/{total_tests}")
        else:
            print(f"⚠️  Some tests failed: {tests_passed}/{total_tests}")
            print(f"❌ Failed: {total_tests - tests_passed}")
        
        print("\nYou can now use individual CLI tools:")
        print("  python3 cli_tools.py myecho 'Hello World'")
        print("  python3 cli_tools.py myls -l")
        print("  python3 cli_tools.py wc filename.txt")
        print("  python3 cli_tools.py mytail -n 5 filename.txt")
        print("  python3 cli_tools.py mygrep pattern filename.txt")
        print("  python3 cli_tools.py mycat filename.txt")


def main():
    """Main entry point"""
    runner = CLIToolsRunner()
    
    if len(sys.argv) < 2:
        print("Usage: python3 cli_tools.py <tool> [args...]")
        print("       python3 cli_tools.py --test")
        print("       python3 cli_tools.py --list")
        return 1
    
    command = sys.argv[1]
    
    if command == '--test':
        runner.run_tests()
        return 0
    elif command == '--list':
        runner.list_tools()
        return 0
    else:
        return runner.run_tool(command, sys.argv[2:])


def run_tests():
    """Test runner function for external use"""
    runner = CLIToolsRunner()
    runner.run_tests()


if __name__ == "__main__":
    sys.exit(main())