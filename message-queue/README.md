# Build Your Own Message Queue

Create distributed messaging systems from scratch and understand pub/sub patterns, message brokers, and reliable message delivery. Learn about queue management, message routing, and scalable communication patterns.

## 🎯 What You'll Learn

- Message queue architectures and communication patterns
- Publisher-subscriber (pub/sub) messaging systems
- Message persistence and durability guarantees
- Queue management and message routing
- Distributed systems concepts and fault tolerance
- Network protocols for messaging systems

## 📋 Prerequisites

- Understanding of network programming and TCP/IP
- Knowledge of concurrent programming and threading
- Familiarity with distributed systems concepts
- Basic understanding of database storage concepts

## 🏗️ Architecture Overview

Our message queue system consists of these core components:

1. **Message Broker**: Central routing and management system
2. **Topic Manager**: Handles message topics and subscriptions
3. **Queue Storage**: Persistent message storage engine
4. **Connection Manager**: Client connection handling
5. **Delivery System**: Message routing and delivery logic
6. **Replication Layer**: Multi-node consistency and failover

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Publishers  │───▶│    Broker    │───▶│  Subscribers    │
│             │    │              │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
                          │
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Queue     │◄───│    Topic     │───▶│   Delivery      │
│  Storage    │    │   Manager    │    │    System       │
└─────────────┘    └──────────────┘    └─────────────────┘
                          │                       │
┌─────────────┐           │                       ▼
│ Replication │───────────┘            ┌─────────────────┐
│   Layer     │                        │   Connection    │
└─────────────┘                        │    Manager      │
                                       └─────────────────┘
```

## 🚀 Implementation Steps

### Step 1: Message and Topic Definitions

Define the core data structures for messages and topics.

```python
import time
import uuid
import threading
from enum import Enum, auto
from typing import List, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
import json
import pickle

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class DeliveryMode(Enum):
    AT_MOST_ONCE = "at_most_once"      # May lose messages, no duplicates
    AT_LEAST_ONCE = "at_least_once"    # No message loss, may duplicate
    EXACTLY_ONCE = "exactly_once"      # No loss, no duplicates (expensive)

@dataclass
class Message:
    id: str
    topic: str
    payload: bytes
    headers: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    expiry: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if self.expiry is None:
            return False
        return time.time() > self.expiry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'id': self.id,
            'topic': self.topic,
            'payload': self.payload.decode('utf-8', errors='ignore'),
            'headers': self.headers,
            'timestamp': self.timestamp,
            'priority': self.priority.value,
            'expiry': self.expiry,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            id=data['id'],
            topic=data['topic'],
            payload=data['payload'].encode('utf-8'),
            headers=data.get('headers', {}),
            timestamp=data.get('timestamp', time.time()),
            priority=MessagePriority(data.get('priority', MessagePriority.NORMAL.value)),
            expiry=data.get('expiry'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )
    
    def serialize(self) -> bytes:
        """Serialize message to bytes"""
        return pickle.dumps(self.to_dict())
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Message':
        """Deserialize message from bytes"""
        return cls.from_dict(pickle.loads(data))

@dataclass
class Subscription:
    id: str
    topic_pattern: str  # Support wildcards
    consumer_id: str
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    auto_ack: bool = True
    max_unacked: int = 100
    created_at: float = field(default_factory=time.time)
    
    def matches_topic(self, topic: str) -> bool:
        """Check if subscription matches topic (basic wildcard support)"""
        if '*' not in self.topic_pattern:
            return self.topic_pattern == topic
        
        # Simple wildcard matching
        pattern_parts = self.topic_pattern.split('*')
        if len(pattern_parts) == 1:
            return self.topic_pattern == topic
        
        # Check if topic starts and ends with pattern parts
        if topic.startswith(pattern_parts[0]) and topic.endswith(pattern_parts[-1]):
            return True
        
        return False

