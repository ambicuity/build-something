# Build Your Own HTTP Server

Learn how web servers work by building a complete HTTP server from scratch. You'll implement the HTTP protocol, request parsing, routing, static file serving, and middleware - all using only standard library functions.

## 🎯 What You'll Learn

- HTTP protocol fundamentals (requests, responses, status codes)
- Socket programming and network communication
- Request parsing and URL routing
- Static file serving with proper MIME types
- Basic middleware architecture
- Concurrent request handling with threading

## 📋 Prerequisites

- Understanding of network basics (TCP/IP, ports, sockets)
- Familiarity with HTTP protocol concepts
- Knowledge of file I/O operations
- Basic understanding of threading concepts

## 🏗️ Architecture Overview

Our HTTP server consists of these components:

1. **Socket Server**: Listens for incoming TCP connections
2. **Request Parser**: Parses incoming HTTP requests
3. **Router**: Maps URLs to handler functions
4. **Response Builder**: Creates properly formatted HTTP responses
5. **Static File Handler**: Serves files from the filesystem
6. **Middleware System**: Processes requests/responses in layers

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   TCP Socket    │───▶│    Parser    │───▶│     Router      │
│   (Port 8080)   │    │  (HTTP Req)  │    │  (URL → Handler)│
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                      │
┌─────────────────┐    ┌──────────────┐              ▼
│   HTTP Response │◄───│   Handler    │    ┌─────────────────┐
│   (Status+Body) │    │  (Process)   │    │   Middleware    │
└─────────────────┘    └──────────────┘    │ (Auth, Logging) │
                                           └─────────────────┘
```

## 🚀 Implementation Steps

### Step 1: Basic Socket Server

Let's start with a simple TCP server that can accept connections.

**Theory**: HTTP runs on top of TCP. We need to create a socket that listens for connections, accepts them, and reads the raw HTTP request data.

```python
import socket
import threading
from datetime import datetime

class HTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        
    def start(self):
        """Start the HTTP server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Server listening on {self.host}:{self.port}")
            
            while True:
                client_socket, address = self.socket.accept()
                print(f"Connection from {address}")
                
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            if self.socket:
                self.socket.close()
    
    def handle_client(self, client_socket):
        """Handle individual client connections"""
        try:
            # Read the request
            request_data = client_socket.recv(4096).decode('utf-8')
            if request_data:
                print(f"Received:\n{request_data}")
                
                # Send a simple response
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html\r\n"
                    "Content-Length: 13\r\n"
                    "\r\n"
                    "Hello, World!"
                )
                client_socket.send(response.encode('utf-8'))
        
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

# Test the basic server
if __name__ == "__main__":
    server = HTTPServer()
    server.start()
```

**Test it**: Run the server and visit `http://localhost:8080` in your browser.

### Step 2: HTTP Request Parser

Now let's parse HTTP requests properly to extract the method, path, headers, and body.

**Theory**: HTTP requests have a specific format:
```
METHOD /path HTTP/1.1
Header-Name: Header-Value
Another-Header: Value

Request Body (optional)
```

```python
from urllib.parse import urlparse, parse_qs

class HTTPRequest:
    """Represents an HTTP request"""
    
    def __init__(self, raw_request):
        self.method = ""
        self.path = ""
        self.query_params = {}
        self.headers = {}
        self.body = ""
        self.version = ""
        
        self.parse(raw_request)
    
    def parse(self, raw_request):
        """Parse raw HTTP request string"""
        if not raw_request:
            return
            
        lines = raw_request.split('\r\n')
        if not lines:
            return
        
        # Parse request line (METHOD /path HTTP/1.1)
        request_line = lines[0]
        parts = request_line.split(' ')
        if len(parts) >= 3:
            self.method = parts[0]
            full_path = parts[1]
            self.version = parts[2]
            
            # Parse path and query parameters
            parsed_url = urlparse(full_path)
            self.path = parsed_url.path
            self.query_params = parse_qs(parsed_url.query)
        
        # Parse headers
        header_end = 1
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                header_end = i + 1
                break
            
            if ':' in line:
                key, value = line.split(':', 1)
                self.headers[key.strip().lower()] = value.strip()
        
        # Parse body (everything after empty line)
        if header_end < len(lines):
            self.body = '\r\n'.join(lines[header_end:])

class HTTPResponse:
    """Represents an HTTP response"""
    
    def __init__(self, status_code=200, headers=None, body=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body
        
        # Set default headers
        if 'content-type' not in self.headers:
            self.headers['content-type'] = 'text/html; charset=utf-8'
        
        if 'server' not in self.headers:
            self.headers['server'] = 'MyHTTPServer/1.0'
        
        if 'date' not in self.headers:
            self.headers['date'] = datetime.utcnow().strftime(
                '%a, %d %b %Y %H:%M:%S GMT'
            )
    
    def to_bytes(self):
        """Convert response to bytes for sending"""
        # Status line
        status_messages = {
            200: 'OK',
            404: 'Not Found',
            500: 'Internal Server Error',
            403: 'Forbidden',
            405: 'Method Not Allowed'
        }
        
        status_line = f"HTTP/1.1 {self.status_code} {status_messages.get(self.status_code, 'Unknown')}\r\n"
        
        # Headers
        header_lines = []
        for key, value in self.headers.items():
            header_lines.append(f"{key.title()}: {value}\r\n")
        
        # Body
        body_bytes = self.body.encode('utf-8') if isinstance(self.body, str) else self.body
        header_lines.append(f"Content-Length: {len(body_bytes)}\r\n")
        
        # Combine all parts
        response = status_line + ''.join(header_lines) + '\r\n'
        return response.encode('utf-8') + body_bytes

# Update the server to use the new parser
class HTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.socket = None
    
    # ... start() method unchanged ...
    
    def handle_client(self, client_socket):
        """Handle individual client connections"""
        try:
            # Read the request
            request_data = client_socket.recv(4096).decode('utf-8')
            if not request_data:
                return
            
            # Parse the request
            request = HTTPRequest(request_data)
            print(f"{request.method} {request.path}")
            
            # Create response
            response = HTTPResponse(
                status_code=200,
                body=f"<h1>Hello from MyHTTPServer!</h1>"
                     f"<p>Method: {request.method}</p>"
                     f"<p>Path: {request.path}</p>"
                     f"<p>Headers: {request.headers}</p>"
            )
            
            # Send response
            client_socket.send(response.to_bytes())
        
        except Exception as e:
            print(f"Error handling client: {e}")
            # Send error response
            error_response = HTTPResponse(
                status_code=500,
                body="<h1>Internal Server Error</h1>"
            )
            try:
                client_socket.send(error_response.to_bytes())
            except:
                pass
        finally:
            client_socket.close()
```

**Test it**: The server now properly parses requests and shows request details in the response.

### Step 3: URL Routing System

Add a routing system to handle different URLs with different functions.

**Theory**: Web frameworks use routing to map URL patterns to handler functions. This allows you to define what happens when someone visits different paths.

```python
import re
from typing import Callable, Dict, List, Tuple

class Route:
    """Represents a single route"""
    
    def __init__(self, pattern: str, handler: Callable, methods: List[str] = None):
        self.pattern = pattern
        self.handler = handler
        self.methods = methods or ['GET']
        self.regex = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern: str):
        """Convert URL pattern to regex"""
        # Replace {param} with named groups
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', pattern)
        return re.compile(f'^{pattern}$')
    
    def match(self, path: str, method: str):
        """Check if this route matches the given path and method"""
        if method not in self.methods:
            return None, {}
        
        match = self.regex.match(path)
        if match:
            return True, match.groupdict()
        return None, {}

class Router:
    """HTTP request router"""
    
    def __init__(self):
        self.routes: List[Route] = []
        self.middleware: List[Callable] = []
    
    def add_route(self, pattern: str, handler: Callable, methods: List[str] = None):
        """Add a route"""
        route = Route(pattern, handler, methods)
        self.routes.append(route)
    
    def get(self, pattern: str):
        """Decorator for GET routes"""
        def decorator(handler):
            self.add_route(pattern, handler, ['GET'])
            return handler
        return decorator
    
    def post(self, pattern: str):
        """Decorator for POST routes"""
        def decorator(handler):
            self.add_route(pattern, handler, ['POST'])
            return handler
        return decorator
    
    def route(self, path: str, method: str, request: HTTPRequest):
        """Route a request to the appropriate handler"""
        for route in self.routes:
            matched, params = route.match(path, method)
            if matched:
                # Add params to request
                request.path_params = params
                return route.handler(request)
        
        # No route found
        return HTTPResponse(
            status_code=404,
            body="<h1>404 Not Found</h1><p>The requested page was not found.</p>"
        )
    
    def add_middleware(self, middleware: Callable):
        """Add middleware function"""
        self.middleware.append(middleware)

# Update HTTPServer to use routing
class HTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.router = Router()
    
    # ... start() method unchanged ...
    
    def handle_client(self, client_socket):
        """Handle individual client connections"""
        try:
            # Read the request
            request_data = client_socket.recv(4096).decode('utf-8')
            if not request_data:
                return
            
            # Parse the request
            request = HTTPRequest(request_data)
            print(f"{request.method} {request.path}")
            
            # Route the request
            response = self.router.route(request.path, request.method, request)
            
            # Send response
            client_socket.send(response.to_bytes())
        
        except Exception as e:
            print(f"Error handling client: {e}")
            error_response = HTTPResponse(
                status_code=500,
                body="<h1>Internal Server Error</h1>"
            )
            try:
                client_socket.send(error_response.to_bytes())
            except:
                pass
        finally:
            client_socket.close()

# Example usage
def create_app():
    """Create and configure the web application"""
    server = HTTPServer()
    
    @server.router.get('/')
    def home(request):
        return HTTPResponse(
            body="""
            <h1>Welcome to MyHTTPServer!</h1>
            <p>Available routes:</p>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/user/john">User Profile (john)</a></li>
                <li><a href="/static/test.html">Static Files</a></li>
            </ul>
            """
        )
    
    @server.router.get('/about')
    def about(request):
        return HTTPResponse(
            body="<h1>About</h1><p>This is a simple HTTP server built from scratch!</p>"
        )
    
    @server.router.get('/user/{username}')
    def user_profile(request):
        username = request.path_params['username']
        return HTTPResponse(
            body=f"<h1>User Profile</h1><p>Welcome, {username}!</p>"
        )
    
    return server

if __name__ == "__main__":
    app = create_app()
    app.start()
```

**Test it**: Visit different URLs to see routing in action:
- `http://localhost:8080/` - Home page
- `http://localhost:8080/about` - About page  
- `http://localhost:8080/user/alice` - User profile with parameter

### Step 4: Static File Serving

Add the ability to serve static files (HTML, CSS, JS, images) from the filesystem.

**Theory**: Web servers need to serve static content like HTML files, stylesheets, and images. We need to read files from disk and send them with appropriate MIME types.

```python
import os
import mimetypes
from pathlib import Path

class StaticFileHandler:
    """Handles serving static files"""
    
    def __init__(self, static_dir='static', url_prefix='/static'):
        self.static_dir = Path(static_dir)
        self.url_prefix = url_prefix
        
        # Ensure static directory exists
        self.static_dir.mkdir(exist_ok=True)
    
    def handle(self, request):
        """Handle static file requests"""
        # Remove URL prefix to get relative file path
        if not request.path.startswith(self.url_prefix):
            return HTTPResponse(status_code=404, body="Not Found")
        
        relative_path = request.path[len(self.url_prefix):].lstrip('/')
        if not relative_path:
            relative_path = 'index.html'
        
        file_path = self.static_dir / relative_path
        
        # Security: prevent directory traversal
        try:
            file_path = file_path.resolve()
            self.static_dir.resolve()
            if not str(file_path).startswith(str(self.static_dir.resolve())):
                return HTTPResponse(status_code=403, body="Forbidden")
        except:
            return HTTPResponse(status_code=403, body="Forbidden")
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            return HTTPResponse(status_code=404, body="File Not Found")
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except IOError:
            return HTTPResponse(status_code=500, body="Error reading file")
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Create response
        return HTTPResponse(
            status_code=200,
            headers={'content-type': mime_type},
            body=content
        )

# Update the server to handle static files
def create_app():
    """Create and configure the web application"""
    server = HTTPServer()
    static_handler = StaticFileHandler()
    
    @server.router.get('/')
    def home(request):
        return HTTPResponse(
            body="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>MyHTTPServer</title>
                <link rel="stylesheet" href="/static/style.css">
            </head>
            <body>
                <h1>Welcome to MyHTTPServer!</h1>
                <p>Available routes:</p>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/user/john">User Profile (john)</a></li>
                    <li><a href="/static/demo.html">Static Demo</a></li>
                </ul>
                <script src="/static/app.js"></script>
            </body>
            </html>
            """
        )
    
    @server.router.get('/about')
    def about(request):
        return HTTPResponse(
            body="""
            <h1>About</h1>
            <p>This is a simple HTTP server built from scratch!</p>
            <p>Features:</p>
            <ul>
                <li>Request parsing</li>
                <li>URL routing</li>
                <li>Static file serving</li>
                <li>Middleware support</li>
            </ul>
            """
        )
    
    @server.router.get('/user/{username}')
    def user_profile(request):
        username = request.path_params['username']
        return HTTPResponse(
            body=f"""
            <h1>User Profile</h1>
            <p>Welcome, {username}!</p>
            <p>Query params: {request.query_params}</p>
            """
        )
    
    # Handle static files with a catch-all route
    @server.router.get('/static/{path:.*}')
    def static_files(request):
        return static_handler.handle(request)
    
    return server
