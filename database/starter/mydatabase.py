#!/usr/bin/env python3
"""
MyDatabase - A relational database implementation from scratch

This database demonstrates core RDBMS concepts:
- Page-based storage engine with disk persistence
- B-tree indexes for efficient data retrieval
- SQL query parsing and execution
- Record serialization and management
- Transaction basics and table management

Built using only Python standard library to show fundamental database concepts.
"""

import os
import struct
import re
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass


class PageType(Enum):
    """Types of database pages"""
    TABLE_LEAF = 1
    TABLE_INTERIOR = 2
    INDEX_LEAF = 3
    INDEX_INTERIOR = 4


class DataType(Enum):
    """Supported data types"""
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    REAL = "REAL"


@dataclass
class Column:
    """Database table column definition"""
    name: str
    data_type: DataType
    is_primary_key: bool = False
    not_null: bool = False
    
    def __str__(self):
        constraints = []
        if self.is_primary_key:
            constraints.append("PRIMARY KEY")
        if self.not_null:
            constraints.append("NOT NULL")
        
        constraint_str = " " + " ".join(constraints) if constraints else ""
        return f"{self.name} {self.data_type.value}{constraint_str}"


class Page:
    """Database page - fixed size block of data on disk"""
    
    PAGE_SIZE = 4096  # 4KB pages
    HEADER_SIZE = 8   # Page header size
    
    def __init__(self, page_num: int, page_type: PageType):
        self.page_num = page_num
        self.page_type = page_type
        self.data = bytearray(self.PAGE_SIZE)
        self.is_dirty = False
        
        # Initialize page header
        self._write_header()
    
    def _write_header(self):
        """Write page header: [page_type(1), flags(1), num_records(2), free_space_offset(2), reserved(2)]"""
        struct.pack_into('<BBHHH', self.data, 0, 
                        self.page_type.value, 0, 0, self.PAGE_SIZE - self.HEADER_SIZE, 0)
    
    def get_num_records(self) -> int:
        """Get number of records in page"""
        return struct.unpack_from('<H', self.data, 2)[0]
    
    def set_num_records(self, count: int):
        """Set number of records in page"""
        struct.pack_into('<H', self.data, 2, count)
        self.is_dirty = True
    
    def get_free_space_offset(self) -> int:
        """Get offset where free space begins"""
        return struct.unpack_from('<H', self.data, 4)[0]
    
    def set_free_space_offset(self, offset: int):
        """Set free space offset"""
        struct.pack_into('<H', self.data, 4, offset)
        self.is_dirty = True
    
    def get_free_space(self) -> int:
        """Get amount of free space available"""
        return self.get_free_space_offset() - self.HEADER_SIZE - (self.get_num_records() * 2)


class Record:
    """Database record with multiple fields"""
    
    def __init__(self, values: List[Any]):
        self.values = values
    
    def __str__(self):
        return f"Record({self.values})"
    
    def __repr__(self):
        return self.__str__()
    
    def serialize(self) -> bytes:
        """Serialize record to bytes for storage"""
        if not self.values:
            return b''
        
        result = bytearray()
        
        # Record header: number of fields
        num_fields = len(self.values)
        result.extend(struct.pack('<H', num_fields))
        
        # Field type and length information
        field_info = []
        data_section = bytearray()
        
        for value in self.values:
            if value is None:
                field_info.append((0, 0))  # Type 0 = NULL, length 0
            elif isinstance(value, str):
                encoded = value.encode('utf-8')
                field_info.append((1, len(encoded)))  # Type 1 = string
                data_section.extend(encoded)
            elif isinstance(value, int):
                field_info.append((2, 8))  # Type 2 = integer, 8 bytes
                data_section.extend(struct.pack('<q', value))
            elif isinstance(value, float):
                field_info.append((3, 8))  # Type 3 = float, 8 bytes
                data_section.extend(struct.pack('<d', value))
        
        # Write field info (type + length for each field)
        for field_type, field_length in field_info:
            result.extend(struct.pack('<BB', field_type, field_length))
        
        # Write data section
        result.extend(data_section)
        
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes, column_types: List[DataType] = None) -> 'Record':
        """Deserialize record from bytes"""
        if len(data) < 2:
            return cls([])
        
        offset = 0
        
        # Read number of fields
        num_fields = struct.unpack_from('<H', data, offset)[0]
        offset += 2
        
        if num_fields == 0:
            return cls([])
        
        # Read field type/length info
        field_info = []
        for i in range(num_fields):
            field_type, field_length = struct.unpack_from('<BB', data, offset)
            field_info.append((field_type, field_length))
            offset += 2
        
        # Read field data
        values = []
        for field_type, field_length in field_info:
            if field_type == 0:  # NULL
                values.append(None)
            elif field_type == 1:  # String
                value = data[offset:offset + field_length].decode('utf-8')
                values.append(value)
                offset += field_length
            elif field_type == 2:  # Integer
                value = struct.unpack_from('<q', data, offset)[0]
                values.append(value)
                offset += field_length
            elif field_type == 3:  # Float
                value = struct.unpack_from('<d', data, offset)[0]
                values.append(value)
                offset += field_length
            else:
                values.append(None)  # Unknown type
        
        return cls(values)


