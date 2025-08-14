#!/usr/bin/env python3
"""
MyTextEditor - A terminal-based text editor built from scratch

This editor demonstrates core text editing concepts:
- Terminal control and raw input handling
- Efficient text buffer management using gap buffers
- Cursor positioning and viewport management
- File operations (load/save)
- Basic syntax highlighting
- Modal editing with commands

Built using only Python standard library.
"""

import sys
import os
import termios
import tty
import select
from typing import Optional, List, Tuple
from enum import Enum


class Key(Enum):
    """Special key codes and escape sequences"""
    CTRL_C = 3
    CTRL_Q = 17
    CTRL_S = 19
    CTRL_X = 24
    BACKSPACE = 127
    DELETE = 126
    ENTER = 13
    ESCAPE = 27
    TAB = 9
    
    # Arrow keys (escape sequences)
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    
    PAGE_UP = "PAGE_UP"
    PAGE_DOWN = "PAGE_DOWN"
    HOME = "HOME"
    END = "END"


class Terminal:
    """Terminal control and raw mode handling"""
    
    def __init__(self):
        self.original_settings = None
        self.raw_mode = False
        self.size = self.get_terminal_size()
    
    def enter_raw_mode(self):
        """Enter raw terminal mode for character-by-character input"""
        if not sys.stdin.isatty():
            raise RuntimeError("Not running in a terminal")
        
        self.original_settings = termios.tcgetattr(sys.stdin.fileno())
        tty.setraw(sys.stdin.fileno())
        self.raw_mode = True
        
        # Hide cursor initially and enable alternate screen
        sys.stdout.write('\x1b[?1049h\x1b[?25l')
        sys.stdout.flush()
    
    def exit_raw_mode(self):
        """Restore original terminal settings"""
        if self.original_settings and self.raw_mode:
            # Restore cursor and exit alternate screen
            sys.stdout.write('\x1b[?25h\x1b[?1049l')
            sys.stdout.flush()
            
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_settings)
            self.raw_mode = False
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions (rows, cols)"""
        try:
            size = os.get_terminal_size()
            return size.lines, size.columns
        except:
            return 24, 80  # Default fallback
    
    def clear_screen(self):
        """Clear the terminal screen"""
        sys.stdout.write('\x1b[2J\x1b[H')
    
    def move_cursor(self, row: int, col: int):
        """Move cursor to specific position (1-indexed)"""
        sys.stdout.write(f'\x1b[{row};{col}H')
    
    def hide_cursor(self):
        """Hide the cursor"""
        sys.stdout.write('\x1b[?25l')
    
    def show_cursor(self):
        """Show the cursor"""
        sys.stdout.write('\x1b[?25h')
    
    def read_key(self) -> Optional[str]:
        """Read a single key press with escape sequence handling"""
        if not self.raw_mode:
            return None
        
        # Check if input is available (non-blocking)
        if not select.select([sys.stdin], [], [], 0.05)[0]:
            return None
        
        char = sys.stdin.read(1)
        if not char:
            return None
        
        # Handle escape sequences
        if ord(char) == Key.ESCAPE.value:
            # Read potential escape sequence
            if select.select([sys.stdin], [], [], 0.1)[0]:
                seq = sys.stdin.read(1)
                if seq == '[':
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'A':
                            return Key.UP.value
                        elif seq2 == 'B':
                            return Key.DOWN.value
                        elif seq2 == 'C':
                            return Key.RIGHT.value
                        elif seq2 == 'D':
                            return Key.LEFT.value
                        elif seq2 == '5':
                            # Page Up (consume trailing ~)
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                sys.stdin.read(1)
                            return Key.PAGE_UP.value
                        elif seq2 == '6':
                            # Page Down (consume trailing ~)
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                sys.stdin.read(1)
                            return Key.PAGE_DOWN.value
                        elif seq2 == 'H':
                            return Key.HOME.value
                        elif seq2 == 'F':
                            return Key.END.value
                        elif seq2 == '3':
                            # Delete key (consume trailing ~)
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                sys.stdin.read(1)
                            return str(Key.DELETE.value)
            # If no escape sequence follows, return ESC
            return char
        
        return char


class TextBuffer:
    """Efficient text buffer using gap buffer data structure"""
    
    def __init__(self, initial_text: str = "", gap_size: int = 512):
        self.gap_size = gap_size
        # Convert text to list and add gap
        text_list = list(initial_text)
        self.buffer = text_list + [None] * gap_size
        self.gap_start = len(text_list)
        self.gap_end = len(self.buffer)
        self.modified = False
    
    def __len__(self) -> int:
        """Return logical length of text (excluding gap)"""
        return len(self.buffer) - (self.gap_end - self.gap_start)
    
    def get_text(self) -> str:
        """Get the complete text as string"""
        before_gap = self.buffer[:self.gap_start]
        after_gap = self.buffer[self.gap_end:]
        chars = before_gap + after_gap
        return ''.join(char for char in chars if char is not None)
    
    def get_lines(self) -> List[str]:
        """Get text as list of lines"""
        text = self.get_text()
        if not text:
            return ['']
        return text.split('\n')
    
    def _move_gap(self, position: int):
        """Move gap to specified position"""
        if position < 0:
            position = 0
        elif position > len(self):
            position = len(self)
        
        if position < self.gap_start:
            # Move gap left
            chars_to_move = self.gap_start - position
            for _ in range(chars_to_move):
                self.gap_end -= 1
                self.gap_start -= 1
                self.buffer[self.gap_end] = self.buffer[self.gap_start]
                self.buffer[self.gap_start] = None
        elif position > self.gap_start:
            # Move gap right
            chars_to_move = position - self.gap_start
            for _ in range(chars_to_move):
                self.buffer[self.gap_start] = self.buffer[self.gap_end]
                self.buffer[self.gap_end] = None
                self.gap_start += 1
                self.gap_end += 1
    
    def _expand_gap(self):
        """Expand gap when it becomes too small"""
        if self.gap_end - self.gap_start < 10:
            # Insert new gap space
            new_gap = [None] * self.gap_size
            self.buffer = (self.buffer[:self.gap_start] + 
                          new_gap + 
                          self.buffer[self.gap_start:])
            self.gap_end = self.gap_start + len(new_gap)
    
    def insert_char(self, position: int, char: str):
        """Insert character at position"""
        self._move_gap(position)
        
        if self.gap_start >= self.gap_end:
            self._expand_gap()
        
        self.buffer[self.gap_start] = char
        self.gap_start += 1
        self.modified = True
    
    def delete_char(self, position: int) -> Optional[str]:
        """Delete character at position"""
        if position < 0 or position >= len(self):
            return None
        
        self._move_gap(position + 1)
        
        if self.gap_start > 0:
            self.gap_start -= 1
            deleted_char = self.buffer[self.gap_start]
            self.buffer[self.gap_start] = None
            self.modified = True
            return deleted_char
        
        return None
    
    def insert_text(self, position: int, text: str):
        """Insert multiple characters at position"""
        for i, char in enumerate(text):
            self.insert_char(position + i, char)


class Cursor:
    """Manages cursor position in the text buffer"""
    
    def __init__(self, buffer: TextBuffer):
        self.buffer = buffer
        self.row = 0
        self.col = 0
        self._desired_col = 0  # Remember column for vertical movement
    
    def get_buffer_position(self) -> int:
        """Convert row/col to buffer position"""
        lines = self.buffer.get_lines()
        position = 0
        
        # Add characters from previous lines
        for i in range(min(self.row, len(lines))):
            if i < len(lines) - 1:  # Not the last line
                position += len(lines[i]) + 1  # +1 for newline
            else:
                position += len(lines[i])
        
        # Add column position in current line
        if self.row < len(lines):
            position += min(self.col, len(lines[self.row]))
        
        return position
    
    def set_position_from_buffer(self, buffer_pos: int):
        """Set cursor position from buffer position"""
        lines = self.buffer.get_lines()
        current_pos = 0
        
        for row, line in enumerate(lines):
            if current_pos + len(line) >= buffer_pos:
                self.row = row
                self.col = buffer_pos - current_pos
                self._desired_col = self.col
                return
            current_pos += len(line) + 1  # +1 for newline
        
        # Position is at end of buffer
        if lines:
            self.row = len(lines) - 1
            self.col = len(lines[-1])
        else:
            self.row = 0
            self.col = 0
        self._desired_col = self.col
    
    def move_left(self):
        """Move cursor left"""
        if self.col > 0:
            self.col -= 1
            self._desired_col = self.col
        elif self.row > 0:
            # Move to end of previous line
            self.row -= 1
            lines = self.buffer.get_lines()
            if self.row < len(lines):
                self.col = len(lines[self.row])
                self._desired_col = self.col
    
    def move_right(self):
        """Move cursor right"""
        lines = self.buffer.get_lines()
        if self.row < len(lines):
            if self.col < len(lines[self.row]):
                self.col += 1
                self._desired_col = self.col
            elif self.row < len(lines) - 1:
                # Move to start of next line
                self.row += 1
                self.col = 0
                self._desired_col = 0
    
    def move_up(self):
        """Move cursor up"""
        if self.row > 0:
            self.row -= 1
            lines = self.buffer.get_lines()
            if self.row < len(lines):
                self.col = min(self._desired_col, len(lines[self.row]))
    
    def move_down(self):
        """Move cursor down"""
        lines = self.buffer.get_lines()
        if self.row < len(lines) - 1:
            self.row += 1
            self.col = min(self._desired_col, len(lines[self.row]))
    
    def move_to_line_start(self):
        """Move cursor to start of current line"""
        self.col = 0
        self._desired_col = 0
    
    def move_to_line_end(self):
        """Move cursor to end of current line"""
        lines = self.buffer.get_lines()
        if self.row < len(lines):
            self.col = len(lines[self.row])
            self._desired_col = self.col


class StatusBar:
    """Status bar showing editor information"""
    
    def __init__(self):
        self.message = ""
        self.filename = "untitled"
    
    def render(self, terminal: Terminal, cursor: Cursor, buffer: TextBuffer) -> str:
        """Render status bar content"""
        rows, cols = terminal.size
        
        # Left side: filename and modified indicator
        left_part = f" {self.filename}"
        if buffer.modified:
            left_part += " [modified]"
        
        # Right side: cursor position and buffer info
        lines = buffer.get_lines()
        right_part = f" {cursor.row + 1}:{cursor.col + 1} ({len(lines)} lines) "
        
        # Message in center
        available_space = cols - len(left_part) - len(right_part)
        if self.message and available_space > 4:
            center_part = f" | {self.message[:available_space-4]} | "
            available_space -= len(center_part)
        else:
            center_part = " | "
            available_space -= 3
        
        # Fill with spaces
        padding = " " * max(0, available_space)
        
        return left_part + center_part + padding + right_part


class SyntaxHighlighter:
    """Basic syntax highlighting for Python code"""
    
    # Python keywords for highlighting
    KEYWORDS = {
        'def', 'class', 'if', 'else', 'elif', 'while', 'for', 'in', 'return',
        'import', 'from', 'try', 'except', 'finally', 'with', 'as', 'pass',
        'break', 'continue', 'True', 'False', 'None', 'and', 'or', 'not',
        'is', 'lambda', 'global', 'nonlocal', 'assert', 'del', 'yield'
    }
    
    def highlight_line(self, line: str) -> str:
        """Apply basic syntax highlighting to a line"""
        if not line:
            return line
        
        # Very basic highlighting - real editors use proper parsers
        result = ""
        i = 0
        
        while i < len(line):
            char = line[i]
            
            # String literals
            if char in ['"', "'"]:
                quote = char
                string_start = i
                result += f"\x1b[32m{char}"  # Green for strings
                i += 1
                
                while i < len(line):
                    if line[i] == quote:
                        result += f"{line[i]}\x1b[0m"  # End green
                        i += 1
                        break
                    elif line[i] == '\\' and i + 1 < len(line):
                        result += line[i:i+2]
                        i += 2
                    else:
                        result += line[i]
                        i += 1
                else:
                    result += "\x1b[0m"  # End color if string not closed
                continue
            
            # Comments
            if char == '#':
                result += f"\x1b[90m{line[i:]}\x1b[0m"  # Gray for comments
                break
            
            # Keywords and identifiers
            if char.isalpha() or char == '_':
                word_start = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                word = line[word_start:i]
                
                if word in self.KEYWORDS:
                    result += f"\x1b[34m{word}\x1b[0m"  # Blue for keywords
                else:
                    result += word
                continue
            
            # Numbers
            if char.isdigit():
                number_start = i
                while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                    i += 1
                number = line[number_start:i]
                result += f"\x1b[33m{number}\x1b[0m"  # Yellow for numbers
                continue
            
            # Regular character
            result += char
            i += 1
        
        return result


class TextEditor:
    """Complete text editor implementation"""
    
    def __init__(self):
        self.terminal = Terminal()
        self.buffer = TextBuffer()
        self.cursor = Cursor(self.buffer)
        self.status_bar = StatusBar()
        self.syntax_highlighter = SyntaxHighlighter()
        self.viewport_row = 0  # Top row of viewport
        self.running = False
        self.command_mode = False
        self.command_buffer = ""
        self.quit_confirmation = False
    
    def run(self, filename: Optional[str] = None):
        """Start the text editor"""
        try:
            self.terminal.enter_raw_mode()
            
            if filename:
                self.load_file(filename)
            
            self.running = True
            self.render()
            
            while self.running:
                key = self.terminal.read_key()
                if key:
                    self.handle_key(key)
                    self.render()
        
        except Exception as e:
            self.status_bar.message = f"Error: {e}"
        finally:
            self.terminal.exit_raw_mode()
    
    def load_file(self, filename: str):
        """Load file into buffer"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    self.buffer = TextBuffer(content)
                    self.cursor = Cursor(self.buffer)
                    self.buffer.modified = False
                    self.status_bar.filename = filename
                    self.status_bar.message = f"Loaded {filename}"
            else:
                self.status_bar.filename = filename
                self.status_bar.message = f"New file: {filename}"
        except Exception as e:
            self.status_bar.message = f"Error loading {filename}: {e}"
    
    def save_file(self, filename: Optional[str] = None):
        """Save buffer to file"""
        try:
            target_filename = filename or self.status_bar.filename
            
            with open(target_filename, 'w', encoding='utf-8') as f:
                f.write(self.buffer.get_text())
            
            self.buffer.modified = False
            self.status_bar.filename = target_filename
            self.status_bar.message = f"Saved {target_filename}"
            
        except Exception as e:
            self.status_bar.message = f"Error saving: {e}"
    
    def handle_key(self, key: str):
        """Handle key press"""
        # Reset quit confirmation on any key except Ctrl+Q
        if len(key) == 1 and ord(key) != Key.CTRL_Q.value:
            self.quit_confirmation = False
        
        if self.command_mode:
            self.handle_command_key(key)
            return
        
        # Handle control keys
        if len(key) == 1:
            code = ord(key)
            
            if code == Key.CTRL_Q.value:
                if self.buffer.modified and not self.quit_confirmation:
                    self.status_bar.message = "Unsaved changes! Press Ctrl+Q again to quit"
                    self.quit_confirmation = True
                else:
                    self.running = False
                return
            
            elif code == Key.CTRL_S.value:
                self.save_file()
                return
            
            elif code == Key.CTRL_X.value:
                self.command_mode = True
                self.command_buffer = ""
                self.status_bar.message = "Command: "
                return
            
            elif code == Key.BACKSPACE.value or code == 8:  # Backspace
                if self.cursor.col > 0 or self.cursor.row > 0:
                    pos = self.cursor.get_buffer_position()
                    if pos > 0:
                        self.buffer.delete_char(pos - 1)
                        self.cursor.set_position_from_buffer(pos - 1)
                return
            
            elif code == Key.DELETE.value:
                pos = self.cursor.get_buffer_position()
                self.buffer.delete_char(pos)
                return
            
            elif code == Key.ENTER.value:
                pos = self.cursor.get_buffer_position()
                self.buffer.insert_char(pos, '\n')
                self.cursor.set_position_from_buffer(pos + 1)
                return
            
            elif code == Key.TAB.value:
                pos = self.cursor.get_buffer_position()
                self.buffer.insert_text(pos, "    ")  # 4 spaces
                self.cursor.set_position_from_buffer(pos + 4)
                return
            
            elif 32 <= code <= 126:  # Printable ASCII
                pos = self.cursor.get_buffer_position()
                self.buffer.insert_char(pos, key)
                self.cursor.set_position_from_buffer(pos + 1)
                return
        
        # Handle special keys
        if key == Key.UP.value:
            self.cursor.move_up()
        elif key == Key.DOWN.value:
            self.cursor.move_down()
        elif key == Key.LEFT.value:
            self.cursor.move_left()
        elif key == Key.RIGHT.value:
            self.cursor.move_right()
        elif key == Key.HOME.value:
            self.cursor.move_to_line_start()
        elif key == Key.END.value:
            self.cursor.move_to_line_end()
        elif key == Key.PAGE_UP.value:
            for _ in range(10):
                self.cursor.move_up()
        elif key == Key.PAGE_DOWN.value:
            for _ in range(10):
                self.cursor.move_down()
    
    def handle_command_key(self, key: str):
        """Handle keys in command mode"""
        if len(key) == 1:
            code = ord(key)
            
            if code == Key.ENTER.value:
                self.execute_command(self.command_buffer)
                self.command_mode = False
                return
            
            elif code == Key.ESCAPE.value or code == Key.CTRL_C.value:
                self.command_mode = False
                self.status_bar.message = "Command cancelled"
                return
            
            elif code == Key.BACKSPACE.value:
                if self.command_buffer:
                    self.command_buffer = self.command_buffer[:-1]
                self.status_bar.message = f"Command: {self.command_buffer}"
                return
            
            elif 32 <= code <= 126:  # Printable characters
                self.command_buffer += key
                self.status_bar.message = f"Command: {self.command_buffer}"
    
    def execute_command(self, command: str):
        """Execute editor command"""
        parts = command.strip().split()
        if not parts:
            self.status_bar.message = ""
            return
        
        cmd = parts[0].lower()
        
        if cmd in ('q', 'quit'):
            if self.buffer.modified:
                self.status_bar.message = "Unsaved changes! Use 'q!' to force quit or 'wq' to save and quit"
            else:
                self.running = False
        
        elif cmd == 'q!':
            self.running = False
        
        elif cmd in ('w', 'write'):
            if len(parts) > 1:
                self.save_file(parts[1])
            else:
                self.save_file()
        
        elif cmd == 'wq':
            self.save_file()
            if not self.buffer.modified:  # Only quit if save was successful
                self.running = False
        
        elif cmd in ('o', 'open'):
            if len(parts) > 1:
                self.load_file(parts[1])
            else:
                self.status_bar.message = "Usage: open <filename>"
        
        elif cmd == 'help':
            self.status_bar.message = "Commands: q(uit) w(rite) o(pen) wq q! help | Keys: Ctrl+S=save Ctrl+Q=quit Ctrl+X=command"
        
        else:
            self.status_bar.message = f"Unknown command: {cmd}. Type 'help' for available commands"
    
    def adjust_viewport(self):
        """Adjust viewport to keep cursor visible"""
        rows, cols = self.terminal.size
        text_rows = rows - 2  # Reserve rows for status bar
        
        # Scroll up if cursor is above viewport
        if self.cursor.row < self.viewport_row:
            self.viewport_row = self.cursor.row
        
        # Scroll down if cursor is below viewport
        elif self.cursor.row >= self.viewport_row + text_rows:
            self.viewport_row = self.cursor.row - text_rows + 1
        
        # Ensure viewport doesn't go negative
        self.viewport_row = max(0, self.viewport_row)
    
    def render(self):
        """Render the complete editor interface"""
        rows, cols = self.terminal.size
        
        # Update terminal size if changed
        self.terminal.size = self.terminal.get_terminal_size()
        rows, cols = self.terminal.size
        
        # Adjust viewport to keep cursor visible
        self.adjust_viewport()
        
        # Clear screen and reset cursor
        self.terminal.clear_screen()
        self.terminal.move_cursor(1, 1)
        
        # Render text content
        lines = self.buffer.get_lines()
        text_rows = rows - 1  # Reserve one row for status bar
        
        for screen_row in range(text_rows):
            buffer_row = self.viewport_row + screen_row
            self.terminal.move_cursor(screen_row + 1, 1)
            
            if buffer_row < len(lines):
                line = lines[buffer_row]
                
                # Apply syntax highlighting for Python files
                if (self.status_bar.filename.endswith('.py') or 
                    self.status_bar.filename.endswith('.pyw')):
                    line = self.syntax_highlighter.highlight_line(line)
                
                # Truncate line if it's too long for the screen
                if len(line) > cols:
                    # Account for ANSI escape sequences when truncating
                    display_line = line[:cols-1] + "…"
                else:
                    display_line = line
                
                sys.stdout.write(display_line)
            else:
                # Show tilde for lines beyond buffer (vim style)
                sys.stdout.write('\x1b[90m~\x1b[0m')
            
            # Clear rest of line
            sys.stdout.write('\x1b[K')
        
        # Render status bar
        self.terminal.move_cursor(rows, 1)
        sys.stdout.write('\x1b[7m')  # Reverse video (invert colors)
        status_content = self.status_bar.render(self.terminal, self.cursor, self.buffer)
        sys.stdout.write(status_content[:cols])  # Ensure it fits
        sys.stdout.write('\x1b[0m')  # Reset colors
        
        # Position cursor at the editing location
        screen_row = self.cursor.row - self.viewport_row + 1
        screen_col = self.cursor.col + 1
        
        # Ensure cursor is within screen bounds
        if 1 <= screen_row <= text_rows and 1 <= screen_col <= cols:
            self.terminal.move_cursor(screen_row, screen_col)
            self.terminal.show_cursor()
        else:
            self.terminal.hide_cursor()
        
        sys.stdout.flush()


