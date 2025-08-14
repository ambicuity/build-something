# Build Your Own Text Editor

Create a terminal-based text editor from scratch and understand how text editing applications work. You'll implement cursor movement, text insertion/deletion, file operations, and basic syntax highlighting.

## 🎯 What You'll Learn

- Terminal control and escape sequences
- Buffer management for efficient text editing
- Cursor positioning and viewport management
- File I/O for loading and saving documents
- Basic syntax highlighting and text processing
- Command parsing and modal editing concepts

## 📋 Prerequisites

- Understanding of terminal/console programming
- Knowledge of string manipulation and character encoding
- Basic familiarity with file operations
- Understanding of data structures (arrays, trees)

## 🏗️ Architecture Overview

Our text editor consists of these components:

1. **Terminal Interface**: Raw terminal control and input handling
2. **Buffer Manager**: Efficient text storage and manipulation
3. **Cursor Manager**: Tracks cursor position and handles movement
4. **Viewport**: Manages what portion of text is visible
5. **Command Parser**: Handles user commands and key bindings
6. **File Manager**: Loading, saving, and file operations

```
Terminal Input → Key Handler → Command Parser → Buffer Operations
      ↑                                              ↓
  Display ← Renderer ← Viewport Manager ← Cursor Manager
```

## 🚀 Implementation Steps

### Step 1: Terminal Control and Raw Mode

Start by implementing basic terminal control to capture individual keystrokes.

**Theory**: Text editors need raw access to terminal input to capture individual keystrokes, arrow keys, and control sequences without line buffering.

```python
import sys
import os
import termios
import tty
import select
from typing import Optional, List, Tuple
from enum import Enum

class Key(Enum):
    """Special key codes"""
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
        
        # Hide cursor initially
        sys.stdout.write('\x1b[?25l')
        sys.stdout.flush()
    
    def exit_raw_mode(self):
        """Restore original terminal settings"""
        if self.original_settings and self.raw_mode:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_settings)
            self.raw_mode = False
            
            # Show cursor
            sys.stdout.write('\x1b[?25h')
            sys.stdout.flush()
    
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
        sys.stdout.flush()
    
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
        """Read a single key press"""
        if not self.raw_mode:
            return None
        
        # Check if input is available
        if not select.select([sys.stdin], [], [], 0.1)[0]:
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
                            # Page Up
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                sys.stdin.read(1)  # consume '~'
                            return Key.PAGE_UP.value
                        elif seq2 == '6':
                            # Page Down
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                sys.stdin.read(1)  # consume '~'
                            return Key.PAGE_DOWN.value
                        elif seq2 == 'H':
                            return Key.HOME.value
                        elif seq2 == 'F':
                            return Key.END.value
        
        return char

# Test terminal control
def test_terminal():
    """Test basic terminal functionality"""
    terminal = Terminal()
    
    try:
        terminal.enter_raw_mode()
        terminal.clear_screen()
        
        print("Terminal Test Mode")
        print("Press any key (Ctrl+C to exit):")
        terminal.move_cursor(3, 1)
        terminal.show_cursor()
        
        while True:
            key = terminal.read_key()
            if key:
                if ord(key) == Key.CTRL_C.value:
                    break
                
                terminal.move_cursor(4, 1)
                sys.stdout.write(f"Key pressed: {repr(key)} (code: {ord(key) if len(key) == 1 else key})")
                sys.stdout.write('\x1b[K')  # Clear rest of line
                sys.stdout.flush()
    
    finally:
        terminal.exit_raw_mode()
        print("\nExited raw mode")

if __name__ == "__main__":
    test_terminal()
```

### Step 2: Text Buffer Management

Implement efficient text storage and manipulation.

**Theory**: Text editors use various data structures for storing text. We'll use a gap buffer, which is efficient for insertions and deletions at the cursor position.

