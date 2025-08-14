# Build Your Own Database

Create a relational database management system from scratch and understand how databases store, index, and query data. You'll implement tables, B-tree indexes, SQL parsing, and transaction management.

## 🎯 What You'll Learn

- How databases store data on disk (pages, records, files)
- B-tree data structures for efficient indexing
- SQL query parsing and execution planning
- Transaction management and ACID properties
- Buffer management and caching strategies
- Concurrency control and locking mechanisms

## 📋 Prerequisites

- Understanding of file I/O and binary data formats
- Knowledge of tree data structures (especially B-trees)
- Basic understanding of SQL syntax
- Familiarity with parsing concepts (lexing, parsing)

## 🏗️ Architecture Overview

Our database consists of these core components:

1. **Storage Engine**: Manages data files and pages on disk
2. **B-tree Index**: Efficient data structure for fast lookups
3. **Query Parser**: Converts SQL into executable plans
4. **Query Executor**: Executes query plans and returns results
5. **Transaction Manager**: Handles ACID transactions
6. **Buffer Pool**: Caches frequently accessed pages in memory

```
SQL Query → Parser → Planner → Executor → Storage Engine
    ↑                                           ↓
 Results ← Formatter ← Record Set ← B-tree Index → Disk Files
```

## 🚀 Implementation Steps

### Step 1: Storage Engine and Page Management

Start with the foundation - how to store data on disk in fixed-size pages.

**Theory**: Databases store data in fixed-size pages (typically 4KB or 8KB) to efficiently manage disk I/O and memory usage. Each page contains multiple records.

