# Build Your Own Command-Line Tools

Master the art of command-line programming by building useful CLI applications. Learn argument parsing, file processing, and creating tools that integrate seamlessly with the shell environment.

## 🎯 What You'll Learn

- Command-line interface design and user experience
- Argument parsing and flag handling
- File and stream processing
- Cross-platform development considerations
- Terminal output formatting and colors
- Error handling and exit codes

## 🚀 Quick Start

```bash
# Navigate to the starter directory
cd cli-tools/starter

# Run tests to verify everything works
python3 cli_tools.py --test

# List available tools
python3 cli_tools.py --list

# Use individual tools
python3 cli_tools.py myecho "Hello World"
python3 cli_tools.py myls -l -c
python3 cli_tools.py wc filename.txt
```

## 🛠️ Implemented Tools

Our implementation includes 6 essential command-line tools built from scratch:

### 1. **myecho** - Enhanced Echo Command
```bash
python3 cli_tools.py myecho "Hello World"
python3 cli_tools.py myecho -c green -b "Colored bold text"
python3 cli_tools.py myecho -e "Line 1\\nLine 2"  # Interpret escapes
python3 cli_tools.py myecho -n "No newline"       # No trailing newline
```

**Features:**
- Color output (red, green, blue, yellow)
- Bold text formatting
- Backslash escape interpretation
- No-newline option

### 2. **myls** - Directory Listing
```bash
python3 cli_tools.py myls                    # Basic listing
python3 cli_tools.py myls -l                 # Long format
python3 cli_tools.py myls -a                 # Show hidden files
python3 cli_tools.py myls -l -c              # Long format with colors
python3 cli_tools.py myls -t -r              # Sort by time, reverse
python3 cli_tools.py myls -H                 # Human readable sizes
```

**Features:**
- Long format with permissions, size, date
- Color coding by file type
- Human-readable file sizes
- Hidden file display
- Time-based sorting

### 3. **wc** - Word Counter
```bash
python3 cli_tools.py wc filename.txt         # Count lines, words, chars
python3 cli_tools.py wc -l filename.txt      # Lines only
python3 cli_tools.py wc -w filename.txt      # Words only
python3 cli_tools.py wc -c filename.txt      # Characters only
python3 cli_tools.py wc file1.txt file2.txt # Multiple files
```

**Features:**
- Line, word, and character counting
- Multiple file processing
- Total summaries
- Individual count options

### 4. **mytail** - File Tail Display
```bash
python3 cli_tools.py mytail filename.txt     # Last 10 lines
python3 cli_tools.py mytail -n 5 file.txt    # Last 5 lines
python3 cli_tools.py mytail file1.txt file2.txt # Multiple files
```

**Features:**
- Configurable line count
- Multiple file support
- Stdin support
- File headers for multiple files

### 5. **mygrep** - Pattern Search
```bash
python3 cli_tools.py mygrep pattern file.txt      # Basic search
python3 cli_tools.py mygrep -i pattern file.txt   # Case insensitive
python3 cli_tools.py mygrep -n pattern file.txt   # Show line numbers
python3 cli_tools.py mygrep -v pattern file.txt   # Invert match
python3 cli_tools.py mygrep -c pattern file.txt   # Count matches
python3 cli_tools.py mygrep -r "pa.*ern" file.txt # Regex mode
```

**Features:**
- Case-sensitive and insensitive search
- Line number display
- Inverted matching
- Match counting
- Regular expression support
- Multiple file search

### 6. **mycat** - File Display
```bash
python3 cli_tools.py mycat filename.txt      # Display file
python3 cli_tools.py mycat -n filename.txt   # With line numbers
python3 cli_tools.py mycat -b filename.txt   # Number non-blank lines
python3 cli_tools.py mycat -s filename.txt   # Squeeze blank lines
```

**Features:**
- File content display
- Line numbering options
- Blank line handling
- Multiple file support

## 📚 Tutorials by Language

