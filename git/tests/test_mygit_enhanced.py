#!/usr/bin/env python3
"""
Test script for enhanced MyGit branching functionality.
"""

import tempfile
import os
import sys
from pathlib import Path

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'starter'))
from mygit import MyGit


def test_git_branching():
    """Test the enhanced Git functionality including branching."""
    print("Testing Enhanced MyGit with Branching...")
    
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
            print("✅ Repository initialized")
            
            # Test 2: Add initial files
            print("\n2. Testing initial commit setup...")
            with open("README.md", "w") as f:
                f.write("# Test Repository\n")
            
            git.add("README.md")
            commit1 = git.commit("Initial commit", "tester")
            assert commit1 is not None, "Initial commit failed"
            print(f"✅ Initial commit: {commit1[:8]}")
            
            # Test 3: Create new branch
            print("\n3. Testing branch creation...")
            git.branch("feature-branch")
            branches = git.list_branches()
            assert "feature-branch" in branches, "Branch not created"
            assert "main" in branches, "Main branch missing"
            print("✅ Branch created successfully")
            
            # Test 4: Switch branches
            print("\n4. Testing branch checkout...")
            git.checkout("feature-branch")
            assert git.current_branch == "feature-branch", "Branch checkout failed"
            print("✅ Branch checkout successful")
            
            # Test 5: Make changes on feature branch
            print("\n5. Testing changes on feature branch...")
            with open("feature.txt", "w") as f:
                f.write("This is a feature file\n")
            
            git.add("feature.txt")
            commit2 = git.commit("Add feature file", "tester")
            assert commit2 is not None, "Feature commit failed"
            print(f"✅ Feature commit: {commit2[:8]}")
            
            # Test 6: Switch back to main
            print("\n6. Testing switch back to main...")
            git.checkout("main")
            assert git.current_branch == "main", "Switch to main failed"
            # Note: In this simplified implementation, files persist in working directory
            # In real Git, checkout would update the working directory
            print("✅ Switched back to main")
            
            # Test 7: Create another branch with checkout -b
            print("\n7. Testing checkout -b...")
            git.checkout("hotfix-branch", create=True)
            assert git.current_branch == "hotfix-branch", "Checkout -b failed"
            assert "hotfix-branch" in git.list_branches(), "Hotfix branch not created"
            print("✅ Checkout -b successful")
            
            # Test 8: List branches
            print("\n8. Testing branch listing...")
            branches = git.list_branches()
            expected_branches = {"main", "feature-branch", "hotfix-branch"}
            assert expected_branches.issubset(set(branches)), f"Expected {expected_branches}, got {branches}"
            print(f"✅ Branches: {', '.join(branches)}")
            
            # Test 9: Basic merge (fast-forward)
            print("\n9. Testing merge...")
            git.checkout("main")
            # This merge should work since hotfix-branch starts from main
            result = git.merge("hotfix-branch")
            assert result, "Merge failed"
            print("✅ Merge successful")
            
            # Test 10: Show diff (simplified)
            print("\n10. Testing diff...")
            diff_result = git.diff(commit1, commit2)
            assert "Diff" in diff_result, "Diff command failed"
            print("✅ Diff command works")
            
            print("\n🎉 All enhanced Git tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    test_git_branching()