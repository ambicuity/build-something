# Build Your Own Git

Learn how version control systems work by building a simplified version of Git from scratch. You'll implement the core concepts that power modern software development: repositories, commits, branching, and merging.

## 🎯 What You'll Learn

- How Git stores data using content-addressable storage
- The structure of Git objects (blobs, trees, commits)
- How to implement hashing and object storage
- Basic version control operations (add, commit, checkout)
- Simple branching and merging algorithms

## 📋 Prerequisites

- Basic understanding of file systems and directories
- Familiarity with hash functions (SHA-1 concept)
- Knowledge of basic data structures (trees, linked lists)
- Programming experience in Python, Go, or C

## 🏗️ Architecture Overview

Our Git implementation consists of these core components:

1. **Object Store**: Content-addressable storage for all Git objects
2. **Index**: Staging area for tracking changes
3. **References**: Branch and tag management
4. **Working Directory**: File system interface

```
.mygit/
├── objects/          # Content-addressable object storage
│   ├── 01/
│   │   └── 23abc...  # Object files (first 2 chars = folder)
├── refs/
│   ├── heads/        # Branch references
│   └── tags/         # Tag references
├── index             # Staging area
└── HEAD              # Current branch reference
```

## 🚀 Implementation Steps

### Step 1: Initialize Repository Structure

First, let's create the basic repository structure and implement the `init` command.

**Theory**: Git repositories are just directories with a special `.git` folder that contains all the version control metadata.

```python
import os
import json
import hashlib
from pathlib import Path

class MyGit:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.git_dir = self.repo_path / ".mygit"
        
    def init(self):
        """Initialize a new repository"""
        # Create directory structure
        (self.git_dir / "objects").mkdir(parents=True, exist_ok=True)
        (self.git_dir / "refs" / "heads").mkdir(parents=True, exist_ok=True)
        (self.git_dir / "refs" / "tags").mkdir(parents=True, exist_ok=True)
        
        # Initialize HEAD to point to main branch
        (self.git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        
        # Create empty index
        (self.git_dir / "index").write_text(json.dumps([]))
        
        print(f"Initialized empty repository in {self.git_dir}")
```

**Test it**:
```python
git = MyGit()
git.init()
```

### Step 2: Implement Object Storage

Git uses a content-addressable storage system where each object is identified by its SHA-1 hash.

**Theory**: Every piece of data in Git (files, directories, commits) is stored as an object with a unique hash. This ensures data integrity and enables efficient storage.

```python
import zlib

class MyGit:
    # ... previous code ...
    
    def hash_object(self, data, obj_type="blob"):
        """Create a Git object hash"""
        # Git object format: "<type> <size>\0<content>"
        header = f"{obj_type} {len(data)}\0"
        store = header.encode() + data
        
        # Calculate SHA-1 hash
        sha1 = hashlib.sha1(store).hexdigest()
        
        # Store object (first 2 chars = directory, rest = filename)
        obj_dir = self.git_dir / "objects" / sha1[:2]
        obj_dir.mkdir(exist_ok=True)
        
        obj_file = obj_dir / sha1[2:]
        if not obj_file.exists():
            # Compress and store
            compressed = zlib.compress(store)
            obj_file.write_bytes(compressed)
            
        return sha1
    
    def read_object(self, sha1):
        """Read an object from storage"""
        obj_file = self.git_dir / "objects" / sha1[:2] / sha1[2:]
        
        if not obj_file.exists():
            raise ValueError(f"Object {sha1} not found")
            
        # Decompress and parse
        compressed = obj_file.read_bytes()
        data = zlib.decompress(compressed)
        
        # Split header and content
        null_idx = data.find(b'\0')
        header = data[:null_idx].decode()
        content = data[null_idx + 1:]
        
        obj_type, size = header.split(' ')
        return obj_type, content
```

**Test it**:
```python
# Store a file
with open("test.txt", "w") as f:
    f.write("Hello, Git!")

with open("test.txt", "rb") as f:
    content = f.read()

git = MyGit()
git.init()
hash_val = git.hash_object(content)
print(f"Object hash: {hash_val}")

# Read it back
obj_type, data = git.read_object(hash_val)
print(f"Type: {obj_type}, Content: {data.decode()}")
```

