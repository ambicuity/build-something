#!/usr/bin/env python3
"""
Test script for MyGit implementation
"""

import tempfile
import os
from pathlib import Path
import sys

# Add the starter directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

from mygit import MyGit


def test_git_implementation():
    """Test the basic Git functionality"""
    print("Testing MyGit implementation...")
    
    # Test in temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            git = MyGit()
            
            # Test 1: Initialize repository
            print("\n1. Testing init...")
            git.init()
            assert Path(".mygit").exists(), "Git directory not created"
            assert Path(".mygit/objects").exists(), "Objects directory not created"
            print("✅ Repository initialized successfully")
            
            # Test 2: Add files
            print("\n2. Testing add...")
            with open("test1.txt", "w") as f:
                f.write("Hello, World!")
            
            with open("test2.txt", "w") as f:
                f.write("This is a second file.")
            
            git.add("test1.txt")
            git.add("test2.txt")
            
            entries = git.read_index()
            assert len(entries) == 2, "Files not added to index"
            print("✅ Files added successfully")
            
            # Test 3: Create commit
            print("\n3. Testing commit...")
            commit_hash = git.commit("Initial commit", author="tester")
            assert commit_hash is not None, "Commit failed"
            print(f"✅ Commit created: {commit_hash[:8]}")
            
            # Test 4: Check status
            print("\n4. Testing status...")
            git.status()
            print("✅ Status command works")
            
            # Test 5: View log
            print("\n5. Testing log...")
            git.log()
            print("✅ Log command works")
            
            # Test 6: Add more files and commit
            print("\n6. Testing second commit...")
            with open("test3.txt", "w") as f:
                f.write("Third file for second commit")
            
            git.add("test3.txt")
            second_commit = git.commit("Second commit", author="tester")
            assert second_commit is not None, "Second commit failed"
            print(f"✅ Second commit created: {second_commit[:8]}")
            
            # Test 7: Verify commit chain
            print("\n7. Testing commit history...")
            git.log(max_commits=5)
            print("✅ Commit history verified")
            
            print("\n🎉 All tests passed! MyGit implementation is working correctly.")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise
        finally:
            os.chdir(original_cwd)


def interactive_demo():
    """Interactive demonstration of MyGit"""
    print("MyGit Interactive Demo")
    print("======================")
    
    # Create demo directory
    demo_dir = Path("mygit_demo")
    if demo_dir.exists():
        import shutil
        shutil.rmtree(demo_dir)
    
    demo_dir.mkdir()
    os.chdir(demo_dir)
    
    git = MyGit()
    
    print("\n1. Initializing repository...")
    git.init()
    
    print("\n2. Creating some files...")
    with open("README.md", "w") as f:
        f.write("# My Project\n\nThis is a demo project for MyGit!")
    
    with open("hello.py", "w") as f:
        f.write('print("Hello from MyGit!")\n')
    
    with open("data.txt", "w") as f:
        f.write("Some important data\nLine 2\nLine 3\n")
    
    print("\n3. Checking status...")
    git.status()
    
    print("\n4. Adding files...")
    git.add("README.md")
    git.add("hello.py")
    git.add("data.txt")
    
    print("\n5. Checking status after add...")
    git.status()
    
    print("\n6. Creating first commit...")
    git.commit("Initial project setup")
    
    print("\n7. Modifying a file...")
    with open("README.md", "a") as f:
        f.write("\n## Updates\n\n- Added more content")
    
    print("\n8. Adding modified file...")
    git.add("README.md")
    
    print("\n9. Creating second commit...")
    git.commit("Updated README with more content")
    
    print("\n10. Viewing commit history...")
    git.log()
    
    print("\nDemo completed! Check the 'mygit_demo' directory to see the results.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MyGit implementation")
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    
    args = parser.parse_args()
    
    if args.demo:
        interactive_demo()
    else:
        test_git_implementation()