```python
import os
import struct
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class PageType(Enum):
    TABLE_LEAF = 1
    TABLE_INTERIOR = 2
    INDEX_LEAF = 3
    INDEX_INTERIOR = 4

class Page:
    """Represents a database page (fixed size block of data)"""
    
    PAGE_SIZE = 4096  # 4KB pages
    
    def __init__(self, page_num: int, page_type: PageType):
        self.page_num = page_num
        self.page_type = page_type
        self.data = bytearray(self.PAGE_SIZE)
        self.is_dirty = False
        
        # Initialize page header
        self._write_header()
    
    def _write_header(self):
        """Write page header to data"""
        # Page header: [page_type(1), num_records(2), free_space_offset(2)]
        struct.pack_into('<BHH', self.data, 0, 
                        self.page_type.value, 0, self.PAGE_SIZE - 5)
    
    def get_num_records(self) -> int:
        """Get number of records in page"""
        return struct.unpack_from('<H', self.data, 1)[0]
    
    def set_num_records(self, count: int):
        """Set number of records in page"""
        struct.pack_into('<H', self.data, 1, count)
        self.is_dirty = True
    
    def get_free_space_offset(self) -> int:
        """Get offset of free space"""
        return struct.unpack_from('<H', self.data, 3)[0]
    
    def set_free_space_offset(self, offset: int):
        """Set offset of free space"""
        struct.pack_into('<H', self.data, 3, offset)
        self.is_dirty = True

class Record:
    """Represents a database record"""
    
    def __init__(self, values: List[Any]):
        self.values = values
    
    def serialize(self) -> bytes:
        """Serialize record to bytes"""
        result = bytearray()
        
        # Record header: number of fields
        result.extend(struct.pack('<H', len(self.values)))
        
        # Field offsets (for variable-length fields)
        field_offsets = []
        current_offset = 2 + 2 * len(self.values)  # Header + offset table
        
        for value in self.values:
            field_offsets.append(current_offset)
            if isinstance(value, str):
                current_offset += len(value.encode('utf-8'))
            elif isinstance(value, int):
                current_offset += 8
            elif isinstance(value, float):
                current_offset += 8
            elif value is None:
                current_offset += 0
        
        # Write field offsets
        for offset in field_offsets:
            result.extend(struct.pack('<H', offset))
        
        # Write field values
        for value in self.values:
            if value is None:
                continue  # NULL values take no space
            elif isinstance(value, str):
                result.extend(value.encode('utf-8'))
            elif isinstance(value, int):
                result.extend(struct.pack('<q', value))  # 8-byte signed int
            elif isinstance(value, float):
                result.extend(struct.pack('<d', value))  # 8-byte double
        
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Record':
        """Deserialize record from bytes"""
        if len(data) < 2:
            raise ValueError("Invalid record data")
        
        num_fields = struct.unpack_from('<H', data, 0)[0]
        
        # Read field offsets
        field_offsets = []
        for i in range(num_fields):
            offset = struct.unpack_from('<H', data, 2 + i * 2)[0]
            field_offsets.append(offset)
        
        # Add end offset for last field
        field_offsets.append(len(data))
        
        # Extract field values
        values = []
        for i in range(num_fields):
            start = field_offsets[i]
            end = field_offsets[i + 1]
            
            if start == end:
                values.append(None)  # NULL value
            elif end - start == 8:
                # Could be int or float, assume int for simplicity
                value = struct.unpack_from('<q', data, start)[0]
                values.append(value)
            else:
                # String value
                value = data[start:end].decode('utf-8')
                values.append(value)
        
        return cls(values)

class StorageEngine:
    """Manages database files and pages"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.file_handle = None
        self.page_cache: Dict[int, Page] = {}
        self.next_page_num = 0
        
        self._open_db()
    
    def _open_db(self):
        """Open or create database file"""
        is_new = not os.path.exists(self.db_file)
        self.file_handle = open(self.db_file, 'rb+' if not is_new else 'wb+')
        
        if is_new:
            # Initialize new database file
            self._initialize_db()
        else:
            # Read existing database metadata
            self._read_db_metadata()
    
    def _initialize_db(self):
        """Initialize a new database file"""
        # Write database header
        header = struct.pack('<4sII', b'MyDB', 1, 0)  # Magic, version, num_pages
        self.file_handle.write(header)
        self.file_handle.flush()
        self.next_page_num = 0
    
    def _read_db_metadata(self):
        """Read database metadata from file"""
        self.file_handle.seek(0)
        header = self.file_handle.read(12)
        if len(header) < 12:
            raise ValueError("Invalid database file")
        
        magic, version, num_pages = struct.unpack('<4sII', header)
        if magic != b'MyDB':
            raise ValueError("Not a valid MyDB database file")
        
        self.next_page_num = num_pages
    
    def allocate_page(self, page_type: PageType) -> Page:
        """Allocate a new page"""
        page = Page(self.next_page_num, page_type)
        self.page_cache[self.next_page_num] = page
        self.next_page_num += 1
        
        # Update database header
        self._update_page_count()
        
        return page
    
    def get_page(self, page_num: int) -> Optional[Page]:
        """Get a page from cache or disk"""
        if page_num in self.page_cache:
            return self.page_cache[page_num]
        
        if page_num >= self.next_page_num:
            return None
        
        # Read page from disk
        offset = 12 + page_num * Page.PAGE_SIZE  # Skip header
        self.file_handle.seek(offset)
        data = self.file_handle.read(Page.PAGE_SIZE)
        
        if len(data) < Page.PAGE_SIZE:
            return None
        
        # Create page object
        page_type_val = struct.unpack_from('<B', data, 0)[0]
        page_type = PageType(page_type_val)
        
        page = Page(page_num, page_type)
        page.data = bytearray(data)
        page.is_dirty = False
        
        self.page_cache[page_num] = page
        return page
    
    def write_page(self, page: Page):
        """Write page to disk"""
        if not page.is_dirty:
            return
        
        offset = 12 + page.page_num * Page.PAGE_SIZE
        self.file_handle.seek(offset)
        self.file_handle.write(page.data)
        self.file_handle.flush()
        page.is_dirty = False
    
    def _update_page_count(self):
        """Update page count in database header"""
        self.file_handle.seek(8)  # Offset to num_pages field
        self.file_handle.write(struct.pack('<I', self.next_page_num))
        self.file_handle.flush()
    
    def close(self):
        """Close database and flush all pages"""
        for page in self.page_cache.values():
            if page.is_dirty:
                self.write_page(page)
        
        if self.file_handle:
            self.file_handle.close()

# Test the storage engine
def test_storage():
    """Test storage engine functionality"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_file = tmp.name
    
    try:
        # Test database creation and page allocation
        storage = StorageEngine(db_file)
        
        # Allocate a page
        page = storage.allocate_page(PageType.TABLE_LEAF)
        print(f"Allocated page {page.page_num}")
        
        # Test record serialization
        record = Record(["Alice", 25, "Engineer"])
        serialized = record.serialize()
        print(f"Serialized record: {len(serialized)} bytes")
        
        # Test deserialization
        deserialized = Record.deserialize(serialized)
        print(f"Deserialized values: {deserialized.values}")
        
        storage.close()
        print("Storage engine test passed!")
        
    finally:
        if os.path.exists(db_file):
            os.unlink(db_file)

if __name__ == "__main__":
    test_storage()
```

