# Build Your Own Load Balancer

Learn distributed systems and high availability by building HTTP load balancers from scratch. Understand traffic distribution, health checking, failover mechanisms, and performance optimization techniques.

## 🎯 What You'll Learn

- Load balancing algorithms and traffic distribution strategies
- Health checking and server monitoring systems
- HTTP proxy implementation and request forwarding
- Circuit breaker patterns and fault tolerance
- SSL termination and security considerations
- Performance monitoring and metrics collection

## 📋 Prerequisites

- Understanding of HTTP protocol and web servers
- Knowledge of network programming and TCP/IP
- Basic understanding of distributed systems concepts
- Familiarity with concurrent programming patterns

## 🏗️ Architecture Overview

Our load balancer consists of these core components:

1. **Frontend Proxy**: Accepts client connections
2. **Backend Pool**: Manages upstream servers
3. **Health Checker**: Monitors server availability
4. **Load Balancer**: Distributes requests across servers
5. **Connection Manager**: Handles persistent connections
6. **Metrics Collector**: Tracks performance statistics

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Clients   │───▶│ Load Balancer│───▶│  Backend Pool   │
│             │    │   (Proxy)    │    │   Server 1      │
└─────────────┘    └──────────────┘    │   Server 2      │
                          │             │   Server 3      │
┌─────────────┐    ┌──────────────┐    └─────────────────┘
│   Health    │◄───│   Metrics    │            ▲
│  Checker    │    │  Collector   │            │
└─────────────┘    └──────────────┘            ▼
                                    ┌─────────────────┐
                                    │ Connection Pool │
                                    │   Management    │
                                    └─────────────────┘
```

## 🚀 Implementation Steps

### Step 1: Basic HTTP Proxy

Start with a simple reverse proxy that forwards requests to a single backend.

```python
import socket
import threading
import time
from urllib.parse import urlparse

class BasicProxy:
    def __init__(self, listen_port, backend_host, backend_port):
        self.listen_port = listen_port
        self.backend_host = backend_host
        self.backend_port = backend_port
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.listen_port))
        server_socket.listen(10)
        
        print(f"Proxy listening on port {self.listen_port}")
        
        while True:
            client_socket, client_addr = server_socket.accept()
            thread = threading.Thread(
                target=self.handle_request,
                args=(client_socket,)
            )
            thread.daemon = True
            thread.start()
    
    def handle_request(self, client_socket):
        try:
            # Receive request from client
            request_data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                if b"\r\n\r\n" in request_data:
                    break
            
            if not request_data:
                return
            
            # Forward to backend
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.connect((self.backend_host, self.backend_port))
            backend_socket.send(request_data)
            
            # Forward response back to client
            while True:
                response_chunk = backend_socket.recv(4096)
                if not response_chunk:
                    break
                client_socket.send(response_chunk)
                
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            client_socket.close()
            if 'backend_socket' in locals():
                backend_socket.close()
```

### Step 2: Backend Server Pool

Implement a pool of backend servers with basic selection.

```python
import random
from enum import Enum

class ServerStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class BackendServer:
    def __init__(self, host, port, weight=1):
        self.host = host
        self.port = port
        self.weight = weight
        self.status = ServerStatus.UNKNOWN
        self.connections = 0
        self.total_requests = 0
        self.failed_requests = 0
        self.response_times = []
        
    def __str__(self):
        return f"{self.host}:{self.port}"