```python
class TextBuffer:
    """Efficient text buffer using gap buffer data structure"""
    
    def __init__(self, initial_text: str = "", gap_size: int = 1024):
        self.gap_size = gap_size
        self.text = list(initial_text) + [None] * gap_size
        self.gap_start = len(initial_text)
        self.gap_end = len(self.text)
        self.modified = False
    
    def __len__(self) -> int:
        """Return logical length of text (excluding gap)"""
        return len(self.text) - (self.gap_end - self.gap_start)
    
    def get_text(self) -> str:
        """Get the complete text as string"""
        before_gap = self.text[:self.gap_start]
        after_gap = self.text[self.gap_end:]
        return ''.join(filter(None, before_gap + after_gap))
    
    def get_lines(self) -> List[str]:
        """Get text as list of lines"""
        text = self.get_text()
        return text.split('\n')
    
    def move_gap(self, position: int):
        """Move gap to specified position"""
        if position < self.gap_start:
            # Move gap left
            chars_to_move = self.gap_start - position
            for i in range(chars_to_move):
                self.gap_end -= 1
                self.gap_start -= 1
                self.text[self.gap_end] = self.text[self.gap_start]
                self.text[self.gap_start] = None
        elif position > self.gap_start:
            # Move gap right
            chars_to_move = position - self.gap_start
            for i in range(chars_to_move):
                self.text[self.gap_start] = self.text[self.gap_end]
                self.text[self.gap_end] = None
                self.gap_start += 1
                self.gap_end += 1
    
    def _expand_gap(self):
        """Expand gap when it becomes too small"""
        old_gap_size = self.gap_end - self.gap_start
        if old_gap_size < 10:
            # Insert more space at gap
            new_space = [None] * self.gap_size
            self.text = self.text[:self.gap_start] + new_space + self.text[self.gap_start:]
            self.gap_end = self.gap_start + len(new_space)
    
    def insert_char(self, position: int, char: str):
        """Insert character at position"""
        self.move_gap(position)
        
        if self.gap_start >= self.gap_end:
            self._expand_gap()
        
        self.text[self.gap_start] = char
        self.gap_start += 1
        self.modified = True
    
    def delete_char(self, position: int) -> Optional[str]:
        """Delete character at position"""
        if position < 0 or position >= len(self):
            return None
        
        self.move_gap(position + 1)
        
        if self.gap_start > 0:
            self.gap_start -= 1
            deleted_char = self.text[self.gap_start]
            self.text[self.gap_start] = None
            self.modified = True
            return deleted_char
        
        return None
    
    def get_char_at(self, position: int) -> Optional[str]:
        """Get character at position"""
        if position < 0 or position >= len(self):
            return None
        
        if position < self.gap_start:
            return self.text[position]
        else:
            gap_size = self.gap_end - self.gap_start
            return self.text[position + gap_size]
    
    def insert_text(self, position: int, text: str):
        """Insert multiple characters at position"""
        for i, char in enumerate(text):
            self.insert_char(position + i, char)
    
    def delete_range(self, start: int, end: int) -> str:
        """Delete range of characters"""
        deleted = ""
        for pos in range(end - 1, start - 1, -1):  # Delete backwards
            char = self.delete_char(pos)
            if char:
                deleted = char + deleted
        return deleted

class Cursor:
    """Manages cursor position in the text buffer"""
    
    def __init__(self, buffer: TextBuffer):
        self.buffer = buffer
        self.row = 0
        self.col = 0
        self._desired_col = 0  # For vertical movement
    
    def get_buffer_position(self) -> int:
        """Convert row/col to buffer position"""
        lines = self.buffer.get_lines()
        position = 0
        
        for i in range(min(self.row, len(lines) - 1)):
            position += len(lines[i]) + 1  # +1 for newline
        
        if self.row < len(lines):
            position += min(self.col, len(lines[self.row]))
        
        return position
    
    def set_position_from_buffer(self, buffer_pos: int):
        """Set cursor position from buffer position"""
        lines = self.buffer.get_lines()
        current_pos = 0
        
        for row, line in enumerate(lines):
            line_end = current_pos + len(line)
            
            if buffer_pos <= line_end:
                self.row = row
                self.col = buffer_pos - current_pos
                self._desired_col = self.col
                return
            
            current_pos = line_end + 1  # +1 for newline
        
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
        """Move cursor to start of line"""
        self.col = 0
        self._desired_col = 0
    
    def move_to_line_end(self):
        """Move cursor to end of line"""
        lines = self.buffer.get_lines()
        if self.row < len(lines):
            self.col = len(lines[self.row])
            self._desired_col = self.col

# Test buffer and cursor
def test_buffer():
    """Test text buffer and cursor"""
    buffer = TextBuffer("Hello\nWorld\n!")
    cursor = Cursor(buffer)
    
    print("Initial text:")
    print(repr(buffer.get_text()))
    
    # Test cursor movement
    cursor.move_down()
    cursor.move_to_line_end()
    print(f"Cursor after move: row={cursor.row}, col={cursor.col}")
    
    # Test insertion
    pos = cursor.get_buffer_position()
    buffer.insert_char(pos, 'd')
    print("After inserting 'd':")
    print(repr(buffer.get_text()))
    
    # Test deletion
    buffer.delete_char(pos)
    print("After deleting character:")
    print(repr(buffer.get_text()))
    
    print("Buffer test completed!")

if __name__ == "__main__":
    test_buffer()
```