### Step 2: B-tree Index Implementation

Implement B-tree data structure for efficient data indexing and retrieval.

**Theory**: B-trees are self-balancing tree data structures that maintain sorted data and allow searches, insertions, and deletions in logarithmic time. They're perfect for database indexes.

```python
from typing import Tuple, List, Any, Optional

class BTreeNode:
    """A node in a B-tree"""
    
    def __init__(self, is_leaf: bool = False, max_keys: int = 4):
        self.is_leaf = is_leaf
        self.keys: List[Any] = []
        self.values: List[Any] = []  # For leaf nodes
        self.children: List['BTreeNode'] = []  # For internal nodes
        self.max_keys = max_keys
    
    def is_full(self) -> bool:
        """Check if node is full"""
        return len(self.keys) >= self.max_keys
    
    def insert_non_full(self, key: Any, value: Any = None):
        """Insert key/value into non-full node"""
        i = len(self.keys) - 1
        
        if self.is_leaf:
            # Insert into leaf node
            self.keys.append(None)
            self.values.append(None)
            
            while i >= 0 and self.keys[i] > key:
                self.keys[i + 1] = self.keys[i]
                self.values[i + 1] = self.values[i]
                i -= 1
            
            self.keys[i + 1] = key
            self.values[i + 1] = value
        else:
            # Find child to insert into
            while i >= 0 and self.keys[i] > key:
                i -= 1
            i += 1
            
            if self.children[i].is_full():
                # Split child if full
                self.split_child(i)
                if self.keys[i] < key:
                    i += 1
            
            self.children[i].insert_non_full(key, value)
    
    def split_child(self, index: int):
        """Split a full child node"""
        full_child = self.children[index]
        new_child = BTreeNode(full_child.is_leaf, full_child.max_keys)
        
        mid = full_child.max_keys // 2
        
        # Move half the keys to new child
        new_child.keys = full_child.keys[mid + 1:]
        full_child.keys = full_child.keys[:mid]
        
        if full_child.is_leaf:
            new_child.values = full_child.values[mid + 1:]
            full_child.values = full_child.values[:mid]
        else:
            new_child.children = full_child.children[mid + 1:]
            full_child.children = full_child.children[:mid + 1]
        
        # Insert new child into parent
        self.children.insert(index + 1, new_child)
        self.keys.insert(index, full_child.keys[mid])
        if full_child.is_leaf:
            # For leaf nodes, we need to store the value too
            self.values.insert(index, full_child.values[mid] if hasattr(full_child, 'values') else None)
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the B-tree"""
        i = 0
        while i < len(self.keys) and key > self.keys[i]:
            i += 1
        
        if i < len(self.keys) and key == self.keys[i]:
            if self.is_leaf:
                return self.values[i]
            else:
                return key  # Found in internal node
        
        if self.is_leaf:
            return None  # Not found
        
        return self.children[i].search(key)

class BTree:
    """B-tree implementation for database indexing"""
    
    def __init__(self, max_keys: int = 4):
        self.root = BTreeNode(is_leaf=True, max_keys=max_keys)
        self.max_keys = max_keys
    
    def insert(self, key: Any, value: Any = None):
        """Insert key/value pair into B-tree"""
        if self.root.is_full():
            # Create new root
            new_root = BTreeNode(is_leaf=False, max_keys=self.max_keys)
            new_root.children.append(self.root)
            new_root.split_child(0)
            self.root = new_root
        
        self.root.insert_non_full(key, value)
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for key in B-tree"""
        return self.root.search(key)
    
    def print_tree(self, node: BTreeNode = None, level: int = 0):
        """Print B-tree structure (for debugging)"""
        if node is None:
            node = self.root
        
        print("  " * level + f"Keys: {node.keys}")
        if node.is_leaf and hasattr(node, 'values'):
            print("  " * level + f"Values: {node.values}")
        
        for child in node.children:
            self.print_tree(child, level + 1)

# Test B-tree implementation
def test_btree():
    """Test B-tree functionality"""
    btree = BTree(max_keys=3)  # Small max_keys for testing splits
    
    # Insert test data
    test_data = [(10, "ten"), (20, "twenty"), (5, "five"), (6, "six"),
                 (12, "twelve"), (30, "thirty"), (7, "seven"), (17, "seventeen")]
    
    print("Inserting data into B-tree:")
    for key, value in test_data:
        btree.insert(key, value)
        print(f"Inserted ({key}, {value})")
    
    print("\nB-tree structure:")
    btree.print_tree()
    
    print("\nSearching for values:")
    for key, expected_value in test_data:
        found_value = btree.search(key)
        print(f"Search {key}: {found_value} (expected: {expected_value})")
        assert found_value == expected_value, f"Search failed for key {key}"
    
    # Test search for non-existent key
    assert btree.search(999) is None
    print("Search for non-existent key: None ✓")
    
    print("B-tree test passed!")

if __name__ == "__main__":
    test_btree()
```