class BackendPool:
    def __init__(self):
        self.servers = []
        self.current_index = 0
        
    def add_server(self, host, port, weight=1):
        server = BackendServer(host, port, weight)
        self.servers.append(server)
        
    def remove_server(self, host, port):
        self.servers = [s for s in self.servers 
                       if not (s.host == host and s.port == port)]
    
    def get_healthy_servers(self):
        return [s for s in self.servers 
                if s.status == ServerStatus.HEALTHY]
    
    def get_next_server_round_robin(self):
        """Round-robin load balancing"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None
            
        server = healthy_servers[self.current_index % len(healthy_servers)]
        self.current_index = (self.current_index + 1) % len(healthy_servers)
        return server
    
    def get_next_server_weighted(self):
        """Weighted random selection"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None
            
        total_weight = sum(s.weight for s in healthy_servers)
        random_weight = random.randint(1, total_weight)
        
        current_weight = 0
        for server in healthy_servers:
            current_weight += server.weight
            if random_weight <= current_weight:
                return server
        
        return healthy_servers[0]  # Fallback
    
    def get_next_server_least_connections(self):
        """Least connections load balancing"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None
            
        return min(healthy_servers, key=lambda s: s.connections)
```

### Step 3: Health Checking System

Implement active health monitoring for backend servers.

```python
import time
import threading
import requests
from datetime import datetime, timedelta

class HealthChecker:
    def __init__(self, backend_pool, check_interval=10):
        self.backend_pool = backend_pool
        self.check_interval = check_interval
        self.running = False
        self.check_thread = None
        
    def start(self):
        self.running = True
        self.check_thread = threading.Thread(target=self._health_check_loop)
        self.check_thread.daemon = True
        self.check_thread.start()
        
    def stop(self):
        self.running = False
        if self.check_thread:
            self.check_thread.join()
    
    def _health_check_loop(self):
        while self.running:
            for server in self.backend_pool.servers:
                try:
                    self._check_server_health(server)
                except Exception as e:
                    print(f"Health check error for {server}: {e}")
                    server.status = ServerStatus.UNHEALTHY
            
            time.sleep(self.check_interval)
    
    def _check_server_health(self, server):
        """Perform health check on a single server"""
        start_time = time.time()
        
        try:
            # Simple HTTP GET health check
            url = f"http://{server.host}:{server.port}/health"
            response = requests.get(url, timeout=5)
            
            response_time = time.time() - start_time
            server.response_times.append(response_time)
            
            # Keep only last 10 response times
            if len(server.response_times) > 10:
                server.response_times = server.response_times[-10:]
            
            if response.status_code == 200:
                server.status = ServerStatus.HEALTHY
                print(f"✅ {server} is healthy (response time: {response_time:.3f}s)")
            else:
                server.status = ServerStatus.UNHEALTHY
                print(f"❌ {server} returned {response.status_code}")
                
        except Exception as e:
            server.status = ServerStatus.UNHEALTHY
            print(f"❌ {server} failed health check: {e}")
```

### Step 4: Load Balancing Algorithms

Implement various load balancing strategies.

```python
import hashlib
from abc import ABC, abstractmethod

class LoadBalancingAlgorithm(ABC):
    @abstractmethod
    def select_server(self, backend_pool, request_info=None):
        pass

class RoundRobinBalancer(LoadBalancingAlgorithm):
    def __init__(self):
        self.current_index = 0
    
    def select_server(self, backend_pool, request_info=None):
        healthy_servers = backend_pool.get_healthy_servers()
        if not healthy_servers:
            return None
        
        server = healthy_servers[self.current_index % len(healthy_servers)]
        self.current_index = (self.current_index + 1) % len(healthy_servers)
        return server

class WeightedRoundRobinBalancer(LoadBalancingAlgorithm):
    def __init__(self):
        self.server_weights = {}
    
    def select_server(self, backend_pool, request_info=None):
        healthy_servers = backend_pool.get_healthy_servers()
        if not healthy_servers:
            return None
        
        # Initialize weights if needed
        for server in healthy_servers:
            if server not in self.server_weights:
                self.server_weights[server] = 0
        
        # Find server with highest current weight
        selected_server = max(healthy_servers, 
                            key=lambda s: self.server_weights[s])
        
        # Decrease selected server's weight and increase others
        self.server_weights[selected_server] -= sum(s.weight for s in healthy_servers)
        for server in healthy_servers:
            self.server_weights[server] += server.weight
        
        return selected_server

class LeastConnectionsBalancer(LoadBalancingAlgorithm):
    def select_server(self, backend_pool, request_info=None):
        healthy_servers = backend_pool.get_healthy_servers()
        if not healthy_servers:
            return None
        
        return min(healthy_servers, key=lambda s: s.connections)

class IPHashBalancer(LoadBalancingAlgorithm):
    def select_server(self, backend_pool, request_info=None):
        healthy_servers = backend_pool.get_healthy_servers()
        if not healthy_servers:
            return None
        
        if not request_info or 'client_ip' not in request_info:
            return healthy_servers[0]
        
        # Hash client IP to consistently select same server
        client_ip = request_info['client_ip']
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return healthy_servers[hash_value % len(healthy_servers)]

class LoadBalancer:
    def __init__(self, backend_pool, algorithm='round_robin'):
        self.backend_pool = backend_pool
        self.algorithms = {
            'round_robin': RoundRobinBalancer(),
            'weighted_round_robin': WeightedRoundRobinBalancer(),
            'least_connections': LeastConnectionsBalancer(),
            'ip_hash': IPHashBalancer()
        }
        self.current_algorithm = self.algorithms[algorithm]
    
    def set_algorithm(self, algorithm):
        if algorithm in self.algorithms:
            self.current_algorithm = self.algorithms[algorithm]
    
    def select_server(self, request_info=None):
        return self.current_algorithm.select_server(self.backend_pool, request_info)
```

### Step 5: Circuit Breaker Pattern

Implement fault tolerance with circuit breakers.

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, 
                 request_threshold=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.request_threshold = request_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def _record_success(self):
        """Record successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.request_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if (self.state == CircuitState.CLOSED and 
            self.failure_count >= self.failure_threshold):
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
```

### Step 6: Complete Load Balancer

Integrate all components into a full-featured load balancer.

```python
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class LoadBalancerHandler(BaseHTTPRequestHandler):
    def __init__(self, load_balancer, *args, **kwargs):
        self.load_balancer = load_balancer
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def _handle_request(self):
        """Handle incoming request and forward to backend"""
        start_time = time.time()
        
        try:
            # Get client information
            client_ip = self.client_address[0]
            request_info = {'client_ip': client_ip}
            
            # Select backend server
            server = self.load_balancer.select_server(request_info)
            if not server:
                self._send_error_response(503, "No healthy backends available")
                return
            
            # Update connection count
            server.connections += 1
            server.total_requests += 1
            
            try:
                # Forward request to backend
                response = self._forward_request_to_backend(server)
                
                # Send response to client
                self.send_response(response['status'])
                for header, value in response['headers'].items():
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response['body'])
                
            except Exception as e:
                server.failed_requests += 1
                self._send_error_response(502, f"Backend error: {str(e)}")
            finally:
                server.connections -= 1
                
        except Exception as e:
            self._send_error_response(500, f"Load balancer error: {str(e)}")
        
        # Record response time
        response_time = time.time() - start_time
        if 'server' in locals():
            server.response_times.append(response_time)
    
    def _forward_request_to_backend(self, server):
        """Forward HTTP request to backend server"""
        import http.client
        
        # Create connection to backend
        conn = http.client.HTTPConnection(server.host, server.port)
        
        # Forward the request
        conn.request(self.command, self.path, 
                    body=self._read_request_body(),
                    headers=dict(self.headers))
        
        # Get response
        response = conn.getresponse()
        
        return {
            'status': response.status,
            'headers': dict(response.getheaders()),
            'body': response.read()
        }
    
    def _read_request_body(self):
        """Read request body for POST/PUT requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return self.rfile.read(content_length)
        return b''
    
    def _send_error_response(self, status, message):
        """Send error response to client"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_body = json.dumps({'error': message}).encode()
        self.wfile.write(error_body)