### Step 3: Implement the Index (Staging Area)

The index tracks which files are staged for the next commit.

**Theory**: Git's index is a binary file that contains a snapshot of the working directory. It serves as a staging area between your working directory and the repository.

```python
import stat
import time

class IndexEntry:
    def __init__(self, path, hash_val, mode, size, mtime):
        self.path = path
        self.hash = hash_val
        self.mode = mode
        self.size = size
        self.mtime = mtime
    
    def to_dict(self):
        return {
            'path': str(self.path),
            'hash': self.hash,
            'mode': self.mode,
            'size': self.size,
            'mtime': self.mtime
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            Path(data['path']),
            data['hash'],
            data['mode'],
            data['size'],
            data['mtime']
        )

class MyGit:
    # ... previous code ...
    
    def read_index(self):
        """Read the current index"""
        index_file = self.git_dir / "index"
        if not index_file.exists():
            return []
            
        data = json.loads(index_file.read_text())
        return [IndexEntry.from_dict(entry) for entry in data]
    
    def write_index(self, entries):
        """Write entries to the index"""
        index_file = self.git_dir / "index"
        data = [entry.to_dict() for entry in entries]
        index_file.write_text(json.dumps(data, indent=2))
    
    def add(self, file_path):
        """Add a file to the index"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        # Read file content and create blob
        content = file_path.read_bytes()
        hash_val = self.hash_object(content, "blob")
        
        # Get file stats
        stats = file_path.stat()
        
        # Create index entry
        entry = IndexEntry(
            path=file_path.relative_to(self.repo_path),
            hash_val=hash_val,
            mode=stats.st_mode,
            size=stats.st_size,
            mtime=stats.st_mtime
        )
        
        # Update index
        entries = self.read_index()
        
        # Remove existing entry for this file
        entries = [e for e in entries if e.path != entry.path]
        entries.append(entry)
        entries.sort(key=lambda e: str(e.path))
        
        self.write_index(entries)
        print(f"Added {file_path} to index")
```

**Test it**:
```python
# Create and add a file
with open("hello.txt", "w") as f:
    f.write("Hello, World!")

git = MyGit()
git.init()
git.add("hello.txt")

# Check index
entries = git.read_index()
for entry in entries:
    print(f"Staged: {entry.path} -> {entry.hash}")
```

### Step 4: Implement Commits

A commit is a snapshot of the repository at a point in time, with metadata about the author, message, and parent commits.

**Theory**: Commits are Git objects that point to a tree object (representing the directory structure) and contain metadata like author, timestamp, and commit message.

```python
import getpass
from datetime import datetime

class MyGit:
    # ... previous code ...
    
    def create_tree(self, entries):
        """Create a tree object from index entries"""
        tree_entries = []
        
        for entry in entries:
            # Tree entry format: "<mode> <name>\0<hash_bytes>"
            mode = oct(entry.mode)[2:]  # Remove '0o' prefix
            name = entry.path.name
            hash_bytes = bytes.fromhex(entry.hash)
            
            tree_entry = f"{mode} {name}\0".encode() + hash_bytes
            tree_entries.append(tree_entry)
        
        tree_data = b''.join(tree_entries)
        return self.hash_object(tree_data, "tree")
    
    def commit(self, message, author=None):
        """Create a new commit"""
        if author is None:
            author = getpass.getuser()
        
        # Read staged files
        entries = self.read_index()
        if not entries:
            print("Nothing to commit")
            return None
        
        # Create tree from staged files
        tree_hash = self.create_tree(entries)
        
        # Get parent commit
        parent = self.get_current_commit()
        
        # Create commit object
        timestamp = int(datetime.now().timestamp())
        commit_content = f"tree {tree_hash}\n"
        
        if parent:
            commit_content += f"parent {parent}\n"
        
        commit_content += f"author {author} <{author}@example.com> {timestamp} +0000\n"
        commit_content += f"committer {author} <{author}@example.com> {timestamp} +0000\n"
        commit_content += f"\n{message}\n"
        
        commit_hash = self.hash_object(commit_content.encode(), "commit")
        
        # Update current branch reference
        current_branch = self.get_current_branch()
        branch_ref = self.git_dir / "refs" / "heads" / current_branch
        branch_ref.write_text(commit_hash)
        
        print(f"Committed {commit_hash[:8]}: {message}")
        return commit_hash
    
    def get_current_branch(self):
        """Get the name of the current branch"""
        head = (self.git_dir / "HEAD").read_text().strip()
        if head.startswith("ref: refs/heads/"):
            return head[16:]  # Remove "ref: refs/heads/"
        return "main"  # Default branch
    
    def get_current_commit(self):
        """Get the hash of the current commit"""
        current_branch = self.get_current_branch()
        branch_ref = self.git_dir / "refs" / "heads" / current_branch
        
        if branch_ref.exists():
            return branch_ref.read_text().strip()
        return None
```