def run_tests():
    """Run tests for editor components"""
    print("Testing Text Editor Components")
    print("=" * 50)
    
    # Test 1: Text buffer operations
    print("1. Testing TextBuffer...")
    buffer = TextBuffer("Hello\nWorld")
    
    # Test basic operations
    assert buffer.get_text() == "Hello\nWorld"
    assert len(buffer) == 11  # "Hello\nWorld"
    
    # Test insertion
    buffer.insert_char(5, '!')
    assert buffer.get_text() == "Hello!\nWorld"
    
    # Test deletion
    deleted = buffer.delete_char(5)
    assert deleted == '!'
    assert buffer.get_text() == "Hello\nWorld"
    
    # Test line splitting
    lines = buffer.get_lines()
    assert lines == ["Hello", "World"]
    
    print("   ✓ TextBuffer operations work correctly")
    
    # Test 2: Cursor positioning
    print("2. Testing Cursor...")
    cursor = Cursor(buffer)
    
    # Test movement
    cursor.move_down()  # Move to "World" line
    cursor.move_to_line_end()
    assert cursor.row == 1
    assert cursor.col == 5  # Length of "World"
    
    # Test buffer position calculation
    pos = cursor.get_buffer_position()
    assert pos == 11  # End of buffer
    
    cursor.move_up()
    cursor.move_to_line_start()
    assert cursor.row == 0
    assert cursor.col == 0
    
    print("   ✓ Cursor positioning works correctly")
    
    # Test 3: Syntax highlighting
    print("3. Testing SyntaxHighlighter...")
    highlighter = SyntaxHighlighter()
    
    # Test keyword highlighting
    highlighted = highlighter.highlight_line("def hello_world():")
    assert '\x1b[34m' in highlighted  # Should contain blue color code for 'def'
    assert 'hello_world' in highlighted
    
    # Test string highlighting
    highlighted = highlighter.highlight_line('print("Hello, World!")')
    assert '\x1b[32m' in highlighted  # Should contain green color code for string
    
    print("   ✓ Syntax highlighting works correctly")
    
    # Test 4: Status bar
    print("4. Testing StatusBar...")
    status_bar = StatusBar()
    status_bar.filename = "test.py"
    status_bar.message = "Test message"
    
    # Create mock terminal
    class MockTerminal:
        size = (24, 80)
    
    mock_terminal = MockTerminal()
    status_content = status_bar.render(mock_terminal, cursor, buffer)
    
    assert "test.py" in status_content
    assert "1:1" in status_content  # Cursor position
    assert "Test message" in status_content
    
    print("   ✓ Status bar rendering works correctly")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("\nYou can now run the editor with:")
    print("  python myeditor.py [filename]")


