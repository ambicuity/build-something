#!/usr/bin/env python3
"""
Master test runner for all build-something projects
Runs comprehensive tests for all implemented components
"""

import sys
import os
import importlib.util
from pathlib import Path

def run_module_test(module_path, test_function_name="run_tests"):
    """Run test function from a specific module"""
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the test function
        if hasattr(module, test_function_name):
            test_func = getattr(module, test_function_name)
            test_func()
            return True
        else:
            print(f"   ⚠ No {test_function_name} function found in {module_path}")
            return False
    except Exception as e:
        print(f"   ❌ Error running tests: {e}")
        return False

def main():
    """Run all tests from all components"""
    print("🚀 Running comprehensive tests for all build-something projects")
    print("=" * 80)
    
    # Get the repository root
    repo_root = Path(__file__).parent
    
    # List of components with their test locations
    components = [
        {
            "name": "Database",
            "path": repo_root / "database" / "starter" / "mydatabase.py",
            "description": "Database management system with B-tree indexing and SQL support"
        },
        {
            "name": "Text Editor", 
            "path": repo_root / "editor" / "starter" / "myeditor.py",
            "description": "Terminal-based text editor with syntax highlighting"
        },
        {
            "name": "Git Version Control",
            "path": repo_root / "git" / "tests" / "test_mygit.py",
            "description": "Git implementation with commits, staging, and history",
            "test_function": "test_git_implementation"
        },
        {
            "name": "HTTP Server",
            "path": repo_root / "http-server" / "starter" / "server.py",
            "description": "Complete HTTP server with routing and static file serving"
        },
        {
            "name": "Shell",
            "path": repo_root / "shell" / "starter" / "myshell.py", 
            "description": "Command-line shell with pipes, redirection, and built-ins"
        },
        {
            "name": "CLI Tools",
            "path": repo_root / "cli-tools" / "starter" / "cli_tools.py",
            "description": "Collection of command-line tools (echo, ls, wc, tail, grep, cat)"
        },
        {
            "name": "Regex Engine",
            "path": repo_root / "regex" / "starter" / "regex_engine.py",
            "description": "Regular expression engine with NFA, quantifiers, and character classes"
        }
    ]
    
    passed_tests = 0
    total_tests = len(components)
    
    # Run tests for each component
    for i, component in enumerate(components, 1):
        print(f"\n{i}. Testing {component['name']}")
        print("-" * 60)
        print(f"   📝 {component['description']}")
        print(f"   📁 {component['path']}")
        
        if not component['path'].exists():
            print(f"   ❌ Component not found: {component['path']}")
            continue
        
        # Change to component directory for proper imports
        original_cwd = os.getcwd()
        component_dir = component['path'].parent
        os.chdir(component_dir)
        
        try:
            # Add component directory to Python path
            sys.path.insert(0, str(component_dir))
            
            # Run the tests
            test_function = component.get('test_function', 'run_tests')
            success = run_module_test(component['path'], test_function)
            
            if success:
                passed_tests += 1
                print(f"   ✅ {component['name']} tests PASSED")
            else:
                print(f"   ❌ {component['name']} tests FAILED")
                
        except Exception as e:
            print(f"   ❌ Error testing {component['name']}: {e}")
        finally:
            # Restore original directory and clean up Python path
            os.chdir(original_cwd)
            if str(component_dir) in sys.path:
                sys.path.remove(str(component_dir))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Everything is working perfectly! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} component(s) have issues that need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())