**Test it**:
```python
# Create, add, and commit files
with open("file1.txt", "w") as f:
    f.write("First file")
    
with open("file2.txt", "w") as f:
    f.write("Second file")

git = MyGit()
git.init()
git.add("file1.txt")
git.add("file2.txt")
commit_hash = git.commit("Initial commit")

print(f"Created commit: {commit_hash}")
```

### Step 5: Implement Status and Log

Add commands to see the current repository state and commit history.

```python
class MyGit:
    # ... previous code ...
    
    def status(self):
        """Show the status of the working directory"""
        print("On branch", self.get_current_branch())
        
        current_commit = self.get_current_commit()
        if current_commit:
            print(f"Current commit: {current_commit[:8]}")
        else:
            print("No commits yet")
        
        # Check for staged files
        entries = self.read_index()
        if entries:
            print("\nStaged files:")
            for entry in entries:
                print(f"  {entry.path}")
        else:
            print("\nNo staged files")
    
    def log(self, max_commits=10):
        """Show commit history"""
        current = self.get_current_commit()
        count = 0
        
        while current and count < max_commits:
            obj_type, commit_data = self.read_object(current)
            if obj_type != "commit":
                break
                
            lines = commit_data.decode().split('\n')
            
            # Parse commit data
            tree_hash = None
            parent = None
            author = None
            message_lines = []
            in_message = False
            
            for line in lines:
                if line.startswith('tree '):
                    tree_hash = line[5:]
                elif line.startswith('parent '):
                    parent = line[7:]
                elif line.startswith('author '):
                    author = line[7:]
                elif line == '':
                    in_message = True
                elif in_message:
                    message_lines.append(line)
            
            print(f"commit {current}")
            if author:
                print(f"Author: {author}")
            if message_lines:
                print(f"Message: {message_lines[0]}")
            print()
            
            current = parent
            count += 1
```

## 🧪 Testing Your Implementation

Create a test script to verify all functionality:

```python
def test_git_implementation():
    import tempfile
    import os
    
    # Test in temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        git = MyGit()
        
        # Test init
        git.init()
        assert (Path(".mygit")).exists()
        
        # Test add and commit
        with open("test.txt", "w") as f:
            f.write("Test content")
        
        git.add("test.txt")
        commit_hash = git.commit("Test commit")
        assert commit_hash is not None
        
        # Test status and log
        git.status()
        git.log()
        
        print("All tests passed!")

if __name__ == "__main__":
    test_git_implementation()
```

## 🎯 Challenges to Extend Your Implementation

1. **Branching**: Implement `checkout -b` to create and switch branches
2. **Merging**: Add basic three-way merge functionality
3. **Diff**: Show differences between commits or working directory
4. **Remote**: Add basic push/pull operations (local filesystem)
5. **Ignore**: Implement `.gitignore` functionality

## 📚 Key Concepts Learned

- **Content-Addressable Storage**: How Git ensures data integrity
- **Object Model**: The four types of Git objects (blob, tree, commit, tag)
- **Staging Area**: The role of the index in Git workflows
- **DAG Structure**: How commits form a directed acyclic graph
- **Hashing**: Using SHA-1 for object identification

## 🔗 Further Reading

- [Git Internals Documentation](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [The Git Object Model](https://github.com/git/git/blob/master/Documentation/technical/api-object-access.txt)
- Content-addressable storage systems and their applications

---

**Congratulations!** You've built a working version control system. You now understand the core concepts that make Git so powerful and reliable.