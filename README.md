# Build Something - Master the Fundamentals

Welcome to **Build Something**, a comprehensive collection of hands-on tutorials where you'll recreate popular tools and systems from scratch. Each project is designed to teach you fundamental programming concepts while building real, working software.

## 🎯 Philosophy

> "What I cannot create, I do not understand." - Richard Feynman

This repository follows the principle of learning by building. Instead of just reading about how systems work, you'll implement them yourself using only basic programming constructs and standard libraries. No external dependencies, no magic frameworks - just pure understanding.

## 📚 Available Projects

### 🔧 System Tools
- **[Build Your Own Git](./git/)** - Version control system with basic branching and merging
- **[Build Your Own Shell](./shell/)** - Command-line interpreter with pipes and redirections
- **[Build Your Own Text Editor](./editor/)** - Terminal-based text editor with syntax highlighting
- **[Build Your Own Command-Line Tools](./cli-tools/)** - Collection of CLI application tutorials
- **[Build Your Own Operating System](./operating-system/)** - OS kernel development from scratch
- **[Build Your Own Docker](./docker/)** - Container runtime and virtualization system

### 🌐 Network & Web
- **[Build Your Own HTTP Server](./http-server/)** - Web server with routing and static file serving
- **[Build Your Own Web Framework](./web-framework/)** - Lightweight framework with templating and middleware
- **[Build Your Own Web Browser](./web-browser/)** - Browser engine implementation
- **[Build Your Own Network Stack](./network/)** - TCP/IP implementation from scratch
- **[Build Your Own Load Balancer](./load-balancer/)** - HTTP load balancer with health checking
- **[Build Your Own BitTorrent Client](./bittorrent/)** - P2P file sharing protocol

### 💾 Data & Storage
- **[Build Your Own Database](./database/)** - Relational database with SQL parsing and B-tree indexing
- **[Build Your Own Key-Value Store](./kv-store/)** - Redis-like in-memory data structure server
- **[Build Your Own Search Engine](./search-engine/)** - Full-text search with indexing and ranking

### ⚡ Languages & Compilers
- **[Build Your Own Interpreter](./interpreter/)** - Language interpreter with lexer, parser, and evaluator
- **[Build Your Own Compiler](./compiler/)** - Simple compiler targeting assembly or bytecode
- **[Build Your Own Programming Language](./programming-language/)** - Complete language implementation
- **[Build Your Own Regex Engine](./regex/)** - Regular expression matching engine
- **[Build Your Own Template Engine](./template-engine/)** - Text templating system

### 🔄 Distributed Systems & Blockchain
- **[Build Your Own Message Queue](./message-queue/)** - Pub/sub messaging system
- **[Build Your Own Blockchain](./blockchain/)** - Cryptocurrency and blockchain implementation

### 🎮 Graphics & Games
- **[Build Your Own 3D Renderer](./3d-renderer/)** - Ray tracing and rasterization tutorials
- **[Build Your Own Game](./game/)** - Game development from scratch
- **[Build Your Own Physics Engine](./physics/)** - 2D/3D physics simulation
- **[Build Your Own Voxel Engine](./voxel-engine/)** - Minecraft-style world generation

### 🤖 AI & Machine Learning
- **[Build Your Own Neural Network](./neural-network/)** - Deep learning from first principles
- **[Build Your Own Bot](./bot/)** - Chatbots, trading bots, and automation
- **[Build Your Own Visual Recognition System](./visual-recognition/)** - Computer vision and image processing

### 🔮 Advanced Systems
- **[Build Your Own Emulator](./emulator/)** - CPU emulation and virtual machines
- **[Build Your Own Augmented Reality](./augmented-reality/)** - AR development tutorials
- **[Build Your Own Frontend Framework](./frontend/)** - React/Vue-like framework implementation

### 📚 Additional Projects & Resources

For more specialized tutorials and language-specific implementations, explore these comprehensive resources:

#### Systems & Infrastructure
- **[Build Your Own Docker](./docker/)** - Container runtime and virtualization
- **[Build Your Own Network Stack](./network/)** - TCP/IP implementation from scratch
- **[Build Your Own BitTorrent Client](./bittorrent/)** - P2P file sharing protocol