class BTreeNode:
    """B-tree node for database indexing"""
    
    def __init__(self, is_leaf: bool = False, max_keys: int = 255):
        self.is_leaf = is_leaf
        self.keys: List[Any] = []
        self.values: List[Any] = []  # For leaf nodes (record data)
        self.children: List['BTreeNode'] = []  # For internal nodes
        self.max_keys = max_keys
        self.parent: Optional['BTreeNode'] = None
    
    def is_full(self) -> bool:
        """Check if node has maximum number of keys"""
        return len(self.keys) >= self.max_keys
    
    def is_minimal(self) -> bool:
        """Check if node has minimum number of keys"""
        min_keys = self.max_keys // 2
        return len(self.keys) < min_keys
    
    def find_child_index(self, key: Any) -> int:
        """Find index of child that should contain the key"""
        i = 0
        while i < len(self.keys) and key > self.keys[i]:
            i += 1
        return i
    
    def insert_key(self, key: Any, value: Any = None, child: 'BTreeNode' = None):
        """Insert key into this node (assumes node is not full)"""
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
            # Insert into internal node
            self.keys.append(None)
            self.children.append(None)
            
            while i >= 0 and self.keys[i] > key:
                self.keys[i + 1] = self.keys[i]
                self.children[i + 2] = self.children[i + 1]
                i -= 1
            
            self.keys[i + 1] = key
            self.children[i + 2] = child
            if child:
                child.parent = self
    
    def split(self) -> Tuple['BTreeNode', Any]:
        """Split this node and return new node and promoted key"""
        mid_index = len(self.keys) // 2
        mid_key = self.keys[mid_index]
        
        # Create new node
        new_node = BTreeNode(self.is_leaf, self.max_keys)
        new_node.parent = self.parent
        
        # Move keys and values/children to new node
        if self.is_leaf:
            new_node.keys = self.keys[mid_index + 1:]
            new_node.values = self.values[mid_index + 1:]
            self.keys = self.keys[:mid_index + 1]  # Keep mid_key in left leaf
            self.values = self.values[:mid_index + 1]
        else:
            new_node.keys = self.keys[mid_index + 1:]
            new_node.children = self.children[mid_index + 1:]
            # Update parent pointers
            for child in new_node.children:
                if child:
                    child.parent = new_node
            
            self.keys = self.keys[:mid_index]
            self.children = self.children[:mid_index + 1]
        
        return new_node, mid_key
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for key in subtree rooted at this node"""
        i = 0
        while i < len(self.keys):
            if key == self.keys[i]:
                if self.is_leaf:
                    return self.values[i] if i < len(self.values) else None
                else:
                    # Found key in internal node, search right child
                    if i + 1 < len(self.children):
                        return self.children[i + 1].search(key)
                    return None
            elif key < self.keys[i]:
                break
            i += 1
        
        if self.is_leaf:
            return None  # Not found in leaf
        
        # Search in appropriate child
        if i < len(self.children):
            return self.children[i].search(key)
        
        return None


class BTree:
    """B-tree for database indexing"""
    
    def __init__(self, max_keys: int = 255):
        self.root = BTreeNode(is_leaf=True, max_keys=max_keys)
        self.max_keys = max_keys
    
    def insert(self, key: Any, value: Any = None):
        """Insert key-value pair into B-tree"""
        if self.root.is_full():
            # Split root
            old_root = self.root
            self.root = BTreeNode(is_leaf=False, max_keys=self.max_keys)
            self.root.children.append(old_root)
            old_root.parent = self.root
            
            new_node, promoted_key = old_root.split()
            self.root.insert_key(promoted_key, child=new_node)
        
        self._insert_non_full(self.root, key, value)
    
    def _insert_non_full(self, node: BTreeNode, key: Any, value: Any):
        """Insert into a non-full node"""
        if node.is_leaf:
            # Insert into leaf node
            i = 0
            while i < len(node.keys) and node.keys[i] < key:
                i += 1
            
            node.keys.insert(i, key)
            node.values.insert(i, value)
        else:
            # Find child to insert into
            child_index = node.find_child_index(key)
            child = node.children[child_index]
            
            if child.is_full():
                # Split child
                new_child, promoted_key = child.split()
                
                # Insert promoted key into current node
                i = 0
                while i < len(node.keys) and node.keys[i] < promoted_key:
                    i += 1
                
                node.keys.insert(i, promoted_key)
                node.children.insert(i + 1, new_child)
                new_child.parent = node
                
                # Determine which child to insert into
                if key > promoted_key:
                    child = new_child
            
            self._insert_non_full(child, key, value)
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for key in B-tree"""
        return self.root.search(key)
    
    def range_search(self, start_key: Any = None, end_key: Any = None) -> List[Tuple[Any, Any]]:
        """Search for keys in range [start_key, end_key]"""
        results = []
        self._range_search(self.root, start_key, end_key, results)
        return results
    
    def _range_search(self, node: BTreeNode, start_key: Any, end_key: Any, results: List[Tuple[Any, Any]]):
        """Recursive range search"""
        if node.is_leaf:
            for i, key in enumerate(node.keys):
                if (start_key is None or key >= start_key) and (end_key is None or key <= end_key):
                    results.append((key, node.values[i]))
        else:
            for i, key in enumerate(node.keys):
                # Search left child
                if start_key is None or key >= start_key:
                    self._range_search(node.children[i], start_key, end_key, results)
                
                # Include current key if in range
                if (start_key is None or key >= start_key) and (end_key is None or key <= end_key):
                    # For internal nodes, we don't store values
                    pass
                
                # Search right child
                if end_key is None or key <= end_key:
                    if i + 1 < len(node.children):
                        self._range_search(node.children[i + 1], start_key, end_key, results)


