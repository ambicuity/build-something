# Build Your Own Key-Value Store

Create a Redis-like in-memory data structure server from scratch. Learn data structures, networking protocols, persistence mechanisms, and distributed system concepts.

## 🎯 What You'll Learn

- In-memory data structures and their implementations
- Network protocols and client-server communication
- Data persistence and durability mechanisms
- Concurrent programming and thread safety
- Memory management and garbage collection
- Distributed systems and replication strategies

## 📋 Prerequisites

- Understanding of basic data structures (hash tables, lists, sets)
- Knowledge of network programming and TCP sockets
- Familiarity with concurrent programming concepts
- Basic understanding of database systems

## 🏗️ Architecture Overview

Our key-value store consists of these core components:

1. **Storage Engine**: In-memory data structure management
2. **Protocol Handler**: Client communication and command parsing
3. **Persistence Layer**: Data durability and recovery
4. **Memory Manager**: Resource allocation and cleanup
5. **Replication System**: Data synchronization across nodes
6. **Expiration Manager**: Time-based key expiration

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Client    │───▶│   Protocol   │───▶│ Command Parser  │
│ (Redis CLI) │    │   Handler    │    │  (GET/SET/etc)  │
└─────────────┘    └──────────────┘    └─────────────────┘
                          │                       │
┌─────────────┐    ┌──────────────┐              ▼
│ Persistence │◄───│    Memory    │    ┌─────────────────┐
│   Layer     │    │   Manager    │    │ Storage Engine  │
└─────────────┘    └──────────────┘    │ (Hash, List,    │
                          ▲             │  Set, ZSet)     │
┌─────────────┐           │             └─────────────────┘
│ Replication │───────────┘                       │
│   System    │                                   ▼
└─────────────┘                         ┌─────────────────┐
                                        │   Expiration    │
                                        │    Manager      │
                                        └─────────────────┘
```

## 🚀 Implementation Steps

### Step 1: Core Data Structures

Start by implementing the fundamental data structures.

```python
import time
import threading
from collections import defaultdict
from typing import Any, Optional, Set, List, Dict

class RedisString:
    def __init__(self, value: str, ttl: Optional[float] = None):
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
    
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def get_value(self) -> Optional[str]:
        return None if self.is_expired() else self.value

class RedisList:
    def __init__(self):
        self.items: List[str] = []
        self.lock = threading.RLock()
    
    def lpush(self, *values: str) -> int:
        with self.lock:
            for value in reversed(values):
                self.items.insert(0, value)
            return len(self.items)
    
    def rpush(self, *values: str) -> int:
        with self.lock:
            self.items.extend(values)
            return len(self.items)
    
    def lpop(self) -> Optional[str]:
        with self.lock:
            return self.items.pop(0) if self.items else None
    
    def rpop(self) -> Optional[str]:
        with self.lock:
            return self.items.pop() if self.items else None
    
    def llen(self) -> int:
        with self.lock:
            return len(self.items)
    
    def lrange(self, start: int, stop: int) -> List[str]:
        with self.lock:
            return self.items[start:stop+1]

class RedisSet:
    def __init__(self):
        self.members: Set[str] = set()
        self.lock = threading.RLock()
    
    def sadd(self, *members: str) -> int:
        with self.lock:
            added = 0
            for member in members:
                if member not in self.members:
                    self.members.add(member)
                    added += 1
            return added
    
    def srem(self, *members: str) -> int:
        with self.lock:
            removed = 0
            for member in members:
                if member in self.members:
                    self.members.remove(member)
                    removed += 1
            return removed
    
    def sismember(self, member: str) -> bool:
        with self.lock:
            return member in self.members
    
    def smembers(self) -> Set[str]:
        with self.lock:
            return self.members.copy()
    
    def scard(self) -> int:
        with self.lock:
            return len(self.members)

class RedisHash:
    def __init__(self):
        self.fields: Dict[str, str] = {}
        self.lock = threading.RLock()
    
    def hset(self, field: str, value: str) -> int:
        with self.lock:
            exists = field in self.fields
            self.fields[field] = value
            return 0 if exists else 1
    
    def hget(self, field: str) -> Optional[str]:
        with self.lock:
            return self.fields.get(field)
    
    def hdel(self, *fields: str) -> int:
        with self.lock:
            deleted = 0
            for field in fields:
                if field in self.fields:
                    del self.fields[field]
                    deleted += 1
            return deleted
    
    def hgetall(self) -> Dict[str, str]:
        with self.lock:
            return self.fields.copy()
    
    def hlen(self) -> int:
        with self.lock:
            return len(self.fields)