class HTTPLoadBalancer:
    def __init__(self, listen_port=8080):
        self.listen_port = listen_port
        self.backend_pool = BackendPool()
        self.load_balancer = LoadBalancer(self.backend_pool)
        self.health_checker = HealthChecker(self.backend_pool)
        
    def add_backend(self, host, port, weight=1):
        """Add backend server to the pool"""
        self.backend_pool.add_server(host, port, weight)
    
    def start(self):
        """Start the load balancer"""
        print(f"Starting load balancer on port {self.listen_port}")
        
        # Start health checker
        self.health_checker.start()
        
        # Create HTTP server with custom handler
        def handler_factory(*args, **kwargs):
            return LoadBalancerHandler(self.load_balancer, *args, **kwargs)
        
        server = HTTPServer(('', self.listen_port), handler_factory)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down load balancer...")
            self.health_checker.stop()
            server.shutdown()

# Example usage
if __name__ == "__main__":
    lb = HTTPLoadBalancer(8080)
    
    # Add backend servers
    lb.add_backend('localhost', 3001, weight=3)
    lb.add_backend('localhost', 3002, weight=2)
    lb.add_backend('localhost', 3003, weight=1)
    
    # Set load balancing algorithm
    lb.load_balancer.set_algorithm('weighted_round_robin')
    
    # Start load balancer
    lb.start()