```

Let's create some sample static files to test:

```python
def create_static_files():
    """Create sample static files"""
    static_dir = Path('static')
    static_dir.mkdir(exist_ok=True)
    
    # CSS file
    (static_dir / 'style.css').write_text("""
    body {
        font-family: Arial, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
    }
    
    h1 {
        color: #333;
        border-bottom: 2px solid #007acc;
        padding-bottom: 10px;
    }
    
    a {
        color: #007acc;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    """)
    
    # JavaScript file
    (static_dir / 'app.js').write_text("""
    console.log('MyHTTPServer is running!');
    
    document.addEventListener('DOMContentLoaded', function() {
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                console.log('Navigating to:', this.href);
            });
        });
    });
    """)
    
    # HTML demo page
    (static_dir / 'demo.html').write_text("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Static File Demo</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        <h1>Static File Demo</h1>
        <p>This page is served as a static file!</p>
        <p>It includes:</p>
        <ul>
            <li>CSS styling (style.css)</li>
            <li>JavaScript functionality (app.js)</li>
            <li>Static HTML content</li>
        </ul>
        <a href="/">Back to Home</a>
        <script src="app.js"></script>
    </body>
    </html>
    """)
```

### Step 5: Middleware System

Add middleware support for cross-cutting concerns like logging, authentication, and CORS.

**Theory**: Middleware functions run before or after request handlers, allowing you to modify requests/responses or add functionality like logging and authentication.

```python
from functools import wraps

class Middleware:
    """Base middleware class"""
    
    def before_request(self, request):
        """Called before the request handler"""
        return None  # Return HTTPResponse to short-circuit
    
    def after_request(self, request, response):
        """Called after the request handler"""
        return response  # Return modified response

class LoggingMiddleware(Middleware):
    """Logs all requests"""
    
    def before_request(self, request):
        print(f"[{datetime.now()}] {request.method} {request.path}")
        return None
    
    def after_request(self, request, response):
        print(f"[{datetime.now()}] Response: {response.status_code}")
        return response

class CORSMiddleware(Middleware):
    """Adds CORS headers"""
    
    def after_request(self, request, response):
        response.headers['access-control-allow-origin'] = '*'
        response.headers['access-control-allow-methods'] = 'GET, POST, PUT, DELETE'
        response.headers['access-control-allow-headers'] = 'Content-Type, Authorization'
        return response

class AuthMiddleware(Middleware):
    """Simple API key authentication"""
    
    def __init__(self, api_key='secret-key'):
        self.api_key = api_key
    
    def before_request(self, request):
        # Skip auth for static files and home page
        if request.path.startswith('/static') or request.path == '/':
            return None
        
        auth_header = request.headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            return HTTPResponse(
                status_code=401,
                body='<h1>Unauthorized</h1><p>API key required</p>'
            )
        
        token = auth_header[7:]  # Remove 'Bearer '
        if token != self.api_key:
            return HTTPResponse(
                status_code=401,
                body='<h1>Unauthorized</h1><p>Invalid API key</p>'
            )
        
        return None

# Update Router to support middleware
class Router:
    def __init__(self):
        self.routes: List[Route] = []
        self.middleware: List[Middleware] = []
    
    def add_middleware(self, middleware: Middleware):
        """Add middleware"""
        self.middleware.append(middleware)
    
    def route(self, path: str, method: str, request: HTTPRequest):
        """Route a request through middleware and handlers"""
        # Before request middleware
        for middleware in self.middleware:
            response = middleware.before_request(request)
            if response:  # Middleware returned a response, short-circuit
                return response
        
        # Find and execute route handler
        response = None
        for route in self.routes:
            matched, params = route.match(path, method)
            if matched:
                request.path_params = params
                response = route.handler(request)
                break
        
        if response is None:
            response = HTTPResponse(
                status_code=404,
                body="<h1>404 Not Found</h1><p>The requested page was not found.</p>"
            )
        
        # After request middleware
        for middleware in self.middleware:
            response = middleware.after_request(request, response)
        
        return response

# Complete server example with middleware
def create_app():
    """Create and configure the web application"""
    server = HTTPServer()
    static_handler = StaticFileHandler()
    
    # Add middleware
    server.router.add_middleware(LoggingMiddleware())
    server.router.add_middleware(CORSMiddleware())
    # server.router.add_middleware(AuthMiddleware())  # Uncomment to enable auth
    
    @server.router.get('/')
    def home(request):
        return HTTPResponse(
            body="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>MyHTTPServer</title>
                <link rel="stylesheet" href="/static/style.css">
            </head>
            <body>
                <h1>Welcome to MyHTTPServer!</h1>
                <p>A complete HTTP server built from scratch with:</p>
                <ul>
                    <li>✅ Request parsing</li>
                    <li>✅ URL routing with parameters</li>
                    <li>✅ Static file serving</li>
                    <li>✅ Middleware support</li>
                    <li>✅ Proper HTTP responses</li>
                </ul>
                
                <h2>Try these routes:</h2>
                <ul>
                    <li><a href="/about">About page</a></li>
                    <li><a href="/user/alice">User profile</a></li>
                    <li><a href="/api/data">API endpoint</a></li>
                    <li><a href="/static/demo.html">Static demo</a></li>
                </ul>
                
                <script src="/static/app.js"></script>
            </body>
            </html>
            """
        )
    
    @server.router.get('/api/data')
    def api_data(request):
        return HTTPResponse(
            headers={'content-type': 'application/json'},
            body='{"message": "Hello from API!", "timestamp": "' + str(datetime.now()) + '"}'
        )
    
    @server.router.get('/static/{path:.*}')
    def static_files(request):
        return static_handler.handle(request)
    
    return server