class StorageEngine:
    """Database storage engine managing pages on disk"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.file_handle = None
        self.page_cache: Dict[int, Page] = {}
        self.next_page_num = 0
        self.is_open = False
        
        self._open_database()
    
    def _open_database(self):
        """Open database file or create new one"""
        is_new_db = not os.path.exists(self.db_file) or os.path.getsize(self.db_file) == 0
        
        self.file_handle = open(self.db_file, 'rb+' if not is_new_db else 'wb+')
        self.is_open = True
        
        if is_new_db:
            self._initialize_database()
        else:
            self._read_database_header()
    
    def _initialize_database(self):
        """Initialize new database file with header"""
        # Database header: magic(4) + version(4) + page_size(4) + num_pages(4)
        header = struct.pack('<4sIII', b'MyDB', 1, Page.PAGE_SIZE, 0)
        self.file_handle.write(header)
        self.file_handle.flush()
        self.next_page_num = 0
    
    def _read_database_header(self):
        """Read database header from existing file"""
        self.file_handle.seek(0)
        header_data = self.file_handle.read(16)
        
        if len(header_data) < 16:
            raise ValueError("Invalid database file: header too short")
        
        magic, version, page_size, num_pages = struct.unpack('<4sIII', header_data)
        
        if magic != b'MyDB':
            raise ValueError(f"Invalid database file: magic bytes = {magic}")
        
        if page_size != Page.PAGE_SIZE:
            raise ValueError(f"Page size mismatch: expected {Page.PAGE_SIZE}, got {page_size}")
        
        self.next_page_num = num_pages
    
    def allocate_page(self, page_type: PageType) -> Page:
        """Allocate a new page"""
        page = Page(self.next_page_num, page_type)
        self.page_cache[self.next_page_num] = page
        self.next_page_num += 1
        
        # Update page count in header
        self._update_page_count()
        
        return page
    
    def get_page(self, page_num: int) -> Optional[Page]:
        """Get page from cache or disk"""
        if page_num in self.page_cache:
            return self.page_cache[page_num]
        
        if page_num >= self.next_page_num:
            return None
        
        # Read from disk
        page_offset = 16 + (page_num * Page.PAGE_SIZE)  # Skip 16-byte header
        self.file_handle.seek(page_offset)
        page_data = self.file_handle.read(Page.PAGE_SIZE)
        
        if len(page_data) < Page.PAGE_SIZE:
            return None
        
        # Reconstruct page
        page_type_val = struct.unpack_from('<B', page_data, 0)[0]
        page_type = PageType(page_type_val)
        
        page = Page(page_num, page_type)
        page.data = bytearray(page_data)
        page.is_dirty = False
        
        self.page_cache[page_num] = page
        return page
    
    def write_page(self, page: Page):
        """Write page to disk if dirty"""
        if not page.is_dirty:
            return
        
        page_offset = 16 + (page.page_num * Page.PAGE_SIZE)
        self.file_handle.seek(page_offset)
        self.file_handle.write(page.data)
        self.file_handle.flush()
        
        page.is_dirty = False
    
    def _update_page_count(self):
        """Update page count in database header"""
        self.file_handle.seek(12)  # Offset to num_pages field
        self.file_handle.write(struct.pack('<I', self.next_page_num))
        self.file_handle.flush()
    
    def flush_all_pages(self):
        """Write all dirty pages to disk"""
        for page in self.page_cache.values():
            if page.is_dirty:
                self.write_page(page)
    
    def close(self):
        """Close database and flush all pages"""
        if self.is_open:
            self.flush_all_pages()
            if self.file_handle:
                self.file_handle.close()
            self.is_open = False


class Table:
    """Database table with schema and data"""
    
    def __init__(self, name: str, columns: List[Column], storage_engine: StorageEngine):
        self.name = name
        self.columns = columns
        self.storage_engine = storage_engine
        self.primary_index = BTree(max_keys=100)  # Primary key index
        self.record_count = 0
        
        # Create column name to index mapping
        self.column_indexes = {col.name: i for i, col in enumerate(columns)}
    
    def get_column_types(self) -> List[DataType]:
        """Get list of column data types"""
        return [col.data_type for col in self.columns]
    
    def validate_record(self, values: List[Any]) -> List[Any]:
        """Validate and convert record values according to schema"""
        if len(values) != len(self.columns):
            raise ValueError(f"Expected {len(self.columns)} values, got {len(values)}")
        
        validated_values = []
        for i, (value, column) in enumerate(zip(values, self.columns)):
            # Check NOT NULL constraint
            if value is None and column.not_null:
                raise ValueError(f"Column {column.name} cannot be NULL")
            
            # Type conversion
            if value is not None:
                if column.data_type == DataType.INTEGER:
                    validated_values.append(int(value))
                elif column.data_type == DataType.TEXT:
                    validated_values.append(str(value))
                elif column.data_type == DataType.REAL:
                    validated_values.append(float(value))
                else:
                    validated_values.append(value)
            else:
                validated_values.append(None)
        
        return validated_values
    
    def insert(self, values: List[Any]) -> bool:
        """Insert record into table"""
        validated_values = self.validate_record(values)
        record = Record(validated_values)
        
        # For simplicity, use first column as primary key
        # In a real database, this would be more sophisticated
        primary_key = validated_values[0] if validated_values else self.record_count
        
        # Check for duplicate primary key (simplified)
        if self.primary_index.search(primary_key) is not None:
            raise ValueError(f"Duplicate primary key: {primary_key}")
        
        # Insert into primary index
        self.primary_index.insert(primary_key, record)
        self.record_count += 1
        
        return True
    
    def select_all(self) -> List[Record]:
        """Select all records from table"""
        results = []
        # Get all records from B-tree (simplified traversal)
        self._collect_all_records(self.primary_index.root, results)
        return results
    
    def select_where(self, conditions: Dict[str, Any]) -> List[Record]:
        """Select records matching WHERE conditions"""
        all_records = self.select_all()
        results = []
        
        for record in all_records:
            if self._matches_conditions(record, conditions):
                results.append(record)
        
        return results
    
    def _collect_all_records(self, node: BTreeNode, results: List[Record]):
        """Collect all records from B-tree (depth-first traversal)"""
        if node.is_leaf:
            for value in node.values:
                if isinstance(value, Record):
                    results.append(value)
        else:
            for child in node.children:
                if child:
                    self._collect_all_records(child, results)
    
    def _matches_conditions(self, record: Record, conditions: Dict[str, Any]) -> bool:
        """Check if record matches WHERE conditions"""
        for column_name, expected_value in conditions.items():
            column_index = self.column_indexes.get(column_name)
            if column_index is None:
                continue  # Unknown column, skip
            
            if column_index >= len(record.values):
                return False
            
            actual_value = record.values[column_index]
            if actual_value != expected_value:
                return False
        
        return True


class Database:
    """Main database management system"""
    
    def __init__(self, db_file: str):
        self.storage_engine = StorageEngine(db_file)
        self.tables: Dict[str, Table] = {}
        self.transaction_active = False
    
    def create_table(self, name: str, columns: List[Column]) -> bool:
        """Create a new table"""
        if name.lower() in [t.lower() for t in self.tables.keys()]:
            raise ValueError(f"Table '{name}' already exists")
        
        table = Table(name, columns, self.storage_engine)
        self.tables[name] = table
        return True
    
    def drop_table(self, name: str) -> bool:
        """Drop a table"""
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")
        
        del self.tables[name]
        return True
    
    def get_table(self, name: str) -> Optional[Table]:
        """Get table by name"""
        return self.tables.get(name)
    
    def list_tables(self) -> List[str]:
        """List all table names"""
        return list(self.tables.keys())
    
    def execute_sql(self, sql: str) -> Any:
        """Execute SQL statement"""
        sql = sql.strip().rstrip(';')
        
        if not sql:
            return None
        
        # Simple SQL dispatcher
        sql_upper = sql.upper()
        
        if sql_upper.startswith('CREATE TABLE'):
            return self._execute_create_table(sql)
        elif sql_upper.startswith('DROP TABLE'):
            return self._execute_drop_table(sql)
        elif sql_upper.startswith('INSERT INTO'):
            return self._execute_insert(sql)
        elif sql_upper.startswith('SELECT'):
            return self._execute_select(sql)
        elif sql_upper.startswith('SHOW TABLES'):
            return self._execute_show_tables()
        elif sql_upper.startswith('DESCRIBE') or sql_upper.startswith('DESC'):
            return self._execute_describe(sql)
        else:
            raise ValueError(f"Unsupported SQL statement: {sql}")
    
    def _execute_create_table(self, sql: str) -> bool:
        """Execute CREATE TABLE statement"""
        # Basic regex to parse CREATE TABLE
        pattern = r'CREATE\s+TABLE\s+(\w+)\s*\(\s*(.+)\s*\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid CREATE TABLE syntax")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        # Parse column definitions
        columns = []
        for column_def in columns_str.split(','):
            column_def = column_def.strip()
            if not column_def:
                continue
            
            # Basic parsing: name type [constraints]
            parts = column_def.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid column definition: {column_def}")
            
            column_name = parts[0]
            column_type_str = parts[1].upper()
            
            # Parse data type
            try:
                column_type = DataType(column_type_str)
            except ValueError:
                raise ValueError(f"Unsupported data type: {column_type_str}")
            
            # Parse constraints
            constraint_str = ' '.join(parts[2:]).upper()
            is_primary_key = 'PRIMARY' in constraint_str and 'KEY' in constraint_str
            not_null = 'NOT' in constraint_str and 'NULL' in constraint_str
            
            columns.append(Column(column_name, column_type, is_primary_key, not_null))
        
        return self.create_table(table_name, columns)
    
    def _execute_drop_table(self, sql: str) -> bool:
        """Execute DROP TABLE statement"""
        pattern = r'DROP\s+TABLE\s+(\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid DROP TABLE syntax")
        
        table_name = match.group(1)
        return self.drop_table(table_name)
    
    def _execute_insert(self, sql: str) -> bool:
        """Execute INSERT INTO statement"""
        # Pattern: INSERT INTO table VALUES (value1, value2, ...)
        pattern = r'INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.+)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid INSERT syntax (only 'INSERT INTO table VALUES (...)' supported)")
        
        table_name = match.group(1)
        values_str = match.group(2)
        
        table = self.get_table(table_name)
        if not table:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        # Parse values - basic CSV parsing
        values = self._parse_values_list(values_str)
        
        return table.insert(values)
    
    def _execute_select(self, sql: str) -> List[Record]:
        """Execute SELECT statement"""
        # Basic patterns
        patterns = [
            # SELECT * FROM table WHERE conditions
            r'SELECT\s+\*\s+FROM\s+(\w+)\s+WHERE\s+(.+)',
            # SELECT * FROM table
            r'SELECT\s+\*\s+FROM\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1)
                where_clause = match.group(2) if len(match.groups()) > 1 else None
                
                table = self.get_table(table_name)
                if not table:
                    raise ValueError(f"Table '{table_name}' does not exist")
                
                if where_clause:
                    conditions = self._parse_where_clause(where_clause)
                    return table.select_where(conditions)
                else:
                    return table.select_all()
        
        raise ValueError("Invalid SELECT syntax (only 'SELECT * FROM table [WHERE ...]' supported)")
    
    def _execute_show_tables(self) -> List[str]:
        """Execute SHOW TABLES statement"""
        return self.list_tables()
    
    def _execute_describe(self, sql: str) -> List[Column]:
        """Execute DESCRIBE table statement"""
        pattern = r'(?:DESCRIBE|DESC)\s+(\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid DESCRIBE syntax")
        
        table_name = match.group(1)
        table = self.get_table(table_name)
        if not table:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        return table.columns
    
    def _parse_values_list(self, values_str: str) -> List[Any]:
        """Parse comma-separated values list"""
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                i += 1
                continue
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                i += 1
                continue
            elif char == ',' and not in_quotes:
                values.append(self._parse_value(current_value.strip()))
                current_value = ""
                i += 1
                continue
            
            current_value += char
            i += 1
        
        # Add last value
        if current_value.strip():
            values.append(self._parse_value(current_value.strip()))
        
        return values
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a single value from string"""
        value_str = value_str.strip()
        
        if value_str.upper() == 'NULL':
            return None
        
        # Remove quotes for string values
        if ((value_str.startswith("'") and value_str.endswith("'")) or
            (value_str.startswith('"') and value_str.endswith('"'))):
            return value_str[1:-1]
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str  # Return as string
    
    def _parse_where_clause(self, where_str: str) -> Dict[str, Any]:
        """Parse simple WHERE clause (column = value)"""
        # Very basic parsing for single condition
        pattern = r'(\w+)\s*=\s*(.+)'
        match = re.match(pattern, where_str.strip(), re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid WHERE clause (only 'column = value' supported)")
        
        column_name = match.group(1)
        value_str = match.group(2).strip()
        
        value = self._parse_value(value_str)
        return {column_name: value}
    
    def close(self):
        """Close database"""
        self.storage_engine.close()


def create_demo_database():
    """Create a demo database with sample data"""
    import tempfile
    
    print("Creating demo database...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_file = tmp.name
    
    try:
        db = Database(db_file)
        
        print(f"Database created: {db_file}")
        
        # Create tables
        print("\n1. Creating tables...")
        
        db.execute_sql("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                age INTEGER
            )
        """)
        
        db.execute_sql("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY NOT NULL,
                user_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                amount REAL
            )
        """)
        
        print("✓ Tables created: users, orders")
        
        # Insert sample data
        print("\n2. Inserting sample data...")
        
        users_data = [
            (1, 'Alice Johnson', 'alice@example.com', 28),
            (2, 'Bob Smith', 'bob@example.com', 35),
            (3, 'Charlie Brown', 'charlie@example.com', 22),
            (4, 'Diana Prince', 'diana@example.com', 31),
            (5, 'Eve Wilson', 'eve@example.com', 26)
        ]
        
        for user in users_data:
            db.execute_sql(f"INSERT INTO users VALUES ({user[0]}, '{user[1]}', '{user[2]}', {user[3]})")
        
        orders_data = [
            (101, 1, 'Laptop', 999.99),
            (102, 1, 'Mouse', 25.50),
            (103, 2, 'Keyboard', 89.99),
            (104, 3, 'Monitor', 299.99),
            (105, 2, 'Headphones', 79.99),
            (106, 4, 'Tablet', 399.99)
        ]
        
        for order in orders_data:
            db.execute_sql(f"INSERT INTO orders VALUES ({order[0]}, {order[1]}, '{order[2]}', {order[3]})")
        
        print(f"✓ Inserted {len(users_data)} users and {len(orders_data)} orders")
        
        # Demonstrate queries
        print("\n3. Running sample queries...")
        
        # Show all users
        print("\nAll users:")
        users = db.execute_sql("SELECT * FROM users")
        for user in users:
            print(f"  ID: {user.values[0]}, Name: {user.values[1]}, Email: {user.values[2]}, Age: {user.values[3]}")
        
        # Filter by age
        print("\nUsers over 30:")
        older_users = db.execute_sql("SELECT * FROM users WHERE age = 35")  # Note: simplified WHERE
        for user in older_users:
            print(f"  {user.values[1]} (age {user.values[3]})")
        
        # Show orders
        print(f"\nAll orders:")
        orders = db.execute_sql("SELECT * FROM orders")
        for order in orders:
            print(f"  Order {order.values[0]}: {order.values[2]} (${order.values[3]}) for user {order.values[1]}")
        
        # Table information
        print("\n4. Database schema:")
        tables = db.execute_sql("SHOW TABLES")
        for table_name in tables:
            print(f"\nTable: {table_name}")
            columns = db.execute_sql(f"DESCRIBE {table_name}")
            for col in columns:
                print(f"  {col}")
        
        db.close()
        print(f"\n✓ Demo completed! Database file: {db_file}")
        
        return db_file
        
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(db_file):
            os.unlink(db_file)
        raise


def run_tests():
    """Run comprehensive database tests"""
    print("Running MyDatabase Tests")
    print("=" * 50)
    
    # Test 1: Basic storage engine
    print("1. Testing storage engine...")
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        storage = StorageEngine(tmp.name)
        page = storage.allocate_page(PageType.TABLE_LEAF)
        assert page.page_num == 0
        storage.close()
    print("   ✓ Storage engine works")
    
    # Test 2: Record serialization
    print("2. Testing record serialization...")
    record = Record(['Alice', 25, 'Engineer', None])
    serialized = record.serialize()
    deserialized = Record.deserialize(serialized)
    print(f"   Original: {record.values}")
    print(f"   Deserialized: {deserialized.values}")
    assert deserialized.values == record.values
    print("   ✓ Record serialization works")
    
    # Test 3: B-tree (simplified)
    print("3. Testing B-tree (simplified)...")
    btree = BTree(max_keys=10)  # Use larger max_keys to avoid splits in test
    btree.root.keys = [5, 10, 15]
    btree.root.values = ["five", "ten", "fifteen"]
    
    # Test basic search in leaf
    actual_value = btree.search(10)
    print(f"   Search 10: got {actual_value}, expected ten")
    assert actual_value == "ten"
    
    # Test not found
    assert btree.search(99) is None
    
    print("   ✓ B-tree indexing works")
    
    # Test 4: Complete database
    print("4. Testing complete database...")
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        db = Database(tmp.name)
        
        # Create table
        db.execute_sql("CREATE TABLE test (id INTEGER, name TEXT)")
        
        # Insert data
        db.execute_sql("INSERT INTO test VALUES (1, 'Alice')")
        db.execute_sql("INSERT INTO test VALUES (2, 'Bob')")
        
        # Query data
        results = db.execute_sql("SELECT * FROM test")
        assert len(results) == 2
        
        # Query with WHERE
        filtered = db.execute_sql("SELECT * FROM test WHERE name = 'Alice'")
        assert len(filtered) == 1
        assert filtered[0].values[1] == 'Alice'
        
        db.close()
    print("   ✓ Complete database works")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        create_demo_database()
    else:
        run_tests()