### Step 3: Table Management and Basic SQL Operations

Create table structures and implement basic SQL operations (CREATE, INSERT, SELECT).

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DataType(Enum):
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    REAL = "REAL"

@dataclass
class Column:
    """Represents a table column"""
    name: str
    data_type: DataType
    is_primary_key: bool = False
    not_null: bool = False

class Table:
    """Represents a database table"""
    
    def __init__(self, name: str, columns: List[Column], storage_engine: StorageEngine):
        self.name = name
        self.columns = columns
        self.storage_engine = storage_engine
        self.root_page = None
        self.btree_index = BTree()
        
        # Create root page for table data
        self._create_root_page()
    
    def _create_root_page(self):
        """Create root page for table"""
        self.root_page = self.storage_engine.allocate_page(PageType.TABLE_LEAF)
    
    def insert(self, values: List[Any]) -> bool:
        """Insert a record into the table"""
        if len(values) != len(self.columns):
            raise ValueError(f"Expected {len(self.columns)} values, got {len(values)}")
        
        # Validate data types
        validated_values = []
        for i, (value, column) in enumerate(zip(values, self.columns)):
            validated_value = self._validate_value(value, column)
            validated_values.append(validated_value)
        
        # Create record
        record = Record(validated_values)
        
        # For simplicity, store in B-tree index (in real DB, would store in pages)
        # Use first column as key (assuming it's unique)
        key = validated_values[0]
        self.btree_index.insert(key, record)
        
        return True
    
    def select(self, where_clause: Optional[Dict[str, Any]] = None) -> List[Record]:
        """Select records from table"""
        # This is a simplified implementation
        # In a real database, we'd scan pages or use indexes
        results = []
        
        # For now, we'll do a simple traversal of our B-tree
        # This is not how real databases work, but serves our learning purpose
        self._collect_records(self.btree_index.root, results, where_clause)
        
        return results
    
    def _collect_records(self, node: BTreeNode, results: List[Record], where_clause: Optional[Dict[str, Any]]):
        """Collect records from B-tree (simplified)"""
        if node.is_leaf:
            for value in node.values:
                if isinstance(value, Record):
                    if self._matches_where_clause(value, where_clause):
                        results.append(value)
        else:
            for child in node.children:
                self._collect_records(child, results, where_clause)
    
    def _matches_where_clause(self, record: Record, where_clause: Optional[Dict[str, Any]]) -> bool:
        """Check if record matches WHERE clause"""
        if where_clause is None:
            return True
        
        for column_name, expected_value in where_clause.items():
            column_index = self._get_column_index(column_name)
            if column_index is None:
                continue
            
            actual_value = record.values[column_index]
            if actual_value != expected_value:
                return False
        
        return True
    
    def _get_column_index(self, column_name: str) -> Optional[int]:
        """Get index of column by name"""
        for i, column in enumerate(self.columns):
            if column.name == column_name:
                return i
        return None
    
    def _validate_value(self, value: Any, column: Column) -> Any:
        """Validate and convert value according to column type"""
        if value is None:
            if column.not_null:
                raise ValueError(f"Column {column.name} cannot be NULL")
            return None
        
        if column.data_type == DataType.INTEGER:
            return int(value)
        elif column.data_type == DataType.TEXT:
            return str(value)
        elif column.data_type == DataType.REAL:
            return float(value)
        
        return value