if __name__ == "__main__":
    # Create static files
    create_static_files()
    
    # Start server
    app = create_app()
    app.start()
```

## 🧪 Testing Your Implementation

Create a comprehensive test suite:

```python
import requests
import json
from threading import Thread
import time

def test_server():
    """Test the HTTP server functionality"""
    base_url = "http://localhost:8080"
    
    # Test 1: Home page
    response = requests.get(f"{base_url}/")
    assert response.status_code == 200
    assert "MyHTTPServer" in response.text
    print("✅ Home page works")
    
    # Test 2: About page
    response = requests.get(f"{base_url}/about")
    assert response.status_code == 200
    print("✅ About page works")
    
    # Test 3: User profile with parameter
    response = requests.get(f"{base_url}/user/testuser")
    assert response.status_code == 200
    assert "testuser" in response.text
    print("✅ Parameterized routes work")
    
    # Test 4: Static files
    response = requests.get(f"{base_url}/static/demo.html")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/html'
    print("✅ Static file serving works")
    
    # Test 5: API endpoint
    response = requests.get(f"{base_url}/api/data")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/json'
    data = json.loads(response.text)
    assert "message" in data
    print("✅ JSON API works")
    
    # Test 6: 404 handling
    response = requests.get(f"{base_url}/nonexistent")
    assert response.status_code == 404
    print("✅ 404 handling works")
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    # Start server in background thread
    app = create_app()
    server_thread = Thread(target=app.start)
    server_thread.daemon = True
    server_thread.start()
    
    time.sleep(1)  # Wait for server to start
    
    try:
        test_server()
    except requests.exceptions.ConnectionError:
        print("Server not running. Start the server first.")
