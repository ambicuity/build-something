# Build Your Own Template Engine

Create text templating systems for generating dynamic content. Learn parsing, variable substitution, control structures, and template inheritance.

## 🎯 What You'll Learn

- Template syntax design and parsing
- Variable interpolation and escaping
- Control structures (loops, conditionals)
- Template filters and transformations
- Context management and scoping
- Security considerations and safe rendering

## 🚀 Quick Start

```bash
# Navigate to the starter directory
cd template-engine/starter

# Run tests to verify everything works
python3 template_engine.py --test

# Use interactive mode to experiment
python3 template_engine.py --interactive

# Use in code
python3 -c "
from template_engine import TemplateEngine
engine = TemplateEngine()
result = engine.render_string('Hello {{ name }}!', {'name': 'World'})
print(result)
"
```

## 🛠️ Implementation Features

Our template engine implements a complete text processing system with:

### Core Features
- **Variable Interpolation**: `{{ variable }}`  
- **Filters**: `{{ variable | filter }}` with chainable filters
- **Control Structures**: `{% if %}`, `{% for %}`, `{% while %}`
- **Comments**: `{# This is a comment #}`
- **Dot Notation**: `{{ user.name }}`, `{{ forloop.counter }}`
- **Safe Rendering**: Automatic HTML escaping and error handling

### Built-in Filters
- `upper`, `lower`, `title` - Text transformation
- `escape` - HTML escaping for security
- `length` - Get length of strings/lists
- `default('fallback')` - Default values for undefined variables
- `join('separator')` - Join lists with separator
- `first`, `last` - Get first/last elements
- `reverse`, `sort` - List manipulation

### Control Structures

#### If Statements
```django
{% if user.logged_in %}
    Welcome back, {{ user.name }}!
{% else %}
    Please log in.
{% endif %}
```

#### For Loops
```django
{% for item in items %}
    {{ forloop.counter }}: {{ item }}
    {% if not forloop.last %}, {% endif %}
{% endfor %}
```

#### Nested Structures
```django
{% for category in categories %}
    <h2>{{ category.name }}</h2>
    {% for product in category.products %}
        {% if product.in_stock %}
            <p>{{ product.name }}: ${{ product.price }}</p>
        {% endif %}
    {% endfor %}
{% endfor %}
```

### Advanced Features

#### Complex Expressions
```django
{{ items | length > 0 }}
{{ price | default(0) | format_currency }}
{{ users | first.name | title }}
```

#### Loop Variables
```django
{% for item in items %}
    Item {{ forloop.counter }}: {{ item }}
    {% if forloop.first %}(First){% endif %}
    {% if forloop.last %}(Last){% endif %}
{% endfor %}
```

## 🏗️ Architecture

### 1. **Lexer** (`TemplateLexer`)
Tokenizes template syntax into components:
```python
lexer = TemplateLexer("Hello {{ name }}!")
tokens = lexer.tokenize()
# [TEXT('Hello '), EXPRESSION('name'), TEXT('!')]
```

### 2. **Parser** (`TemplateParser`)
Builds AST from tokens:
```python
parser = TemplateParser(tokens)
nodes = parser.parse()
# [TextNode, ExpressionNode, TextNode]
```

### 3. **Context** (`TemplateContext`)
Manages variable scoping:
```python
context = TemplateContext({'user': 'Alice'})
context.push({'local_var': 'value'})  # New scope
```

### 4. **Nodes** (AST Classes)
- `TextNode` - Plain text
- `ExpressionNode` - Variable interpolation with filters
- `IfNode` - Conditional rendering
- `ForNode` - Loop iteration

### 5. **Engine** (`TemplateEngine`)
High-level interface:
```python
engine = TemplateEngine()
engine.set_global('site_name', 'My Site')
result = engine.render_string(template, context)
```

## 📊 Test Coverage

The implementation includes 12 comprehensive tests covering:
- ✅ Basic variable interpolation
- ✅ Filter application and chaining
- ✅ If/else conditionals
- ✅ For loops with loop variables
- ✅ Nested control structures
- ✅ Complex templates with multiple features
- ✅ Default value handling
- ✅ List processing and joining

All tests pass: **12/12** ✅

## 📚 Tutorials by Language

### JavaScript
- **[JavaScript template engine in just 20 lines](https://krasimirtsonev.com/blog/article/Javascript-template-engine-in-just-20-line)** - Minimal implementation
- **[Understanding JavaScript Micro-Templating](https://johnresig.com/blog/javascript-micro-templating/)** - John Resig's approach

### Python
- **[Approach: Building a toy template engine in Python](https://alexmic.net/building-a-template-engine/)** - Educational implementation
- **[A Template Engine](https://aosabook.org/en/500L/a-template-engine.html)** - Architecture of templating systems

### Ruby
- **[How to write a template engine in less than 30 lines of code](https://blog.jeremyfairbank.com/ruby/how-to-write-a-template-engine-in-less-than-30-lines-of-code/)** - Concise Ruby implementation

## 🎯 Key Concepts
- Template syntax design and parsing
- Variable interpolation and escaping
- Control structures (loops, conditionals)
- Template inheritance and composition  
- Context management and scoping
- Security considerations and XSS prevention

---

Start with simple variable substitution and evolve into full-featured templating systems!