#### Specialized Engines
- **[Build Your Own Regex Engine](./regex/)** - Pattern matching and finite automata
- **[Build Your Own Search Engine](./search-engine/)** - Information retrieval and indexing
- **[Build Your Own Template Engine](./template-engine/)** - Text templating systems
- **[Build Your Own Voxel Engine](./voxel-engine/)** - Minecraft-style world generation

#### Machine Learning & Vision
- **[Build Your Own Visual Recognition System](./visual-recognition/)** - Computer vision and image processing

#### Comprehensive Tutorial Collections
Each category contains extensive tutorials covering multiple programming languages including C, C++, Python, JavaScript, Go, Rust, Java, C#, and many more. From beginner-friendly introductions to advanced implementations, these tutorials provide complete learning paths for mastering each technology from first principles.

## 🚀 Getting Started

1. **Choose a Project**: Pick any project that interests you from the list above
2. **Read the Guide**: Each project has a detailed README with step-by-step instructions  
3. **Start Building**: Follow along with the tutorial, implementing features incrementally
4. **Test as You Go**: Each step includes tests to verify your implementation
5. **Extend and Explore**: Add your own features once you've mastered the basics

## 📖 How to Use This Repository

Each project directory contains:
- `README.md` - Complete tutorial with theory and implementation steps
- `starter/` - Basic project structure to get you started
- `examples/` - Reference implementations and test cases
- `tests/` - Automated tests to verify your implementation
- `docs/` - Additional resources and deep-dive explanations

## 🎓 Learning Path Recommendations

### 🌱 Beginner Path
**Foundation**: Start with Shell → Text Editor → HTTP Server
**Next Steps**: Try Command-Line Tools → Simple Game → Bot

### 🚀 Intermediate Path  
**Core Systems**: Database → Interpreter → Web Framework → Regex Engine
**Networking**: Network Stack → BitTorrent Client → Load Balancer
**Graphics**: 3D Renderer → Physics Engine → Voxel Engine

### 🧠 Advanced Path
**Languages**: Compiler → Programming Language → Template Engine
**Systems**: Operating System → Emulator → Docker → Message Queue
**AI/ML**: Neural Network → Visual Recognition → Advanced Bot

### 🎯 Specialized Tracks
**Web Developer**: HTTP Server → Web Framework → Frontend Framework → Web Browser
**Game Developer**: Game → Physics Engine → 3D Renderer → Voxel Engine
**Systems Engineer**: Shell → Operating System → Network Stack → Docker
**AI Engineer**: Neural Network → Bot → Visual Recognition → Search Engine
**Blockchain Developer**: Database → Blockchain → P2P BitTorrent → Distributed Systems

## 🧪 Testing

All implemented projects include comprehensive test suites to verify functionality:

### Run All Tests
```bash
python3 run_all_tests.py
```

### Individual Component Tests
```bash
# Database tests
python3 database/starter/mydatabase.py

# Text Editor tests  
python3 editor/starter/myeditor.py
# OR
python3 -c "import sys; sys.path.append('editor/starter'); from myeditor import run_tests; run_tests()"

# Git tests
python3 git/tests/test_mygit.py

# HTTP Server tests
python3 http-server/starter/server.py --test

# Shell tests
python3 shell/starter/myshell.py --test
```

### Test Status
✅ **All 5 implemented components pass their tests:**
- **Database**: Storage engine, B-tree indexing, SQL parsing (4/4 tests)
- **Text Editor**: TextBuffer, Cursor, Syntax highlighting, Status bar (4/4 tests)  
- **Git**: Init, add, commit, status, log, history (7/7 tests)
- **HTTP Server**: Request parsing, routing, static files, integration (5/5 tests)
- **Shell**: Lexer, parser, built-ins, variables, execution (5/5 tests)

## 🛠️ Prerequisites

- Basic programming knowledge in your chosen language (examples provided in Python, Go, and C)
- Understanding of fundamental data structures (arrays, linked lists, hash tables)
- Familiarity with command-line tools and basic system concepts

## 🤝 Contributing

This is an educational resource! Contributions are welcome:
- Fix bugs in tutorials or example code
- Add new project ideas
- Improve explanations and documentation
- Translate tutorials to other programming languages

## 📜 License

This project is licensed under the MIT License - see each project directory for specific licensing information.

---

**Ready to build something amazing?** Pick a project and start coding! Remember: the goal isn't just to make it work, but to understand *why* it works.