```

### Step 2: Storage Engine

Implement the main storage system that manages all data structures.

```python
import threading
from enum import Enum
from typing import Union, Any

class DataType(Enum):
    STRING = "string"
    LIST = "list"
    SET = "set"
    HASH = "hash"
    ZSET = "zset"

class StorageEngine:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.types: Dict[str, DataType] = {}
        self.expiration: Dict[str, float] = {}
        self.lock = threading.RWLock()
        
        # Start expiration cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_keys)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
    
    def _cleanup_expired_keys(self):
        """Background thread to clean up expired keys"""
        while True:
            current_time = time.time()
            expired_keys = []
            
            with self.lock.read_lock():
                for key, expiry_time in self.expiration.items():
                    if current_time >= expiry_time:
                        expired_keys.append(key)
            
            if expired_keys:
                with self.lock.write_lock():
                    for key in expired_keys:
                        self._delete_key(key)
            
            time.sleep(1)  # Check every second
    
    def _delete_key(self, key: str):
        """Internal method to delete a key (assumes write lock held)"""
        if key in self.data:
            del self.data[key]
        if key in self.types:
            del self.types[key]
        if key in self.expiration:
            del self.expiration[key]
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key is expired"""
        if key not in self.expiration:
            return False
        return time.time() >= self.expiration[key]
    
    def set_string(self, key: str, value: str, ttl: Optional[float] = None) -> bool:
        """Set a string value"""
        with self.lock.write_lock():
            self.data[key] = RedisString(value, ttl)
            self.types[key] = DataType.STRING
            
            if ttl is not None:
                self.expiration[key] = time.time() + ttl
            elif key in self.expiration:
                del self.expiration[key]
            
            return True
    
    def get_string(self, key: str) -> Optional[str]:
        """Get a string value"""
        with self.lock.read_lock():
            if self._is_expired(key):
                return None
            
            if key not in self.data or self.types.get(key) != DataType.STRING:
                return None
            
            redis_string = self.data[key]
            return redis_string.get_value()
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        deleted = 0
        with self.lock.write_lock():
            for key in keys:
                if key in self.data:
                    self._delete_key(key)
                    deleted += 1
        return deleted
    
    def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        count = 0
        with self.lock.read_lock():
            for key in keys:
                if key in self.data and not self._is_expired(key):
                    count += 1
        return count
    
    def expire(self, key: str, seconds: float) -> bool:
        """Set expiration on a key"""
        with self.lock.write_lock():
            if key not in self.data or self._is_expired(key):
                return False
            
            self.expiration[key] = time.time() + seconds
            return True
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        with self.lock.read_lock():
            if key not in self.data:
                return -2  # Key doesn't exist
            
            if key not in self.expiration:
                return -1  # Key exists but has no expiration
            
            remaining = self.expiration[key] - time.time()
            return max(0, int(remaining))
    
    def get_or_create_list(self, key: str) -> Optional[RedisList]:
        """Get existing list or create new one"""
        with self.lock.write_lock():
            if self._is_expired(key):
                self._delete_key(key)
            
            if key not in self.data:
                self.data[key] = RedisList()
                self.types[key] = DataType.LIST
            elif self.types.get(key) != DataType.LIST:
                return None  # Wrong type
            
            return self.data[key]
    
    def get_or_create_set(self, key: str) -> Optional[RedisSet]:
        """Get existing set or create new one"""
        with self.lock.write_lock():
            if self._is_expired(key):
                self._delete_key(key)
            
            if key not in self.data:
                self.data[key] = RedisSet()
                self.types[key] = DataType.SET
            elif self.types.get(key) != DataType.SET:
                return None  # Wrong type
            
            return self.data[key]
    
    def get_or_create_hash(self, key: str) -> Optional[RedisHash]:
        """Get existing hash or create new one"""
        with self.lock.write_lock():
            if self._is_expired(key):
                self._delete_key(key)
            
            if key not in self.data:
                self.data[key] = RedisHash()
                self.types[key] = DataType.HASH
            elif self.types.get(key) != DataType.HASH:
                return None  # Wrong type
            
            return self.data[key]
```

### Step 3: Protocol Handler

Implement the Redis protocol for client communication.

```python
import socket
import threading
from typing import List, Optional, Any

class RedisProtocolHandler:
    def __init__(self, storage_engine: StorageEngine):
        self.storage = storage_engine
    
    def parse_command(self, data: bytes) -> Optional[List[str]]:
        """Parse Redis protocol command"""
        try:
            lines = data.decode('utf-8').strip().split('\r\n')
            if not lines or not lines[0].startswith('*'):
                return None
            
            num_args = int(lines[0][1:])
            args = []
            
            line_idx = 1
            for _ in range(num_args):
                if line_idx >= len(lines) or not lines[line_idx].startswith('$'):
                    return None
                
                arg_length = int(lines[line_idx][1:])
                line_idx += 1
                
                if line_idx >= len(lines):
                    return None
                
                arg = lines[line_idx][:arg_length]
                args.append(arg)
                line_idx += 1
            
            return args
        
        except (UnicodeDecodeError, ValueError, IndexError):
            return None
    
    def format_response(self, response: Any) -> bytes:
        """Format response in Redis protocol"""
        if response is None:
            return b"$-1\r\n"
        elif isinstance(response, str):
            return f"${len(response)}\r\n{response}\r\n".encode()
        elif isinstance(response, int):
            return f":{response}\r\n".encode()
        elif isinstance(response, list):
            result = f"*{len(response)}\r\n"
            for item in response:
                if isinstance(item, str):
                    result += f"${len(item)}\r\n{item}\r\n"
                else:
                    result += f":{item}\r\n"
            return result.encode()
        elif isinstance(response, set):
            return self.format_response(list(response))
        elif isinstance(response, dict):
            # Format hash as array of key-value pairs
            items = []
            for key, value in response.items():
                items.extend([key, value])
            return self.format_response(items)
        else:
            return f"+{str(response)}\r\n".encode()
    
    def execute_command(self, args: List[str]) -> Any:
        """Execute a Redis command"""
        if not args:
            return "ERR empty command"
        
        command = args[0].upper()
        
        # String commands
        if command == "SET":
            if len(args) < 3:
                return "ERR wrong number of arguments for 'set' command"
            key, value = args[1], args[2]
            
            # Handle optional TTL (EX seconds)
            ttl = None
            if len(args) > 3 and args[3].upper() == "EX":
                if len(args) < 5:
                    return "ERR wrong number of arguments for 'set' command"
                try:
                    ttl = float(args[4])
                except ValueError:
                    return "ERR invalid expire time in set"
            
            self.storage.set_string(key, value, ttl)
            return "OK"
        
        elif command == "GET":
            if len(args) != 2:
                return "ERR wrong number of arguments for 'get' command"
            return self.storage.get_string(args[1])
        
        elif command == "DEL":
            if len(args) < 2:
                return "ERR wrong number of arguments for 'del' command"
            return self.storage.delete(*args[1:])
        
        elif command == "EXISTS":
            if len(args) < 2:
                return "ERR wrong number of arguments for 'exists' command"
            return self.storage.exists(*args[1:])
        
        elif command == "EXPIRE":
            if len(args) != 3:
                return "ERR wrong number of arguments for 'expire' command"
            try:
                seconds = float(args[2])
                return 1 if self.storage.expire(args[1], seconds) else 0
            except ValueError:
                return "ERR invalid expire time"
        
        elif command == "TTL":
            if len(args) != 2:
                return "ERR wrong number of arguments for 'ttl' command"
            return self.storage.ttl(args[1])
        
        # List commands
        elif command == "LPUSH":
            if len(args) < 3:
                return "ERR wrong number of arguments for 'lpush' command"
            redis_list = self.storage.get_or_create_list(args[1])
            if redis_list is None:
                return "ERR wrong kind of value"
            return redis_list.lpush(*args[2:])
        
        elif command == "RPUSH":
            if len(args) < 3:
                return "ERR wrong number of arguments for 'rpush' command"
            redis_list = self.storage.get_or_create_list(args[1])
            if redis_list is None:
                return "ERR wrong kind of value"
            return redis_list.rpush(*args[2:])
        
        elif command == "LPOP":
            if len(args) != 2:
                return "ERR wrong number of arguments for 'lpop' command"
            redis_list = self.storage.get_or_create_list(args[1])
            if redis_list is None:
                return "ERR wrong kind of value"
            return redis_list.lpop()
        
        elif command == "LLEN":
            if len(args) != 2:
                return "ERR wrong number of arguments for 'llen' command"
            redis_list = self.storage.get_or_create_list(args[1])
            if redis_list is None:
                return "ERR wrong kind of value"
            return redis_list.llen()
        
        # Set commands
        elif command == "SADD":
            if len(args) < 3:
                return "ERR wrong number of arguments for 'sadd' command"
            redis_set = self.storage.get_or_create_set(args[1])
            if redis_set is None:
                return "ERR wrong kind of value"
            return redis_set.sadd(*args[2:])
        
        elif command == "SMEMBERS":
            if len(args) != 2:
                return "ERR wrong number of arguments for 'smembers' command"
            redis_set = self.storage.get_or_create_set(args[1])
            if redis_set is None:
                return "ERR wrong kind of value"
            return redis_set.smembers()
        
        # Hash commands
        elif command == "HSET":
            if len(args) < 4 or len(args) % 2 != 0:
                return "ERR wrong number of arguments for 'hset' command"
            redis_hash = self.storage.get_or_create_hash(args[1])
            if redis_hash is None:
                return "ERR wrong kind of value"
            
            added = 0
            for i in range(2, len(args), 2):
                added += redis_hash.hset(args[i], args[i + 1])
            return added
        
        elif command == "HGET":
            if len(args) != 3:
                return "ERR wrong number of arguments for 'hget' command"
            redis_hash = self.storage.get_or_create_hash(args[1])
            if redis_hash is None:
                return "ERR wrong kind of value"
            return redis_hash.hget(args[2])
        
        elif command == "HGETALL":
            if len(args) != 2:
                return "ERR wrong number of arguments for 'hgetall' command"
            redis_hash = self.storage.get_or_create_hash(args[1])
            if redis_hash is None:
                return "ERR wrong kind of value"
            return redis_hash.hgetall()
        
        # Server commands
        elif command == "PING":
            return "PONG"
        
        elif command == "INFO":
            # Return basic server info
            info = "# Server\r\n"
            info += "redis_version:7.0.0-custom\r\n"
            info += "redis_mode:standalone\r\n"
            info += "# Clients\r\n"
            info += "connected_clients:1\r\n"
            return info
        
        else:
            return f"ERR unknown command '{command}'"
```

### Step 4: Network Server

Create the TCP server to handle client connections.

```python
import socket
import threading
import select
from concurrent.futures import ThreadPoolExecutor

class RedisServer:
    def __init__(self, host='localhost', port=6379, max_clients=100):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        
        self.storage = StorageEngine()
        self.protocol = RedisProtocolHandler(self.storage)
        
        self.server_socket = None
        self.running = False
        
        # Thread pool for handling clients
        self.executor = ThreadPoolExecutor(max_workers=max_clients)
    
    def start(self):
        """Start the Redis server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            self.running = True
            
            print(f"Redis server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    # Accept new client connections
                    client_socket, client_addr = self.server_socket.accept()
                    print(f"New client connected: {client_addr}")
                    
                    # Handle client in thread pool
                    self.executor.submit(self.handle_client, client_socket, client_addr)
                    
                except OSError:
                    if self.running:
                        print("Error accepting client connection")
                    break
        
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def handle_client(self, client_socket: socket.socket, client_addr):
        """Handle individual client connection"""
        buffer = b""
        
        try:
            client_socket.settimeout(300)  # 5 minute timeout
            
            while self.running:
                # Read data from client
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    buffer += data
                    
                    # Process complete commands
                    while b"\r\n" in buffer:
                        # Find the end of the current command
                        if buffer.startswith(b"*"):
                            # Parse Redis protocol to find command boundary
                            command_end = self._find_command_end(buffer)
                            if command_end == -1:
                                break  # Incomplete command
                            
                            command_data = buffer[:command_end]
                            buffer = buffer[command_end:]
                        else:
                            # Simple string command
                            end_pos = buffer.find(b"\r\n")
                            command_data = buffer[:end_pos + 2]
                            buffer = buffer[end_pos + 2:]
                        
                        # Parse and execute command
                        args = self.protocol.parse_command(command_data)
                        if args:
                            result = self.protocol.execute_command(args)
                            response = self.protocol.format_response(result)
                            client_socket.send(response)
                        else:
                            # Send error for invalid command
                            error_response = b"-ERR Protocol error\r\n"
                            client_socket.send(error_response)
                
                except socket.timeout:
                    print(f"Client {client_addr} timed out")
                    break
                except ConnectionResetError:
                    print(f"Client {client_addr} disconnected")
                    break
        
        except Exception as e:
            print(f"Error handling client {client_addr}: {e}")
        
        finally:
            try:
                client_socket.close()
            except:
                pass
            print(f"Client {client_addr} disconnected")
    
    def _find_command_end(self, buffer: bytes) -> int:
        """Find the end of a Redis protocol command"""
        try:
            if not buffer.startswith(b"*"):
                return -1
            
            # Find first \r\n to get argument count
            first_crlf = buffer.find(b"\r\n")
            if first_crlf == -1:
                return -1
            
            num_args = int(buffer[1:first_crlf])
            pos = first_crlf + 2
            
            # Parse each argument
            for _ in range(num_args):
                # Find argument length line
                if pos >= len(buffer) or buffer[pos] != ord('$'):
                    return -1
                
                arg_len_end = buffer.find(b"\r\n", pos)
                if arg_len_end == -1:
                    return -1
                
                arg_length = int(buffer[pos + 1:arg_len_end])
                pos = arg_len_end + 2
                
                # Skip argument data and its \r\n
                pos += arg_length + 2
                
                if pos > len(buffer):
                    return -1
            
            return pos
        
        except (ValueError, IndexError):
            return -1
    
    def shutdown(self):
        """Shutdown the server"""
        print("Shutting down Redis server...")
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        self.executor.shutdown(wait=True)
        print("Server shutdown complete")

# Example usage
if __name__ == "__main__":
    server = RedisServer(host='localhost', port=6379)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
        server.shutdown()
```

### Step 5: Persistence Layer

Implement data persistence and recovery mechanisms.

```python
import json
import os
import time
import threading
from typing import Dict, Any

class PersistenceManager:
    def __init__(self, storage_engine: StorageEngine, 
                 snapshot_file="dump.rdb", 
                 aof_file="appendonly.aof"):
        self.storage = storage_engine
        self.snapshot_file = snapshot_file
        self.aof_file = aof_file
        self.aof_enabled = True
        
        # Background save thread
        self.save_thread = None
        self.save_interval = 60  # Save every 60 seconds
        
    def start_background_save(self):
        """Start background saving thread"""
        if self.save_thread is None or not self.save_thread.is_alive():
            self.save_thread = threading.Thread(target=self._background_save)
            self.save_thread.daemon = True
            self.save_thread.start()
    
    def _background_save(self):
        """Background thread for periodic saves"""
        while True:
            time.sleep(self.save_interval)
            try:
                self.save_snapshot()
            except Exception as e:
                print(f"Background save error: {e}")
    
    def save_snapshot(self) -> bool:
        """Save current database state to snapshot file"""
        try:
            with self.storage.lock.read_lock():
                # Create a snapshot of current data
                snapshot = {
                    'timestamp': time.time(),
                    'data': {},
                    'types': self.storage.types.copy(),
                    'expiration': self.storage.expiration.copy()
                }
                
                # Serialize data structures
                for key, value in self.storage.data.items():
                    if isinstance(value, RedisString):
                        snapshot['data'][key] = {
                            'type': 'string',
                            'value': value.value
                        }
                    elif isinstance(value, RedisList):
                        snapshot['data'][key] = {
                            'type': 'list',
                            'value': value.items.copy()
                        }
                    elif isinstance(value, RedisSet):
                        snapshot['data'][key] = {
                            'type': 'set',
                            'value': list(value.members)
                        }
                    elif isinstance(value, RedisHash):
                        snapshot['data'][key] = {
                            'type': 'hash',
                            'value': value.fields.copy()
                        }
            
            # Write snapshot to temporary file first
            temp_file = self.snapshot_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, self.snapshot_file)
            print(f"Snapshot saved to {self.snapshot_file}")
            return True
            
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return False
    
    def load_snapshot(self) -> bool:
        """Load database state from snapshot file"""
        if not os.path.exists(self.snapshot_file):
            print(f"Snapshot file {self.snapshot_file} not found")
            return False
        
        try:
            with open(self.snapshot_file, 'r') as f:
                snapshot = json.load(f)
            
            with self.storage.lock.write_lock():
                # Clear existing data
                self.storage.data.clear()
                self.storage.types.clear()
                self.storage.expiration.clear()
                
                # Restore data structures
                for key, item in snapshot.get('data', {}).items():
                    data_type = item['type']
                    value = item['value']
                    
                    if data_type == 'string':
                        self.storage.data[key] = RedisString(value)
                        self.storage.types[key] = DataType.STRING
                    elif data_type == 'list':
                        redis_list = RedisList()
                        redis_list.items = value
                        self.storage.data[key] = redis_list
                        self.storage.types[key] = DataType.LIST
                    elif data_type == 'set':
                        redis_set = RedisSet()
                        redis_set.members = set(value)
                        self.storage.data[key] = redis_set
                        self.storage.types[key] = DataType.SET
                    elif data_type == 'hash':
                        redis_hash = RedisHash()
                        redis_hash.fields = value
                        self.storage.data[key] = redis_hash
                        self.storage.types[key] = DataType.HASH
                
                # Restore expiration times
                current_time = time.time()
                snapshot_time = snapshot.get('timestamp', current_time)
                time_diff = current_time - snapshot_time
                
                for key, expiry_time in snapshot.get('expiration', {}).items():
                    adjusted_expiry = expiry_time + time_diff
                    if adjusted_expiry > current_time:  # Only keep non-expired keys
                        self.storage.expiration[key] = adjusted_expiry
                    else:
                        # Remove expired keys
                        if key in self.storage.data:
                            del self.storage.data[key]
                        if key in self.storage.types:
                            del self.storage.types[key]
            
            print(f"Snapshot loaded from {self.snapshot_file}")
            return True
            
        except Exception as e:
            print(f"Error loading snapshot: {e}")
            return False
    
    def append_to_aof(self, command: List[str]):
        """Append command to AOF file"""
        if not self.aof_enabled:
            return
        
        try:
            with open(self.aof_file, 'a') as f:
                # Write command in Redis protocol format
                f.write(f"*{len(command)}\r\n")
                for arg in command:
                    f.write(f"${len(arg)}\r\n{arg}\r\n")
        except Exception as e:
            print(f"Error writing to AOF: {e}")
    
    def load_aof(self) -> bool:
        """Load and replay commands from AOF file"""
        if not os.path.exists(self.aof_file):
            print(f"AOF file {self.aof_file} not found")
            return False
        
        try:
            protocol = RedisProtocolHandler(self.storage)
            
            with open(self.aof_file, 'rb') as f:
                buffer = b""
                
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    
                    buffer += chunk
                    
                    # Process complete commands
                    while buffer:
                        if not buffer.startswith(b"*"):
                            break
                        
                        command_end = self._find_command_end_in_buffer(buffer)
                        if command_end == -1:
                            break
                        
                        command_data = buffer[:command_end]
                        buffer = buffer[command_end:]
                        
                        # Parse and execute command
                        args = protocol.parse_command(command_data)
                        if args:
                            protocol.execute_command(args)
            
            print(f"AOF loaded from {self.aof_file}")
            return True
            
        except Exception as e:
            print(f"Error loading AOF: {e}")
            return False
    
    def _find_command_end_in_buffer(self, buffer: bytes) -> int:
        """Find the end of a command in buffer (same as in server)"""
        # Implementation same as in RedisServer._find_command_end
        # ... (copy the method here)
        pass
