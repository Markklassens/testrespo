#!/usr/bin/env python3
"""
Test runner for MarketMindAI API modular tests
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print("STDOUT:", result.stdout)
    else:
        print(f"❌ {description} - FAILED")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    
    return result.returncode == 0

def main():
    """Main test runner"""
    # Change to backend directory
    os.chdir('/app/backend')
    
    # Test commands
    test_commands = [
        ("python -m pytest tests/test_user_routes.py -v", "User Routes Tests"),
        ("python -m pytest tests/test_admin_routes.py -v", "Admin Routes Tests"),
        ("python -m pytest tests/test_superadmin_routes.py -v", "Superadmin Routes Tests"),
        ("python -m pytest tests/test_tools_routes.py -v", "Tools Routes Tests"),
        ("python -m pytest tests/test_blogs_routes.py -v", "Blogs Routes Tests"),
        ("python -m pytest tests/test_integration.py -v", "Integration Tests"),
        ("python -m pytest tests/ -v --tb=short", "All Tests with Short Traceback"),
        ("python -m pytest tests/ --cov=. --cov-report=html", "Coverage Report"),
    ]
    
    print("🚀 Starting MarketMindAI API Modular Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for command, description in test_commands:
        if run_command(command, description):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed > 0:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()