class Topic:
    def __init__(self, name: str, partitions: int = 1, replication_factor: int = 1):
        self.name = name
        self.partitions = partitions
        self.replication_factor = replication_factor
        self.created_at = time.time()
        
        # Message storage (one deque per partition)
        self.message_queues: List[deque] = [deque() for _ in range(partitions)]
        self.queue_locks: List[threading.RLock] = [threading.RLock() for _ in range(partitions)]
        
        # Subscription management
        self.subscriptions: Set[Subscription] = set()
        self.subscription_lock = threading.RLock()
        
        # Statistics
        self.total_messages = 0
        self.total_bytes = 0
        
    def add_message(self, message: Message, partition: Optional[int] = None) -> bool:
        """Add message to topic"""
        if message.is_expired():
            return False
        
        # Determine partition
        if partition is None:
            partition = hash(message.id) % self.partitions
        
        partition = min(partition, self.partitions - 1)
        
        with self.queue_locks[partition]:
            self.message_queues[partition].append(message)
            self.total_messages += 1
            self.total_bytes += len(message.payload)
        
        return True
    
    def get_messages(self, partition: int, max_messages: int = 10) -> List[Message]:
        """Get messages from partition"""
        if partition >= self.partitions:
            return []
        
        messages = []
        with self.queue_locks[partition]:
            for _ in range(min(max_messages, len(self.message_queues[partition]))):
                if self.message_queues[partition]:
                    message = self.message_queues[partition].popleft()
                    if not message.is_expired():
                        messages.append(message)
        
        return messages
    
    def add_subscription(self, subscription: Subscription):
        """Add subscription to topic"""
        with self.subscription_lock:
            self.subscriptions.add(subscription)
    
    def remove_subscription(self, subscription_id: str):
        """Remove subscription from topic"""
        with self.subscription_lock:
            self.subscriptions = {s for s in self.subscriptions if s.id != subscription_id}
    
    def get_matching_subscriptions(self) -> Set[Subscription]:
        """Get subscriptions that match this topic"""
        with self.subscription_lock:
            return {s for s in self.subscriptions if s.matches_topic(self.name)}
```

### Step 2: Queue Storage and Persistence

Implement persistent storage for messages and recovery.

```python
import os
import struct
from threading import RLock
from typing import Iterator