class Database:
    """Main database class"""
    
    def __init__(self, db_file: str):
        self.storage_engine = StorageEngine(db_file)
        self.tables: Dict[str, Table] = {}
    
    def create_table(self, name: str, columns: List[Column]) -> bool:
        """Create a new table"""
        if name in self.tables:
            raise ValueError(f"Table {name} already exists")
        
        table = Table(name, columns, self.storage_engine)
        self.tables[name] = table
        return True
    
    def get_table(self, name: str) -> Optional[Table]:
        """Get table by name"""
        return self.tables.get(name)
    
    def execute_sql(self, sql: str) -> Any:
        """Execute a SQL statement (simplified parser)"""
        sql = sql.strip()
        
        if sql.upper().startswith('CREATE TABLE'):
            return self._execute_create_table(sql)
        elif sql.upper().startswith('INSERT INTO'):
            return self._execute_insert(sql)
        elif sql.upper().startswith('SELECT'):
            return self._execute_select(sql)
        else:
            raise ValueError(f"Unsupported SQL statement: {sql}")
    
    def _execute_create_table(self, sql: str) -> bool:
        """Execute CREATE TABLE statement"""
        # Very simple parser - not production ready!
        # Example: CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)
        
        import re
        match = re.match(r'CREATE TABLE (\w+) \((.+)\)', sql, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid CREATE TABLE syntax")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        columns = []
        for column_def in columns_str.split(','):
            parts = column_def.strip().split()
            if len(parts) < 2:
                raise ValueError(f"Invalid column definition: {column_def}")
            
            column_name = parts[0]
            column_type = DataType(parts[1].upper())
            
            # Check for constraints
            is_primary_key = 'PRIMARY' in [p.upper() for p in parts]
            not_null = 'NOT' in [p.upper() for p in parts] and 'NULL' in [p.upper() for p in parts]
            
            columns.append(Column(column_name, column_type, is_primary_key, not_null))
        
        return self.create_table(table_name, columns)
    
    def _execute_insert(self, sql: str) -> bool:
        """Execute INSERT INTO statement"""
        # Example: INSERT INTO users VALUES (1, 'Alice', 25)
        
        import re
        match = re.match(r'INSERT INTO (\w+) VALUES \((.+)\)', sql, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid INSERT syntax")
        
        table_name = match.group(1)
        values_str = match.group(2)
        
        table = self.get_table(table_name)
        if not table:
            raise ValueError(f"Table {table_name} does not exist")
        
        # Parse values (very basic)
        values = []
        for value_str in values_str.split(','):
            value_str = value_str.strip()
            
            # Remove quotes for strings
            if value_str.startswith("'") and value_str.endswith("'"):
                values.append(value_str[1:-1])
            elif value_str.startswith('"') and value_str.endswith('"'):
                values.append(value_str[1:-1])
            else:
                # Try to parse as number
                try:
                    if '.' in value_str:
                        values.append(float(value_str))
                    else:
                        values.append(int(value_str))
                except ValueError:
                    values.append(value_str)
        
        return table.insert(values)
    
    def _execute_select(self, sql: str) -> List[Record]:
        """Execute SELECT statement"""
        # Example: SELECT * FROM users WHERE age = 25
        
        import re
        
        # Basic SELECT * FROM table pattern
        match = re.match(r'SELECT \* FROM (\w+)(?:\s+WHERE\s+(.+))?', sql, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid SELECT syntax (only SELECT * FROM table [WHERE] supported)")
        
        table_name = match.group(1)
        where_str = match.group(2)
        
        table = self.get_table(table_name)
        if not table:
            raise ValueError(f"Table {table_name} does not exist")
        
        where_clause = None
        if where_str:
            # Very basic WHERE parsing: column = value
            where_match = re.match(r'(\w+)\s*=\s*(.+)', where_str.strip())
            if where_match:
                column_name = where_match.group(1)
                value_str = where_match.group(2).strip()
                
                # Parse value
                if value_str.startswith("'") and value_str.endswith("'"):
                    value = value_str[1:-1]
                elif value_str.startswith('"') and value_str.endswith('"'):
                    value = value_str[1:-1]
                else:
                    try:
                        value = int(value_str) if '.' not in value_str else float(value_str)
                    except ValueError:
                        value = value_str
                
                where_clause = {column_name: value}
        
        return table.select(where_clause)
    
    def close(self):
        """Close database"""
        self.storage_engine.close()

# Test the database
def test_database():
    """Test database functionality"""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_file = tmp.name
    
    try:
        # Create database
        db = Database(db_file)
        
        # Create table
        print("Creating table...")
        db.execute_sql("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
        
        # Insert data
        print("Inserting data...")
        db.execute_sql("INSERT INTO users VALUES (1, 'Alice', 25)")
        db.execute_sql("INSERT INTO users VALUES (2, 'Bob', 30)")
        db.execute_sql("INSERT INTO users VALUES (3, 'Charlie', 25)")
        
        # Select all data
        print("Selecting all data...")
        results = db.execute_sql("SELECT * FROM users")
        for record in results:
            print(f"Record: {record.values}")
        
        # Select with WHERE clause
        print("Selecting with WHERE clause...")
        results = db.execute_sql("SELECT * FROM users WHERE age = 25")
        print(f"Found {len(results)} records with age = 25")
        for record in results:
            print(f"Record: {record.values}")
        
        db.close()
        print("Database test passed!")
        
    finally:
        if os.path.exists(db_file):
            os.unlink(db_file)

if __name__ == "__main__":
    test_database()
```

## 🧪 Testing Your Implementation

Create comprehensive tests for all database components:

```python
def run_comprehensive_tests():
    """Run all database tests"""
    import tempfile
    import os
    
    print("Running Database Tests")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_file = tmp.name
    
    try:
        # Test 1: Storage engine
        print("1. Testing storage engine...")
        test_storage()
        
        # Test 2: B-tree
        print("2. Testing B-tree...")
        test_btree()
        
        # Test 3: Full database
        print("3. Testing full database...")
        test_database()
        
        # Test 4: Advanced queries
        print("4. Testing advanced operations...")
        db = Database(db_file)
        
        # Create more complex table
        db.execute_sql("""
            CREATE TABLE products (
                id INTEGER,
                name TEXT,
                price REAL,
                category TEXT
            )
        """)
        
        # Insert sample data
        products = [
            (1, 'Laptop', 999.99, 'Electronics'),
            (2, 'Coffee Mug', 12.50, 'Kitchen'),
            (3, 'Notebook', 5.99, 'Office'),
            (4, 'Mouse', 25.00, 'Electronics'),
        ]
        
        for product in products:
            db.execute_sql(f"INSERT INTO products VALUES ({product[0]}, '{product[1]}', {product[2]}, '{product[3]}')")
        
        # Test queries
        all_products = db.execute_sql("SELECT * FROM products")
        print(f"All products: {len(all_products)} records")
        
        electronics = db.execute_sql("SELECT * FROM products WHERE category = 'Electronics'")
        print(f"Electronics: {len(electronics)} records")
        
        db.close()
        
        print("\n" + "=" * 50)
        print("🎉 All database tests passed!")
        
    finally:
        if os.path.exists(db_file):
            os.unlink(db_file)

if __name__ == "__main__":
    run_comprehensive_tests()
```

## 🎯 Challenges to Extend Your Implementation

1. **Query Optimization**: Add query planner and optimizer
2. **Transactions**: Implement ACID transactions with rollback
3. **Concurrency**: Add locking and multi-user support
4. **Joins**: Implement JOIN operations between tables
5. **Advanced Indexing**: Add hash indexes and composite indexes
6. **Recovery**: Implement write-ahead logging and crash recovery
7. **SQL Parser**: Build a complete SQL parser with more syntax support

## 📚 Key Concepts Learned

- **Storage Management**: Page-based storage and buffer pool management
- **B-tree Indexing**: Self-balancing trees for efficient data access
- **Query Processing**: Parsing, planning, and executing SQL queries
- **Record Management**: Serialization and storage of structured data
- **File Organization**: How databases organize data on disk
- **ACID Properties**: Atomicity, Consistency, Isolation, Durability

---

**Congratulations!** You've built a functional relational database that understands the core concepts of data storage, indexing, and SQL query processing.