```

## 📚 Tutorials by Language

### Python
- **[Build a Redis Clone in Python](https://charlesleifer.com/blog/building-a-simple-redis-server-with-python/)** - Complete Python implementation
- **[Redis Internals](http://pauladamsmith.com/blog/2011/03/redis_lessons_learned.html)** - Understanding Redis architecture
- **[Build Your Own Redis](https://rohitpaulk.com/articles/redis-0)** - Step-by-step tutorial

### Go
- **[Building Redis in Go](https://www.youtube.com/watch?v=5qBtagAD8kw)** - Video tutorial series
- **[Go Redis Implementation](https://github.com/HDT3213/godis)** - Production-like Go implementation
- **[Simple Redis Clone in Go](https://blog.markvincze.com/implementing-a-simple-redis-clone-in-go/)** - Basic Go tutorial

### Java
- **[Java Redis Implementation](https://github.com/xetorthio/jedis)** - Redis client internals
- **[Building a Redis Server in Java](https://medium.com/@ssaurel/build-a-redis-server-in-java-from-scratch-ec5c6b8c4f0c)** - Java tutorial

### C++
- **[Redis Source Code](https://github.com/redis/redis)** - Official Redis implementation
- **[Understanding Redis Implementation](https://redis.io/topics/internals)** - Official internals documentation

### JavaScript/Node.js
- **[Node.js Redis Clone](https://github.com/luin/ioredis)** - Advanced Node.js client
- **[Building Redis in Node.js](https://medium.com/@stockholmux/building-a-redis-compatible-datastore-with-node-js-streams-b94684a06655)** - Streams-based approach

### Rust
- **[Redis Clone in Rust](https://github.com/tokio-rs/mini-redis)** - Tokio-based implementation
- **[Building a Redis Server in Rust](https://blog.logrocket.com/build-fast-redis-clone-rust/)** - Rust tutorial

## 🏗️ Project Ideas

### Beginner Projects
1. **Basic Key-Value Store** - Simple string operations
2. **List Data Structure** - FIFO/LIFO operations
3. **Memory-only Cache** - LRU eviction policies

### Intermediate Projects
1. **Multi-Type Store** - Strings, lists, sets, hashes
2. **Persistent Storage** - Snapshot and AOF persistence
3. **Protocol Server** - Redis-compatible network protocol

### Advanced Projects
1. **Distributed Store** - Replication and sharding
2. **Cluster Mode** - Consistent hashing and failover
3. **Stream Processing** - Redis Streams implementation

## ⚙️ Core Concepts

### Data Structures
- **Hash Tables**: O(1) key lookup and storage
- **Skip Lists**: Sorted sets implementation
- **Radix Trees**: Memory-efficient string storage
- **LRU Cache**: Least recently used eviction

### Memory Management
- **Object Sharing**: String interning and deduplication
- **Memory Pools**: Efficient allocation strategies
- **Garbage Collection**: Reference counting and cleanup
- **Memory Optimization**: Compact data representations

### Concurrency
- **Read-Write Locks**: Concurrent read operations
- **Lock-Free Structures**: Atomic operations
- **Thread Safety**: Consistent data access
- **Connection Pooling**: Efficient client handling

## 🚀 Performance Optimization

### Data Structure Optimization
- **Compact Representations**: Memory-efficient encoding
- **Lazy Deletion**: Deferred cleanup operations
- **Index Structures**: Fast key lookup methods
- **Cache-Friendly Layout**: CPU cache optimization

### Network Performance
- **Connection Multiplexing**: Single connection efficiency
- **Pipeline Support**: Batch command processing
- **Protocol Optimization**: Minimal parsing overhead
- **Zero-Copy Operations**: Direct memory transfers

### Memory Optimization
- **Memory Fragmentation**: Allocation strategies
- **Reference Counting**: Automatic cleanup
- **Memory Mapping**: File-based storage
- **Compression**: Data size reduction

## 🧪 Testing Strategies

### Unit Testing
- **Data Structure Tests**: Individual component testing
- **Protocol Tests**: Command parsing and formatting
- **Persistence Tests**: Save and load verification
- **Concurrency Tests**: Thread safety validation

### Integration Testing
- **Client Compatibility**: Redis client testing
- **Performance Benchmarks**: Throughput and latency
- **Stress Testing**: High load scenarios
- **Failover Testing**: Recovery mechanisms

### Compliance Testing
- **Redis Protocol**: Command compatibility
- **Data Type Behavior**: Semantic correctness
- **Error Handling**: Proper error responses
- **Memory Consistency**: Data integrity

## 🔗 Additional Resources

### Books
- [Redis in Action](https://www.manning.com/books/redis-in-action) - Comprehensive Redis guide
- [Database Internals](https://www.databass.dev/) - Storage engine fundamentals
- [Designing Data-Intensive Applications](https://dataintensive.net/) - System design patterns

### Online Resources
- [Redis Documentation](https://redis.io/documentation) - Official Redis docs
- [Redis Protocol Specification](https://redis.io/topics/protocol) - Communication protocol
- [Redis Internals](https://redis.io/topics/internals) - Implementation details
- [Redis University](https://university.redis.com/) - Free Redis courses

### Development Communities
- [/r/redis](https://www.reddit.com/r/redis/) - Redis community discussions
- [Redis GitHub](https://github.com/redis/redis) - Source code and issues
- [Redis Discord](https://discord.gg/redis) - Developer community
- [Stack Overflow Redis](https://stackoverflow.com/questions/tagged/redis) - Q&A discussions

---

**Ready to cache?** Start with basic string operations and build up to a full-featured data structure server!