```

## 📚 Tutorials by Language

### Python
- **[Building a Load Balancer](https://karimjedda.com/building-load-balancer/)** - Complete Python implementation
- **[Implementing a Simple Load Balancer in Python](https://medium.com/@amitosh/implementing-a-simple-load-balancer-in-python-5d9f5ad6e4b4)** - Basic load balancer
- **[Python Load Balancer with Health Checks](https://realpython.com/python-sockets/#multi-connection-client-and-server)** - Advanced networking

### Go
- **[Writing a Load Balancer in Go](https://kasvith.me/posts/lets-create-a-simple-lb-go/)** - Go implementation tutorial
- **[Building a Load Balancer in Go](https://www.sobyte.net/post/2022-02/load-balancer-go/)** - Production-ready load balancer
- **[Simple Load Balancer in Go](https://medium.com/@matryer/golang-advent-calendar-day-eleven-a-simple-client-side-load-balancer-for-go-5a9b4e52b8)** - Client-side balancing

### Java
- **[Building a Load Balancer with Java](https://www.baeldung.com/java-load-balancer)** - Java NIO implementation
- **[Simple HTTP Load Balancer](https://github.com/javadev/simple-load-balancer)** - Spring Boot load balancer

### Node.js
- **[Load Balancer in Node.js](https://medium.com/@diego.coder/creating-a-load-balancer-with-node-js-8d0e3cb04cc7)** - JavaScript implementation
- **[Building a Load Balancer with Node.js](https://blog.logrocket.com/building-load-balancer-node-js/)** - Complete Node.js guide

### C++
- **[High Performance Load Balancer](https://github.com/microsoft/FASTER)** - C++ system programming
- **[Network Programming in C++](https://www.boost.org/doc/libs/1_75_0/doc/html/boost_asio/tutorial.html)** - Boost.Asio networking

### Rust
- **[Load Balancer in Rust](https://github.com/tokio-rs/mini-redis)** - Async Rust networking
- **[Building Network Services with Rust](https://tokio.rs/tokio/tutorial)** - Tokio async runtime

## 🏗️ Project Ideas

### Beginner Projects
1. **Round-Robin Proxy** - Basic request distribution
2. **Health Check Monitor** - Server availability tracking
3. **Simple API Gateway** - Request routing and filtering

### Intermediate Projects
1. **Weighted Load Balancer** - Server capacity-based distribution
2. **Session-Aware Balancer** - Sticky session support
3. **Circuit Breaker System** - Fault tolerance implementation

### Advanced Projects
1. **Auto-Scaling Balancer** - Dynamic backend management
2. **Geographic Load Balancer** - Location-based routing
3. **Service Mesh Gateway** - Microservices communication

## ⚙️ Core Concepts

### Load Balancing Algorithms
- **Round Robin**: Sequential server selection
- **Weighted Round Robin**: Capacity-based distribution
- **Least Connections**: Connection count optimization
- **IP Hash**: Client affinity and session persistence

### Health Monitoring
- **Active Health Checks**: Proactive server monitoring
- **Passive Health Checks**: Request-based failure detection
- **Circuit Breakers**: Failure cascade prevention
- **Graceful Degradation**: Service quality management

### Performance Optimization
- **Connection Pooling**: Resource efficiency
- **Keep-Alive Connections**: Reduced connection overhead
- **Request Multiplexing**: Concurrent request handling
- **Caching Strategies**: Response optimization

## 🚀 Performance Optimization

### Network Performance
- **TCP Optimization**: Socket tuning and buffer management
- **HTTP/2 Support**: Multiplexed connections
- **SSL Termination**: Encrypted traffic handling
- **Compression**: Response size optimization

### Scalability Techniques
- **Horizontal Scaling**: Multiple load balancer instances
- **DNS Load Balancing**: Geographic distribution
- **Anycast Networking**: Global traffic distribution
- **Edge Computing**: Distributed processing

### Monitoring and Metrics
- **Request Latency**: Response time tracking
- **Throughput Metrics**: Request rate monitoring
- **Error Rates**: Failure tracking and alerting
- **Resource Utilization**: System performance monitoring

## 🧪 Testing Strategies

### Load Testing
- **Stress Testing**: Maximum capacity validation
- **Spike Testing**: Traffic burst handling
- **Volume Testing**: Large-scale data processing
- **Endurance Testing**: Long-term stability

### Failover Testing
- **Server Failure Simulation**: Backend outage handling
- **Network Partition Testing**: Split-brain scenarios
- **Graceful Shutdown**: Planned maintenance procedures
- **Recovery Testing**: Service restoration validation

## 🔗 Additional Resources

### Books
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices/9781491950340/) - Distributed system patterns
- [Designing Data-Intensive Applications](https://dataintensive.net/) - System architecture principles
- [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/) - Google's SRE practices

### Online Resources
- [HAProxy Documentation](http://www.haproxy.org/#docs) - Production load balancer reference
- [NGINX Load Balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/) - HTTP load balancing guide
- [AWS Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/) - Cloud load balancing
- [Envoy Proxy](https://www.envoyproxy.io/docs/envoy/latest/) - Modern service proxy

### Development Communities
- [/r/networking](https://www.reddit.com/r/networking/) - Network engineering discussions
- [High Scalability](http://highscalability.com/) - Architecture case studies
- [SRE Community](https://www.usenix.org/conferences/srecon) - Site reliability engineering
- [CNCF Projects](https://www.cncf.io/projects/) - Cloud native networking tools

---

**Ready to balance?** Start with a simple round-robin proxy and build up to a production-ready load balancer!