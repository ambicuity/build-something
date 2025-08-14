#!/usr/bin/env python3
"""
MyGit - A simplified Git implementation for learning purposes

This is a basic version control system that demonstrates the core concepts
of Git without external dependencies.
"""

import os
import json
import hashlib
import zlib
import stat
import time
import getpass
from pathlib import Path
from datetime import datetime


class IndexEntry:
    """Represents a file in the Git index (staging area)"""
    
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
    """A simplified Git implementation"""
    
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
    
    def hash_object(self, data, obj_type="blob"):
        """Create a Git object hash and store the object"""
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
            try:
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
            except ValueError:
                break


def main():
    """Command line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mygit.py <command> [args...]")
        print("Commands: init, add <file>, commit <message>, status, log")
        return
    
    git = MyGit()
    command = sys.argv[1]
    
    try:
        if command == "init":
            git.init()
        elif command == "add":
            if len(sys.argv) < 3:
                print("Usage: python mygit.py add <file>")
                return
            git.add(sys.argv[2])
        elif command == "commit":
            if len(sys.argv) < 3:
                print("Usage: python mygit.py commit <message>")
                return
            git.commit(sys.argv[2])
        elif command == "status":
            git.status()
        elif command == "log":
            git.log()
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()