### Go
- **[Visualize your local git contributions with Go](https://github.com/IonicaBizau/git-stats)** - Git statistics visualization
- **[Build a command line app with Go: lolcat](https://flaviocopes.com/go-tutorial-lolcat/)** - Colorful text output tool
- **[Building a cli command with Go: cowsay](https://medium.com/@kris-nova/building-a-cli-command-with-go-cowsay-8b96ca8e9e70)** - ASCII art generator
- **[Go CLI tutorial: fortune clone](https://blog.rapid7.com/2016/08/04/build-a-simple-cli-tool-with-golang/)** - Random quote generator

### Node.js/JavaScript
- **[Create a CLI tool in Javascript](https://blog.npmjs.org/post/118810260230/building-a-simple-command-line-tool-with-npm)** - NPM package creation

### Rust
- **[Command line apps in Rust](https://rust-cli.github.io/book/index.html)** - Comprehensive Rust CLI guide
- **[Writing a Command Line Tool in Rust](https://mattgathu.dev/2017/08/29/writing-cli-app-rust.html)** - Practical Rust CLI tutorial

### Nim
- **[Writing a stow alternative to manage dotfiles](https://xmonader.github.io/nim-days/day04_stow.html)** - Dotfile management tool

### Zig
- **[Build Your Own CLI App in Zig from Scratch](https://dev.to/williambanfield/build-your-own-cli-app-in-zig-from-scratch-3g2m)** - Modern systems language CLI

## 🏗️ Project Ideas

### Beginner Projects
1. **Echo Tool** - Simple text output with formatting options
2. **File Counter** - Count lines, words, and characters in files
3. **Directory Lister** - Enhanced `ls` with custom formatting

### Intermediate Projects
1. **Log Parser** - Extract and analyze log file data
2. **File Organizer** - Automatically sort files by type/date
3. **Todo Manager** - Command-line task management system

### Advanced Projects
1. **Git Helper** - Custom git commands and workflow automation
2. **System Monitor** - Real-time system resource display
3. **Build Tool** - Project-specific build automation

## 🛠️ Common CLI Tool Types

### File Processing Tools
- **Text Processors**: grep, sed, awk alternatives
- **File Converters**: Format transformation utilities
- **Archive Tools**: Compression and extraction utilities
- **Backup Tools**: Automated backup solutions

### Development Tools
- **Code Formatters**: Language-specific formatting tools
- **Linters**: Code quality and style checkers
- **Build Systems**: Project compilation and packaging
- **Testing Tools**: Test runners and assertion libraries

### System Administration
- **Process Managers**: Service control and monitoring
- **Log Analyzers**: System log processing and alerting
- **Configuration Tools**: System setup and management
- **Network Tools**: Connection testing and monitoring

### Productivity Tools
- **Task Managers**: Todo lists and project tracking
- **Time Trackers**: Work time monitoring and reporting
- **Note Taking**: Command-line knowledge management
- **Calculators**: Mathematical and unit conversion tools

## 🧪 Key Concepts

### Interface Design
- **Subcommands**: git-style command hierarchies
- **Flags and Options**: Short (-v) and long (--verbose) options
- **Arguments**: Positional and optional parameters
- **Help Systems**: Usage information and examples

### Input/Output
- **Stream Processing**: stdin, stdout, stderr handling
- **File Operations**: Reading, writing, and modifying files
- **Piping Support**: Unix pipe compatibility
- **Output Formatting**: Tables, JSON, and colored output

### Error Handling
- **Exit Codes**: Standard success/failure indicators
- **Error Messages**: Clear and actionable feedback
- **Validation**: Input sanitization and verification
- **Graceful Degradation**: Fallback behavior for edge cases

### Performance
- **Memory Management**: Efficient resource usage
- **Large File Handling**: Stream processing for big data
- **Concurrency**: Parallel processing when beneficial
- **Caching**: Avoiding redundant computations

## 🎨 User Experience

### Documentation
- **Man Pages**: Traditional Unix documentation
- **Built-in Help**: --help flag implementation
- **Examples**: Common usage patterns
- **Tutorials**: Getting started guides

### Accessibility
- **Color Blindness**: Alternative visual indicators
- **Screen Readers**: Text-based output compatibility
- **Internationalization**: Multi-language support
- **Terminal Compatibility**: Wide terminal support

### Integration
- **Shell Completion**: Tab completion support
- **Configuration Files**: User preferences and settings
- **Environment Variables**: System integration
- **Exit Status**: Shell scripting compatibility

## 📦 Distribution & Packaging

### Language-Specific
- **Go**: Single binary distribution
- **Rust**: Cargo packaging and crates.io
- **Node.js**: NPM package management
- **Python**: PyPI and pip installation

### System Integration
- **Package Managers**: apt, brew, chocolatey support
- **Container Images**: Docker containerization
- **Snap Packages**: Universal Linux packages
- **Windows Installer**: MSI/executable distribution

## 🔗 Additional Resources

- [Command Line Interface Guidelines](https://clig.dev/) - Modern CLI design principles
- [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line) - Command-line mastery guide
- [CLI Style Guide](https://devcenter.heroku.com/articles/cli-style-guide) - Heroku's CLI design principles
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) - Best practices for CLI tools

---

**Ready to build?** Start with a simple file processor and evolve into powerful command-line applications!