### Step 3: Complete Text Editor Implementation

Put it all together into a working text editor.

```python
import os
from typing import Optional, List

class StatusBar:
    """Status bar for showing editor information"""
    
    def __init__(self):
        self.message = ""
        self.filename = "untitled"
        self.modified = False
    
    def render(self, terminal: Terminal, cursor: Cursor, buffer: TextBuffer) -> str:
        """Render status bar"""
        rows, cols = terminal.size
        
        # Left side: filename and modified indicator
        left = f" {self.filename}" + ("*" if buffer.modified else "")
        
        # Right side: cursor position and buffer info
        lines = buffer.get_lines()
        right = f" {cursor.row + 1}:{cursor.col + 1} | {len(lines)} lines "
        
        # Center: message
        available_space = cols - len(left) - len(right)
        if self.message and available_space > 0:
            center = f" {self.message[:available_space-2]} "
        else:
            center = ""
        
        # Fill remaining space
        total_used = len(left) + len(center) + len(right)
        padding = " " * max(0, cols - total_used)
        
        return left + center + padding + right

class SyntaxHighlighter:
    """Basic syntax highlighting"""
    
    KEYWORDS = {
        'def', 'class', 'if', 'else', 'elif', 'while', 'for', 'in', 'return',
        'import', 'from', 'try', 'except', 'finally', 'with', 'as', 'pass',
        'break', 'continue', 'True', 'False', 'None', 'and', 'or', 'not'
    }
    
    def highlight_line(self, line: str) -> str:
        """Apply basic syntax highlighting to a line"""
        # This is a very basic implementation
        # In a real editor, you'd use proper tokenization
        
        result = ""
        i = 0
        while i < len(line):
            char = line[i]
            
            # String literals
            if char in ['"', "'"]:
                quote = char
                result += f"\x1b[32m{char}"  # Green
                i += 1
                while i < len(line) and line[i] != quote:
                    if line[i] == '\\' and i + 1 < len(line):
                        result += line[i:i+2]
                        i += 2
                    else:
                        result += line[i]
                        i += 1
                if i < len(line):
                    result += f"{line[i]}\x1b[0m"  # Reset color
                i += 1
                continue
            
            # Comments
            if char == '#':
                result += f"\x1b[90m{line[i:]}\x1b[0m"  # Gray
                break
            
            # Keywords (very basic check)
            if char.isalpha() or char == '_':
                word_start = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                word = line[word_start:i]
                
                if word in self.KEYWORDS:
                    result += f"\x1b[34m{word}\x1b[0m"  # Blue
                else:
                    result += word
                continue
            
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
    
    def run(self, filename: Optional[str] = None):
        """Start the text editor"""
        try:
            self.terminal.enter_raw_mode()
            
            if filename and os.path.exists(filename):
                self.load_file(filename)
                self.status_bar.filename = filename
            
            self.running = True
            self.render()
            
            while self.running:
                key = self.terminal.read_key()
                if key:
                    self.handle_key(key)
                    self.render()
        
        except KeyboardInterrupt:
            pass
        finally:
            self.terminal.exit_raw_mode()
            self.terminal.clear_screen()
    
    def load_file(self, filename: str):
        """Load file into buffer"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                self.buffer = TextBuffer(content)
                self.cursor = Cursor(self.buffer)
                self.buffer.modified = False
                self.status_bar.message = f"Loaded {filename}"
        except Exception as e:
            self.status_bar.message = f"Error loading {filename}: {e}"
    
    def save_file(self, filename: Optional[str] = None):
        """Save buffer to file"""
        if filename:
            self.status_bar.filename = filename
        
        try:
            with open(self.status_bar.filename, 'w', encoding='utf-8') as f:
                f.write(self.buffer.get_text())
                self.buffer.modified = False
                self.status_bar.message = f"Saved {self.status_bar.filename}"
        except Exception as e:
            self.status_bar.message = f"Error saving: {e}"
    
    def handle_key(self, key: str):
        """Handle key press"""
        if self.command_mode:
            self.handle_command_key(key)
            return
        
        # Control keys
        if len(key) == 1:
            code = ord(key)
            
            if code == Key.CTRL_Q.value:
                if self.buffer.modified:
                    self.status_bar.message = "Unsaved changes! Press Ctrl+Q again to quit"
                    # Simple confirmation - in real editor, you'd track this properly
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
                    self.cursor.move_left()
                    pos = self.cursor.get_buffer_position()
                    self.buffer.delete_char(pos)
                return
            elif code == Key.ENTER.value:
                pos = self.cursor.get_buffer_position()
                self.buffer.insert_char(pos, '\n')
                self.cursor.move_right()
                return
            elif code == Key.TAB.value:
                pos = self.cursor.get_buffer_position()
                self.buffer.insert_text(pos, "    ")  # 4 spaces
                for _ in range(4):
                    self.cursor.move_right()
                return
        
        # Special keys
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
        elif len(key) == 1 and ord(key) >= 32:  # Printable characters
            pos = self.cursor.get_buffer_position()
            self.buffer.insert_char(pos, key)
            self.cursor.move_right()
    
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
                self.status_bar.message = ""
                return
            elif code == Key.BACKSPACE.value:
                if self.command_buffer:
                    self.command_buffer = self.command_buffer[:-1]
                self.status_bar.message = f"Command: {self.command_buffer}"
                return
            elif code >= 32:  # Printable character
                self.command_buffer += key
                self.status_bar.message = f"Command: {self.command_buffer}"
    
    def execute_command(self, command: str):
        """Execute editor command"""
        parts = command.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == 'q' or cmd == 'quit':
            if self.buffer.modified:
                self.status_bar.message = "Unsaved changes! Use 'q!' to force quit"
            else:
                self.running = False
        elif cmd == 'q!':
            self.running = False
        elif cmd == 'w' or cmd == 'write':
            if len(parts) > 1:
                self.save_file(parts[1])
            else:
                self.save_file()
        elif cmd == 'wq':
            self.save_file()
            self.running = False
        elif cmd == 'o' or cmd == 'open':
            if len(parts) > 1:
                self.load_file(parts[1])
        elif cmd == 'help':
            self.status_bar.message = "Commands: q(uit), w(rite), o(pen), wq, q!, help. Ctrl+S=save, Ctrl+Q=quit, Ctrl+X=command"
        else:
            self.status_bar.message = f"Unknown command: {cmd}"
    
    def render(self):
        """Render the editor"""
        rows, cols = self.terminal.size
        
        # Clear screen
        self.terminal.clear_screen()
        
        # Ensure cursor is visible in viewport
        self.adjust_viewport()
        
        # Render text lines
        lines = self.buffer.get_lines()
        text_rows = rows - 2  # Reserve space for status bar and message
        
        for screen_row in range(text_rows):
            buffer_row = self.viewport_row + screen_row
            
            self.terminal.move_cursor(screen_row + 1, 1)
            
            if buffer_row < len(lines):
                line = lines[buffer_row]
                
                # Apply syntax highlighting for Python files
                if self.status_bar.filename.endswith('.py'):
                    line = self.syntax_highlighter.highlight_line(line)
                
                # Truncate line if too long
                if len(line) > cols:
                    line = line[:cols-1] + "…"
                
                sys.stdout.write(line)
            else:
                # Show tilde for empty lines (like vim)
                sys.stdout.write("~")
            
            # Clear rest of line
            sys.stdout.write('\x1b[K')
        
        # Render status bar
        self.terminal.move_cursor(rows - 1, 1)
        sys.stdout.write('\x1b[7m')  # Reverse video
        status_text = self.status_bar.render(self.terminal, self.cursor, self.buffer)
        sys.stdout.write(status_text)
        sys.stdout.write('\x1b[0m')  # Reset attributes
        
        # Position cursor
        screen_row = self.cursor.row - self.viewport_row + 1
        screen_col = self.cursor.col + 1
        self.terminal.move_cursor(screen_row, screen_col)
        self.terminal.show_cursor()
        
        sys.stdout.flush()
    
    def adjust_viewport(self):
        """Adjust viewport to keep cursor visible"""
        rows, cols = self.terminal.size
        text_rows = rows - 2
        
        # Scroll up if cursor is above viewport
        if self.cursor.row < self.viewport_row:
            self.viewport_row = self.cursor.row
        
        # Scroll down if cursor is below viewport
        if self.cursor.row >= self.viewport_row + text_rows:
            self.viewport_row = self.cursor.row - text_rows + 1

def main():
    """Main entry point"""
    import sys
    
    editor = TextEditor()
    
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    print("MyTextEditor - A simple text editor")
    print("Controls: Ctrl+S=Save, Ctrl+Q=Quit, Ctrl+X=Commands")
    print("Commands: q(uit), w(rite), o(pen) filename, wq, help")
    
    if filename:
        print(f"Opening: {filename}")
    else:
        print("Starting with empty buffer")
    
    input("Press Enter to start...")
    
    editor.run(filename)
    
    print("\nThanks for using MyTextEditor!")

if __name__ == "__main__":
    main()
```