def main():
    """Main entry point for the text editor"""
    import sys
    
    # Check if we should run tests
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_tests()
        return
    
    # Show welcome message
    print("╭─────────────────────────────────────────────────╮")
    print("│                MyTextEditor                     │")
    print("│            A Terminal Text Editor               │")
    print("├─────────────────────────────────────────────────┤")
    print("│  Controls:                                      │")
    print("│    Ctrl+S  Save file                           │")
    print("│    Ctrl+Q  Quit (press twice if unsaved)       │")
    print("│    Ctrl+X  Enter command mode                   │")
    print("│                                                 │")
    print("│  Commands (in command mode):                    │")
    print("│    w [file]    Write/save file                  │")
    print("│    o <file>    Open file                        │")
    print("│    q           Quit                             │")
    print("│    q!          Force quit (lose changes)       │")
    print("│    wq          Write and quit                   │")
    print("│    help        Show help                        │")
    print("├─────────────────────────────────────────────────┤")
    print("│  Features:                                      │")
    print("│  • Basic text editing with cursor movement     │")
    print("│  • File operations (open/save)                 │")
    print("│  • Python syntax highlighting                  │")
    print("│  • Modal command system                        │")
    print("│  • Status bar with file info                   │")
    print("╰─────────────────────────────────────────────────╯")
    
    # Get filename from command line
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        print(f"\nOpening file: {filename}")
    else:
        print("\nStarting with empty buffer")
    
    input("\nPress Enter to start the editor...")
    
    # Create and run editor
    editor = TextEditor()
    
    try:
        editor.run(filename)
    except KeyboardInterrupt:
        print("\n\nEditor interrupted by user")
    except Exception as e:
        print(f"\n\nEditor error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nThanks for using MyTextEditor!")


if __name__ == "__main__":
    main()