class MessageStorage:
    """Persistent storage for messages"""
    
    def __init__(self, storage_dir: str = "message_data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.topic_files: Dict[str, 'TopicStorage'] = {}
        self.lock = RLock()
    
    def get_topic_storage(self, topic_name: str) -> 'TopicStorage':
        """Get or create topic storage"""
        with self.lock:
            if topic_name not in self.topic_files:
                self.topic_files[topic_name] = TopicStorage(
                    os.path.join(self.storage_dir, f"{topic_name}.log")
                )
            return self.topic_files[topic_name]
    
    def store_message(self, message: Message) -> bool:
        """Store message persistently"""
        topic_storage = self.get_topic_storage(message.topic)
        return topic_storage.append_message(message)
    
    def load_messages(self, topic: str, from_offset: int = 0) -> Iterator[Message]:
        """Load messages from storage"""
        topic_storage = self.get_topic_storage(topic)
        return topic_storage.read_messages(from_offset)
    
    def close(self):
        """Close all storage files"""
        with self.lock:
            for storage in self.topic_files.values():
                storage.close()

class TopicStorage:
    """Storage for a single topic"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.write_file = open(file_path, 'ab')
        self.read_file = open(file_path, 'rb')
        self.lock = RLock()
        self.offset = 0
        
        # Calculate current offset
        self.write_file.seek(0, 2)  # Seek to end
        self.offset = self.write_file.tell()
    
    def append_message(self, message: Message) -> bool:
        """Append message to log file"""
        try:
            with self.lock:
                serialized_data = message.serialize()
                
                # Write message length (4 bytes) + message data
                length_bytes = struct.pack('I', len(serialized_data))
                self.write_file.write(length_bytes + serialized_data)
                self.write_file.flush()
                
                return True
        except Exception as e:
            print(f"Error storing message: {e}")
            return False
    
    def read_messages(self, from_offset: int = 0) -> Iterator[Message]:
        """Read messages from log file"""
        try:
            with self.lock:
                # Create new read file handle for this operation
                read_file = open(self.file_path, 'rb')
                read_file.seek(from_offset)
                
                while True:
                    # Read message length
                    length_bytes = read_file.read(4)
                    if len(length_bytes) < 4:
                        break
                    
                    message_length = struct.unpack('I', length_bytes)[0]
                    
                    # Read message data
                    message_data = read_file.read(message_length)
                    if len(message_data) < message_length:
                        break
                    
                    try:
                        message = Message.deserialize(message_data)
                        yield message
                    except Exception as e:
                        print(f"Error deserializing message: {e}")
                        break
                
                read_file.close()
        
        except Exception as e:
            print(f"Error reading messages: {e}")
    
    def close(self):
        """Close storage files"""
        if hasattr(self, 'write_file'):
            self.write_file.close()
        if hasattr(self, 'read_file'):
            self.read_file.close()

class MessageIndex:
    """Index for fast message lookups"""
    
    def __init__(self):
        self.topic_offsets: Dict[str, List[int]] = {}
        self.message_id_index: Dict[str, tuple[str, int]] = {}  # message_id -> (topic, offset)
        self.lock = RLock()
    
    def add_message(self, message: Message, offset: int):
        """Add message to index"""
        with self.lock:
            if message.topic not in self.topic_offsets:
                self.topic_offsets[message.topic] = []
            
            self.topic_offsets[message.topic].append(offset)
            self.message_id_index[message.id] = (message.topic, offset)
    
    def find_message_offset(self, message_id: str) -> Optional[tuple[str, int]]:
        """Find message offset by ID"""
        with self.lock:
            return self.message_id_index.get(message_id)
    
    def get_topic_offsets(self, topic: str) -> List[int]:
        """Get all offsets for a topic"""
        with self.lock:
            return self.topic_offsets.get(topic, [])
```

### Step 3: Publisher and Consumer Clients

Create client interfaces for publishing and consuming messages.

```python
import socket
import json
import threading
from typing import Callable, Optional
from queue import Queue, Empty

class MessageQueueClient:
    """Base client for message queue operations"""
    
    def __init__(self, broker_host: str = 'localhost', broker_port: int = 9092):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.lock = threading.RLock()
    
    def connect(self) -> bool:
        """Connect to message broker"""
        try:
            with self.lock:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.broker_host, self.broker_port))
                self.connected = True
                return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        with self.lock:
            if self.socket:
                self.socket.close()
                self.socket = None
            self.connected = False
    
    def send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command to broker and get response"""
        if not self.connected:
            return None
        
        try:
            with self.lock:
                # Send command
                command_json = json.dumps(command) + '\n'
                self.socket.send(command_json.encode())
                
                # Read response
                response_data = b""
                while b'\n' not in response_data:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        return None
                    response_data += chunk
                
                response_json = response_data.decode().strip()
                return json.loads(response_json)
        
        except Exception as e:
            print(f"Communication error: {e}")
            self.connected = False
            return None

class MessageProducer(MessageQueueClient):
    """Message producer/publisher client"""
    
    def __init__(self, broker_host: str = 'localhost', broker_port: int = 9092):
        super().__init__(broker_host, broker_port)
    
    def publish(self, topic: str, payload: bytes, headers: Optional[Dict[str, str]] = None,
                priority: MessagePriority = MessagePriority.NORMAL,
                expiry_seconds: Optional[int] = None) -> Optional[str]:
        """Publish message to topic"""
        message_id = str(uuid.uuid4())
        
        command = {
            'action': 'publish',
            'message': {
                'id': message_id,
                'topic': topic,
                'payload': payload.decode('utf-8', errors='ignore'),
                'headers': headers or {},
                'priority': priority.value,
                'expiry': time.time() + expiry_seconds if expiry_seconds else None
            }
        }
        
        response = self.send_command(command)
        if response and response.get('status') == 'success':
            return message_id
        else:
            print(f"Publish failed: {response.get('error') if response else 'No response'}")
            return None
    
    def publish_json(self, topic: str, data: Dict[str, Any], **kwargs) -> Optional[str]:
        """Publish JSON data as message"""
        payload = json.dumps(data).encode()
        return self.publish(topic, payload, **kwargs)
    
    def publish_text(self, topic: str, text: str, **kwargs) -> Optional[str]:
        """Publish text message"""
        payload = text.encode()
        return self.publish(topic, payload, **kwargs)

class MessageConsumer(MessageQueueClient):
    """Message consumer/subscriber client"""
    
    def __init__(self, consumer_id: str, broker_host: str = 'localhost', broker_port: int = 9092):
        super().__init__(broker_host, broker_port)
        self.consumer_id = consumer_id
        self.subscriptions: Dict[str, Subscription] = {}
        self.message_handlers: Dict[str, Callable[[Message], bool]] = {}
        self.running = False
        self.consumer_thread: Optional[threading.Thread] = None
        self.message_queue: Queue = Queue()
    
    def subscribe(self, topic_pattern: str, 
                 delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE,
                 message_handler: Optional[Callable[[Message], bool]] = None) -> bool:
        """Subscribe to topic pattern"""
        subscription_id = str(uuid.uuid4())
        subscription = Subscription(
            id=subscription_id,
            topic_pattern=topic_pattern,
            consumer_id=self.consumer_id,
            delivery_mode=delivery_mode
        )
        
        command = {
            'action': 'subscribe',
            'subscription': {
                'id': subscription.id,
                'topic_pattern': subscription.topic_pattern,
                'consumer_id': subscription.consumer_id,
                'delivery_mode': subscription.delivery_mode.value
            }
        }
        
        response = self.send_command(command)
        if response and response.get('status') == 'success':
            self.subscriptions[topic_pattern] = subscription
            if message_handler:
                self.message_handlers[topic_pattern] = message_handler
            return True
        else:
            print(f"Subscribe failed: {response.get('error') if response else 'No response'}")
            return False
    
    def unsubscribe(self, topic_pattern: str) -> bool:
        """Unsubscribe from topic pattern"""
        if topic_pattern not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[topic_pattern]
        command = {
            'action': 'unsubscribe',
            'subscription_id': subscription.id
        }
        
        response = self.send_command(command)
        if response and response.get('status') == 'success':
            del self.subscriptions[topic_pattern]
            self.message_handlers.pop(topic_pattern, None)
            return True
        return False
    
    def start_consuming(self):
        """Start consuming messages in background thread"""
        if self.running:
            return
        
        self.running = True
        self.consumer_thread = threading.Thread(target=self._consume_loop)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
    
    def stop_consuming(self):
        """Stop consuming messages"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5.0)
    
    def _consume_loop(self):
        """Main consumption loop"""
        while self.running and self.connected:
            try:
                # Request messages
                command = {
                    'action': 'consume',
                    'consumer_id': self.consumer_id,
                    'max_messages': 10
                }
                
                response = self.send_command(command)
                if response and response.get('status') == 'success':
                    messages_data = response.get('messages', [])
                    
                    for message_data in messages_data:
                        message = Message.from_dict(message_data)
                        self._handle_message(message)
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"Consume loop error: {e}")
                time.sleep(1.0)
    
    def _handle_message(self, message: Message):
        """Handle received message"""
        # Find matching handler
        handler = None
        for pattern, pattern_handler in self.message_handlers.items():
            if pattern == message.topic or ('*' in pattern):  # Simplified matching
                handler = pattern_handler
                break
        
        if handler:
            try:
                # Call handler
                success = handler(message)
                
                # Send acknowledgment if processing succeeded
                if success:
                    self.acknowledge_message(message.id)
                else:
                    self.reject_message(message.id)
            except Exception as e:
                print(f"Message handler error: {e}")
                self.reject_message(message.id)
        else:
            # Put in queue for manual processing
            self.message_queue.put(message)
    
    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge message processing"""
        command = {
            'action': 'ack',
            'message_id': message_id,
            'consumer_id': self.consumer_id
        }
        
        response = self.send_command(command)
        return response and response.get('status') == 'success'
    
    def reject_message(self, message_id: str) -> bool:
        """Reject message (may be redelivered)"""
        command = {
            'action': 'reject',
            'message_id': message_id,
            'consumer_id': self.consumer_id
        }
        
        response = self.send_command(command)
        return response and response.get('status') == 'success'
    
    def get_message(self, timeout: float = 1.0) -> Optional[Message]:
        """Get message from queue (blocking)"""
        try:
            return self.message_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_message_nowait(self) -> Optional[Message]:
        """Get message from queue (non-blocking)"""
        try:
            return self.message_queue.get_nowait()
        except Empty:
            return None
```

### Step 4: Message Broker Server

Implement the central message broker that manages topics and routing.

```python
import socketserver
import json
from threading import Thread
from collections import defaultdict

class MessageBroker:
    """Central message broker"""
    
    def __init__(self, port: int = 9092, persistence_enabled: bool = True):
        self.port = port
        self.persistence_enabled = persistence_enabled
        
        # Core components
        self.topics: Dict[str, Topic] = {}
        self.topic_lock = threading.RLock()
        
        self.subscriptions: Dict[str, Subscription] = {}
        self.consumer_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # consumer_id -> subscription_ids
        self.subscription_lock = threading.RLock()
        
        # Message storage
        if persistence_enabled:
            self.storage = MessageStorage()
        else:
            self.storage = None
        
        # Delivery tracking
        self.pending_messages: Dict[str, Dict[str, Message]] = defaultdict(dict)  # consumer_id -> message_id -> message
        self.delivered_messages: Dict[str, Set[str]] = defaultdict(set)  # consumer_id -> message_ids
        self.delivery_lock = threading.RLock()
        
        # Background tasks
        self.running = False
        self.cleanup_thread: Optional[Thread] = None
        
        # Statistics
        self.stats = {
            'messages_published': 0,
            'messages_delivered': 0,
            'total_topics': 0,
            'total_subscriptions': 0
        }
    
    def start(self):
        """Start the message broker"""
        self.running = True
        
        # Start background cleanup
        self.cleanup_thread = Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
        
        # Start TCP server
        server = socketserver.ThreadingTCPServer(('localhost', self.port), MessageBrokerHandler)
        server.broker = self
        
        print(f"Message broker started on port {self.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down message broker...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the message broker"""
        self.running = False
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5.0)
        
        if self.storage:
            self.storage.close()
    
    def create_topic(self, topic_name: str, partitions: int = 1, replication_factor: int = 1) -> bool:
        """Create a new topic"""
        with self.topic_lock:
            if topic_name in self.topics:
                return False  # Topic already exists
            
            self.topics[topic_name] = Topic(topic_name, partitions, replication_factor)
            self.stats['total_topics'] += 1
            return True
    
    def publish_message(self, message: Message) -> bool:
        """Publish message to topic"""
        # Create topic if it doesn't exist
        if message.topic not in self.topics:
            self.create_topic(message.topic)
        
        with self.topic_lock:
            topic = self.topics[message.topic]
            success = topic.add_message(message)
            
            if success:
                self.stats['messages_published'] += 1
                
                # Persist message if enabled
                if self.storage:
                    self.storage.store_message(message)
                
                # Trigger message delivery
                self._deliver_message_to_subscribers(message)
            
            return success
    
    def subscribe_consumer(self, subscription: Subscription) -> bool:
        """Subscribe consumer to topic pattern"""
        with self.subscription_lock:
            self.subscriptions[subscription.id] = subscription
            self.consumer_subscriptions[subscription.consumer_id].add(subscription.id)
            self.stats['total_subscriptions'] += 1
            
            # Add subscription to matching topics
            with self.topic_lock:
                for topic_name, topic in self.topics.items():
                    if subscription.matches_topic(topic_name):
                        topic.add_subscription(subscription)
            
            return True
    
    def unsubscribe_consumer(self, subscription_id: str) -> bool:
        """Unsubscribe consumer"""
        with self.subscription_lock:
            if subscription_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            # Remove from consumer subscriptions
            self.consumer_subscriptions[subscription.consumer_id].discard(subscription_id)
            
            # Remove from topics
            with self.topic_lock:
                for topic in self.topics.values():
                    topic.remove_subscription(subscription_id)
            
            del self.subscriptions[subscription_id]
            self.stats['total_subscriptions'] -= 1
            return True
    
    def consume_messages(self, consumer_id: str, max_messages: int = 10) -> List[Message]:
        """Get messages for consumer"""
        messages = []
        
        # Get consumer subscriptions
        with self.subscription_lock:
            subscription_ids = self.consumer_subscriptions.get(consumer_id, set())
            subscriptions = [self.subscriptions[sid] for sid in subscription_ids 
                           if sid in self.subscriptions]
        
        # Collect messages from all subscribed topics
        for subscription in subscriptions:
            with self.topic_lock:
                for topic_name, topic in self.topics.items():
                    if subscription.matches_topic(topic_name):
                        # Get messages from all partitions
                        for partition in range(topic.partitions):
                            partition_messages = topic.get_messages(partition, 
                                                                  max_messages - len(messages))
                            messages.extend(partition_messages)
                            
                            if len(messages) >= max_messages:
                                break
                    
                    if len(messages) >= max_messages:
                        break
        
        # Track pending messages for acknowledgment
        with self.delivery_lock:
            for message in messages:
                self.pending_messages[consumer_id][message.id] = message
        
        self.stats['messages_delivered'] += len(messages)
        return messages
    
    def acknowledge_message(self, consumer_id: str, message_id: str) -> bool:
        """Acknowledge message processing"""
        with self.delivery_lock:
            if (consumer_id in self.pending_messages and 
                message_id in self.pending_messages[consumer_id]):
                
                del self.pending_messages[consumer_id][message_id]
                self.delivered_messages[consumer_id].add(message_id)
                return True
        
        return False
    
    def reject_message(self, consumer_id: str, message_id: str) -> bool:
        """Reject message (re-queue for delivery)"""
        with self.delivery_lock:
            if (consumer_id in self.pending_messages and 
                message_id in self.pending_messages[consumer_id]):
                
                message = self.pending_messages[consumer_id][message_id]
                del self.pending_messages[consumer_id][message_id]
                
                # Increment retry count
                message.retry_count += 1
                
                # Re-queue if retries available
                if message.retry_count <= message.max_retries:
                    self._requeue_message(message)
                    return True
        
        return False
    
    def _deliver_message_to_subscribers(self, message: Message):
        """Deliver message to all matching subscribers"""
        # This is handled when consumers call consume_messages
        # In a real implementation, you might want to push messages
        # to consumers or use a more sophisticated delivery mechanism
        pass
    
    def _requeue_message(self, message: Message):
        """Re-queue message for delivery"""
        if message.topic in self.topics:
            with self.topic_lock:
                self.topics[message.topic].add_message(message)
    
    def _cleanup_loop(self):
        """Background cleanup of expired messages and pending deliveries"""
        while self.running:
            try:
                # Clean up expired messages
                current_time = time.time()
                
                with self.topic_lock:
                    for topic in self.topics.values():
                        for partition in range(topic.partitions):
                            with topic.queue_locks[partition]:
                                # Remove expired messages from front of queue
                                queue = topic.message_queues[partition]
                                while queue and queue[0].is_expired():
                                    queue.popleft()
                
                # Clean up old pending messages (timeout after 5 minutes)
                timeout = 5 * 60  # 5 minutes
                with self.delivery_lock:
                    for consumer_id in list(self.pending_messages.keys()):
                        expired_messages = []
                        for message_id, message in self.pending_messages[consumer_id].items():
                            if current_time - message.timestamp > timeout:
                                expired_messages.append(message_id)
                        
                        for message_id in expired_messages:
                            message = self.pending_messages[consumer_id][message_id]
                            del self.pending_messages[consumer_id][message_id]
                            
                            # Re-queue if retries available
                            if message.retry_count < message.max_retries:
                                message.retry_count += 1
                                self._requeue_message(message)
                
                time.sleep(30)  # Run cleanup every 30 seconds
                
            except Exception as e:
                print(f"Cleanup error: {e}")
                time.sleep(30)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics"""
        with self.topic_lock, self.subscription_lock:
            stats = self.stats.copy()
            stats.update({
                'topics': {name: {
                    'partitions': topic.partitions,
                    'total_messages': topic.total_messages,
                    'total_bytes': topic.total_bytes,
                    'subscriptions': len(topic.subscriptions)
                } for name, topic in self.topics.items()},
                'active_consumers': len(self.consumer_subscriptions)
            })
        
        return stats

class MessageBrokerHandler(socketserver.BaseRequestHandler):
    """TCP handler for broker client connections"""
    
    def handle(self):
        """Handle client connection"""
        print(f"Client connected: {self.client_address}")
        
        try:
            while True:
                # Read command
                data = b""
                while b'\n' not in data:
                    chunk = self.request.recv(1024)
                    if not chunk:
                        return
                    data += chunk
                
                command_json = data.decode().strip()
                if not command_json:
                    continue
                
                try:
                    command = json.loads(command_json)
                    response = self._process_command(command)
                    
                    # Send response
                    response_json = json.dumps(response) + '\n'
                    self.request.send(response_json.encode())
                
                except json.JSONDecodeError:
                    error_response = json.dumps({
                        'status': 'error',
                        'error': 'Invalid JSON'
                    }) + '\n'
                    self.request.send(error_response.encode())
        
        except Exception as e:
            print(f"Handler error: {e}")
        finally:
            print(f"Client disconnected: {self.client_address}")
    
    def _process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process client command"""
        action = command.get('action')
        broker = self.server.broker
        
        try:
            if action == 'publish':
                message_data = command['message']
                message = Message.from_dict(message_data)
                success = broker.publish_message(message)
                
                return {
                    'status': 'success' if success else 'error',
                    'error': 'Failed to publish message' if not success else None
                }
            
            elif action == 'subscribe':
                subscription_data = command['subscription']
                subscription = Subscription(
                    id=subscription_data['id'],
                    topic_pattern=subscription_data['topic_pattern'],
                    consumer_id=subscription_data['consumer_id'],
                    delivery_mode=DeliveryMode(subscription_data.get('delivery_mode', 'at_least_once'))
                )
                success = broker.subscribe_consumer(subscription)
                
                return {
                    'status': 'success' if success else 'error',
                    'error': 'Failed to subscribe' if not success else None
                }
            
            elif action == 'unsubscribe':
                subscription_id = command['subscription_id']
                success = broker.unsubscribe_consumer(subscription_id)
                
                return {
                    'status': 'success' if success else 'error',
                    'error': 'Failed to unsubscribe' if not success else None
                }
            
            elif action == 'consume':
                consumer_id = command['consumer_id']
                max_messages = command.get('max_messages', 10)
                messages = broker.consume_messages(consumer_id, max_messages)
                
                return {
                    'status': 'success',
                    'messages': [msg.to_dict() for msg in messages]
                }
            
            elif action == 'ack':
                consumer_id = command['consumer_id']
                message_id = command['message_id']
                success = broker.acknowledge_message(consumer_id, message_id)
                
                return {
                    'status': 'success' if success else 'error',
                    'error': 'Failed to acknowledge message' if not success else None
                }
            
            elif action == 'reject':
                consumer_id = command['consumer_id']
                message_id = command['message_id']
                success = broker.reject_message(consumer_id, message_id)
                
                return {
                    'status': 'success' if success else 'error',
                    'error': 'Failed to reject message' if not success else None
                }
            
            elif action == 'stats':
                return {
                    'status': 'success',
                    'stats': broker.get_stats()
                }
            
            else:
                return {
                    'status': 'error',
                    'error': f'Unknown action: {action}'
                }
        
        except KeyError as e:
            return {
                'status': 'error',
                'error': f'Missing required field: {e}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Internal error: {str(e)}'
            }

# Example usage and testing
def example_usage():
    """Example of how to use the message queue system"""
    
    # Start broker in background thread
    broker_thread = Thread(target=lambda: MessageBroker().start())
    broker_thread.daemon = True
    broker_thread.start()
    
    time.sleep(1)  # Wait for broker to start
    
    # Create producer
    producer = MessageProducer()
    if not producer.connect():
        print("Failed to connect producer")
        return
    
    # Create consumer
    consumer = MessageConsumer("test-consumer")
    if not consumer.connect():
        print("Failed to connect consumer")
        return
    
    # Define message handler
    def message_handler(message: Message) -> bool:
        print(f"Received message: {message.payload.decode()}")
        return True
    
    # Subscribe to topic
    consumer.subscribe("test.topic.*", message_handler=message_handler)
    consumer.start_consuming()
    
    # Publish some messages
    for i in range(5):
        message_text = f"Hello World {i}!"
        message_id = producer.publish_text("test.topic.example", message_text)
        print(f"Published message {message_id}: {message_text}")
        time.sleep(1)
    
    # Let consumer process messages
    time.sleep(5)
    
    # Cleanup
    consumer.stop_consuming()
    producer.disconnect()
    consumer.disconnect()

if __name__ == "__main__":
    example_usage()
```

## 📚 Tutorials by Language

### Python
- **[Build a Message Queue with Python](https://python.plainenglish.io/building-a-message-queue-using-python-3c9b02a5b9e1)** - Complete Python implementation
- **[RabbitMQ Python Tutorial](https://www.rabbitmq.com/tutorials/tutorial-one-python.html)** - Official RabbitMQ Python guide
- **[Apache Kafka with Python](https://kafka-python.readthedocs.io/)** - Kafka client library tutorial

### Go
- **[Building a Message Queue in Go](https://medium.com/@petomalina/building-a-message-queue-in-golang-3d67d3494c0a)** - Go implementation tutorial
- **[NSQ Go Client](https://github.com/nsqio/go-nsq)** - Distributed messaging platform
- **[NATS Go Client](https://github.com/nats-io/nats.go)** - High-performance messaging system

### Java
- **[Build a Message Queue in Java](https://www.baeldung.com/java-message-queues)** - Java implementation guide
- **[ActiveMQ Tutorial](https://activemq.apache.org/getting-started)** - Apache ActiveMQ guide
- **[Apache Kafka Java](https://kafka.apache.org/documentation/#producerapi)** - Kafka producer/consumer APIs

### JavaScript/Node.js
- **[Node.js Message Queue](https://blog.logrocket.com/message-queues-node-js/)** - Building queues with Node.js
- **[Redis Pub/Sub with Node.js](https://redis.io/topics/pubsub)** - Redis-based messaging
- **[Bull Queue Tutorial](https://github.com/OptimalBits/bull)** - Job and message queue for Node.js

### C#
- **[Message Queuing in .NET](https://docs.microsoft.com/en-us/dotnet/api/system.messaging)** - .NET Framework messaging
- **[Azure Service Bus](https://docs.microsoft.com/en-us/azure/service-bus-messaging/)** - Cloud messaging service
- **[RabbitMQ .NET Client](https://www.rabbitmq.com/dotnet.html)** - RabbitMQ for .NET

### Rust
- **[Message Queue in Rust](https://github.com/tokio-rs/tokio)** - Async messaging with Tokio
- **[lapin - RabbitMQ Client](https://github.com/CleverCloud/lapin)** - RabbitMQ client for Rust
- **[Distributed Systems in Rust](https://github.com/pingcap/talent-plan)** - TiKV distributed systems course

### C++
- **[ZeroMQ C++ Guide](http://zguide.zeromq.org/cpp:all)** - ZeroMQ messaging library
- **[Apache Kafka C++ Client](https://github.com/edenhill/librdkafka)** - High-performance Kafka client
- **[Message Passing in C++](https://www.boost.org/doc/libs/1_75_0/doc/html/interprocess.html)** - Boost.Interprocess

## 🏗️ Project Ideas

### Beginner Projects
1. **Simple Pub/Sub** - Basic publisher-subscriber pattern
2. **Task Queue** - Background job processing system
3. **Event Bus** - In-process event messaging

### Intermediate Projects
1. **Persistent Message Queue** - Durable message storage
2. **Topic-Based Routing** - Advanced message routing
3. **Dead Letter Queue** - Failed message handling

### Advanced Projects
1. **Distributed Message Broker** - Multi-node clustering
2. **Stream Processing** - Real-time data processing
3. **Message Queue Cluster** - High availability and sharding

## ⚙️ Core Concepts

### Messaging Patterns
- **Point-to-Point**: Direct message delivery between sender and receiver
- **Publish-Subscribe**: One-to-many message broadcasting
- **Request-Reply**: Synchronous communication pattern
- **Message Routing**: Content-based and topic-based routing

### Delivery Guarantees
- **At-Most-Once**: Fire-and-forget, possible message loss
- **At-Least-Once**: Guaranteed delivery, possible duplicates
- **Exactly-Once**: No loss, no duplicates (complex to implement)
- **Ordering Guarantees**: FIFO and partial ordering

### Persistence and Durability
- **Message Persistence**: Storing messages on disk
- **Acknowledgments**: Confirming message processing
- **Replication**: Data redundancy across nodes
- **Recovery**: Restoring messages after failures

## 🚀 Performance Optimization

### Throughput Optimization
- **Batching**: Processing multiple messages together
- **Pipelining**: Overlapping network operations
- **Connection Pooling**: Reusing network connections
- **Asynchronous Processing**: Non-blocking I/O operations

### Scalability Techniques
- **Partitioning**: Distributing messages across partitions
- **Load Balancing**: Distributing consumers across partitions
- **Horizontal Scaling**: Adding more broker nodes
- **Caching**: In-memory message buffering

### Latency Optimization
- **Zero-Copy**: Avoiding unnecessary data copying
- **Memory Mapping**: Direct file system access
- **Network Optimization**: TCP tuning and batching
- **Local Buffers**: Reducing network round-trips

## 🧪 Testing Strategies

### Unit Testing
- **Message Serialization**: Encoding/decoding validation
- **Topic Management**: Subscription and routing tests
- **Storage Layer**: Persistence and recovery testing
- **Client Libraries**: Producer and consumer functionality

### Integration Testing
- **End-to-End Messaging**: Complete workflow testing
- **Failure Scenarios**: Network partitions and node failures
- **Performance Testing**: Throughput and latency benchmarks
- **Compatibility Testing**: Multiple client versions

### Distributed System Testing
- **Chaos Engineering**: Random failure injection
- **Network Partitions**: Split-brain scenarios
- **Data Consistency**: Replication and synchronization
- **Failover Testing**: Leader election and recovery

## 🔗 Additional Resources

### Books
- [Designing Data-Intensive Applications](https://dataintensive.net/) - Distributed systems fundamentals
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices/9781491950340/) - Service communication patterns
- [Kafka: The Definitive Guide](https://www.oreilly.com/library/view/kafka-the-definitive/9781491936153/) - Apache Kafka deep dive
- [RabbitMQ in Action](https://www.manning.com/books/rabbitmq-in-action) - Comprehensive RabbitMQ guide

### Online Resources
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/) - Official Kafka docs
- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html) - Getting started with RabbitMQ
- [Redis Pub/Sub](https://redis.io/topics/pubsub) - Redis messaging capabilities
- [NATS Documentation](https://docs.nats.io/) - High-performance messaging system

### Message Queue Systems
- [Apache Kafka](https://kafka.apache.org/) - Distributed streaming platform
- [RabbitMQ](https://www.rabbitmq.com/) - Feature-rich message broker
- [Apache Pulsar](https://pulsar.apache.org/) - Cloud-native messaging
- [NATS](https://nats.io/) - Simple, secure, and performant messaging

### Development Communities
- [/r/messagingqueue](https://www.reddit.com/r/messagingqueue/) - Message queue discussions
- [Apache Kafka Community](https://kafka.apache.org/community) - Kafka development and support
- [RabbitMQ Community](https://www.rabbitmq.com/community.html) - RabbitMQ forums and support
- [Cloud Native Computing Foundation](https://www.cncf.io/) - Cloud-native messaging projects

---

**Ready to queue?** Start with a simple pub/sub system and build up to a distributed message broker!