```

## 🎯 Challenges to Extend Your Implementation

1. **HTTPS Support**: Add SSL/TLS encryption
2. **File Upload**: Handle multipart form data
3. **Session Management**: Implement cookies and sessions
4. **Template Engine**: Add a simple templating system
5. **WebSocket Support**: Upgrade HTTP connections to WebSocket
6. **Compression**: Add gzip compression for responses
7. **Caching**: Implement HTTP caching headers
8. **Rate Limiting**: Add request rate limiting

## 📚 Key Concepts Learned

- **HTTP Protocol**: Request/response format, status codes, headers
- **Socket Programming**: TCP connections, client-server communication
- **URL Routing**: Pattern matching and parameter extraction
- **File I/O**: Reading files and determining MIME types
- **Middleware Pattern**: Request/response processing pipeline
- **Concurrency**: Handling multiple simultaneous connections

## 🔗 Further Reading

- [HTTP/1.1 Specification (RFC 7230)](https://tools.ietf.org/html/rfc7230)
- [Socket Programming Guide](https://docs.python.org/3/howto/sockets.html)
- Web framework architectures (Flask, Express.js)

---

**Congratulations!** You've built a fully functional HTTP server that can handle routing, static files, and middleware. You now understand the fundamentals that power all web servers and frameworks.