## 🧪 Testing Your Implementation

Create tests to verify the text editor components:

```python
def test_editor_components():
    """Test editor components"""
    print("Testing Text Editor Components")
    print("=" * 40)
    
    # Test 1: Text buffer
    print("1. Testing text buffer...")
    buffer = TextBuffer("Hello\nWorld")
    assert buffer.get_text() == "Hello\nWorld"
    
    buffer.insert_char(5, '!')
    assert buffer.get_text() == "Hello!\nWorld"
    
    deleted = buffer.delete_char(5)
    assert deleted == '!'
    assert buffer.get_text() == "Hello\nWorld"
    
    print("   ✓ Text buffer works")
    
    # Test 2: Cursor movement
    print("2. Testing cursor...")
    cursor = Cursor(buffer)
    
    cursor.move_down()
    cursor.move_to_line_end()
    assert cursor.row == 1
    assert cursor.col == 5  # "World" length
    
    cursor.move_up()
    assert cursor.row == 0
    assert cursor.col == 5  # "Hello" length
    
    print("   ✓ Cursor movement works")
    
    # Test 3: Syntax highlighter
    print("3. Testing syntax highlighter...")
    highlighter = SyntaxHighlighter()
    
    highlighted = highlighter.highlight_line("def hello():")
    assert '\x1b[34m' in highlighted  # Blue color for 'def'
    
    print("   ✓ Syntax highlighting works")
    
    print("\n" + "=" * 40)
    print("🎉 All component tests passed!")

if __name__ == "__main__":
    test_editor_components()
```

## 🎯 Challenges to Extend Your Implementation

1. **Search and Replace**: Add text search and replacement functionality
2. **Multiple Buffers**: Support editing multiple files simultaneously
3. **Undo/Redo**: Implement operation history with undo/redo
4. **Advanced Syntax Highlighting**: Add proper tokenization and language support
5. **Configuration**: Add customizable key bindings and settings
6. **Plugin System**: Support for extending editor functionality
7. **Mouse Support**: Handle mouse clicks and selection
8. **Split Windows**: Allow viewing multiple files at once

## 📚 Key Concepts Learned

- **Terminal Programming**: Raw mode, escape sequences, cursor control
- **Text Data Structures**: Gap buffers for efficient editing
- **Viewport Management**: Scrolling and screen updates
- **Event Handling**: Key processing and command dispatch
- **File I/O**: Loading and saving documents
- **Syntax Processing**: Basic tokenization and highlighting

---

**Congratulations!** You've built a functional text editor that demonstrates the core concepts used in all text editing applications.