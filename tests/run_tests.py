"""
Comprehensive Test Runner for Super Admin Tools Testing
======================================================

This is the main test runner that orchestrates all testing modules:
1. Unit tests for individual components
2. Functional tests for end-to-end workflows  
3. Performance tests for scalability
4. Integration tests for discover page
5. Detailed reporting and analysis

Author: MarketMindAI Testing Suite
Version: 1.0.0
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import traceback

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestResult:
    """Test result container"""
    
    def __init__(self, name: str, status: str, duration: float, details: Optional[Dict] = None):
        self.name = name
        self.status = status  # 'passed', 'failed', 'skipped'
        self.duration = duration
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'duration': self.duration,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class TestReporter:
    """Test reporter for generating detailed reports"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def start_testing(self):
        """Start testing session"""
        self.start_time = datetime.now()
        print(f"\n🚀 Starting comprehensive test session at {self.start_time}")
    
    def end_testing(self):
        """End testing session"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"\n🏁 Testing session completed in {duration:.2f} seconds")
    
    def add_result(self, result: TestResult):
        """Add test result"""
        self.results.append(result)
        
        status_symbol = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
        print(f"{status_symbol} {result.name}: {result.status.upper()} ({result.duration:.2f}s)")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.start_time or not self.end_time:
            return {}
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        passed = len([r for r in self.results if r.status == "passed"])
        failed = len([r for r in self.results if r.status == "failed"])
        skipped = len([r for r in self.results if r.status == "skipped"])
        total = len(self.results)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Generate detailed report
        report = {
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'success_rate': success_rate,
                'total_duration': total_duration,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            },
            'results': [r.to_dict() for r in self.results],
            'failed_tests': [r.to_dict() for r in self.results if r.status == "failed"]
        }
        
        return report
    
    def print_summary(self):
        """Print test summary"""
        if not self.results:
            print("\n📋 No tests were executed")
            return
        
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "passed"])
        failed = len([r for r in self.results if r.status == "failed"])
        skipped = len([r for r in self.results if r.status == "skipped"])
        
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"Total Tests:  {total}")
        print(f"Passed:       {passed} ✅")
        print(f"Failed:       {failed} ❌")
        print(f"Skipped:      {skipped} ⚠️")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result.status == "failed":
                    print(f"  - {result.name}")
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        print(f"\nTotal Duration: {total_duration:.2f} seconds")
        print("="*80)

class SuperAdminToolsTestRunner:
    """Main test runner for Super Admin Tools"""
    
    def __init__(self):
        self.reporter = TestReporter()
        self.test_modules = {
            'unit': 'test_unit_tools.py',
            'functional': 'test_super_admin_tools.py',
            'performance': 'test_performance.py'
        }
    
    def run_unit_tests(self) -> TestResult:
        """Run unit tests"""
        print("\n🧪 Running Unit Tests...")
        
        start_time = time.time()
        try:
            # Import and run unit tests
            from test_unit_tools import create_test_suite
            import unittest
            
            # Create test suite
            suite = create_test_suite()
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
            result = runner.run(suite)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.wasSuccessful():
                return TestResult(
                    name="Unit Tests",
                    status="passed",
                    duration=duration,
                    details={
                        'tests_run': result.testsRun,
                        'failures': len(result.failures),
                        'errors': len(result.errors)
                    }
                )
            else:
                return TestResult(
                    name="Unit Tests",
                    status="failed",
                    duration=duration,
                    details={
                        'tests_run': result.testsRun,
                        'failures': len(result.failures),
                        'errors': len(result.errors),
                        'failure_details': [str(f) for f in result.failures],
                        'error_details': [str(e) for e in result.errors]
                    }
                )
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return TestResult(
                name="Unit Tests",
                status="failed",
                duration=duration,
                details={
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
    
    def run_functional_tests(self) -> TestResult:
        """Run functional tests"""
        print("\n🔧 Running Functional Tests...")
        
        start_time = time.time()
        try:
            # Import and run functional tests
            from test_super_admin_tools import SuperAdminToolsTest
            
            # Create test instance
            test_suite = SuperAdminToolsTest()
            
            # Run tests
            success = test_suite.run_all_tests()
            
            end_time = time.time()
            duration = end_time - start_time
            
            return TestResult(
                name="Functional Tests",
                status="passed" if success else "failed",
                duration=duration,
                details={
                    'comprehensive_test': success
                }
            )
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return TestResult(
                name="Functional Tests",
                status="failed",
                duration=duration,
                details={
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
    
    def run_performance_tests(self) -> TestResult:
        """Run performance tests"""
        print("\n⚡ Running Performance Tests...")
        
        start_time = time.time()
        try:
            # Import and run performance tests
            from test_performance import PerformanceTest
            
            # Create test instance
            test_suite = PerformanceTest()
            
            # Run tests
            results = test_suite.run_all_performance_tests()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Determine success based on results
            success = bool(results and len(results) > 0)
            
            return TestResult(
                name="Performance Tests",
                status="passed" if success else "failed",
                duration=duration,
                details={
                    'performance_results': results
                }
            )
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return TestResult(
                name="Performance Tests",
                status="failed",
                duration=duration,
                details={
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
    
    def run_discover_page_integration_test(self) -> TestResult:
        """Run discover page integration test"""
        print("\n🔍 Running Discover Page Integration Test...")
        
        start_time = time.time()
        try:
            # Import required modules
            from test_super_admin_tools import TestClient, AuthManager, TestDataGenerator
            
            client = TestClient()
            auth = AuthManager(client)
            data_generator = TestDataGenerator()
            
            # Get super admin token
            super_admin_token = auth.get_super_admin_token()
            
            # Get categories
            categories_response = client.get("/api/categories")
            if categories_response.status_code != 200:
                raise Exception("Failed to get categories")
            
            categories = categories_response.json()
            if not categories:
                raise Exception("No categories available")
            
            # Create a test tool
            tool_data = data_generator.generate_tool_data("discover-integration")
            tool_data["category_id"] = categories[0]["id"]
            tool_data["is_featured"] = True
            
            create_response = client.post(
                "/api/tools",
                json=tool_data,
                headers=auth.get_auth_headers(super_admin_token)
            )
            
            if create_response.status_code != 200:
                raise Exception("Failed to create test tool")
            
            created_tool = create_response.json()
            tool_id = created_tool["id"]
            
            # Test discover page endpoints
            endpoints_to_test = [
                "/api/tools/search",
                "/api/tools/analytics",
                "/api/categories/analytics"
            ]
            
            endpoint_results = {}
            
            for endpoint in endpoints_to_test:
                response = client.get(endpoint)
                endpoint_results[endpoint] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
            
            # Verify tool appears in search results
            search_response = client.get("/api/tools/search")
            if search_response.status_code == 200:
                search_result = search_response.json()
                tools = search_result.get("tools", [])
                tool_found = any(tool["id"] == tool_id for tool in tools)
                endpoint_results["tool_in_search"] = tool_found
            
            # Clean up
            delete_response = client.delete(
                f"/api/tools/{tool_id}",
                headers=auth.get_auth_headers(super_admin_token)
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Determine success
            all_endpoints_passed = all(
                result.get('success', False) for result in endpoint_results.values()
            )
            
            return TestResult(
                name="Discover Page Integration",
                status="passed" if all_endpoints_passed else "failed",
                duration=duration,
                details={
                    'endpoints_tested': endpoint_results,
                    'tool_created': created_tool["name"],
                    'tool_deleted': delete_response.status_code == 200
                }
            )
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return TestResult(
                name="Discover Page Integration",
                status="failed",
                duration=duration,
                details={
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
    
    def run_all_tests(self, test_types: List[str] = None) -> bool:
        """Run all tests"""
        print("\n" + "="*100)
        print("🧪 SUPER ADMIN TOOLS COMPREHENSIVE TEST SUITE")
        print("="*100)
        
        if test_types is None:
            test_types = ['unit', 'functional', 'performance', 'integration']
        
        # Start testing session
        self.reporter.start_testing()
        
        # Run tests based on requested types
        if 'unit' in test_types:
            result = self.run_unit_tests()
            self.reporter.add_result(result)
        
        if 'functional' in test_types:
            result = self.run_functional_tests()
            self.reporter.add_result(result)
        
        if 'performance' in test_types:
            result = self.run_performance_tests()
            self.reporter.add_result(result)
        
        if 'integration' in test_types:
            result = self.run_discover_page_integration_test()
            self.reporter.add_result(result)
        
        # End testing session
        self.reporter.end_testing()
        
        # Generate and save report
        report = self.reporter.generate_report()
        
        # Save detailed report
        report_file = f"/app/tests/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 Detailed report saved to: {report_file}")
        
        # Print summary
        self.reporter.print_summary()
        
        # Return overall success
        failed_tests = [r for r in self.reporter.results if r.status == "failed"]
        return len(failed_tests) == 0
    
    def run_specific_test(self, test_name: str) -> bool:
        """Run a specific test"""
        test_mapping = {
            'unit': self.run_unit_tests,
            'functional': self.run_functional_tests,
            'performance': self.run_performance_tests,
            'integration': self.run_discover_page_integration_test
        }
        
        if test_name not in test_mapping:
            print(f"❌ Unknown test: {test_name}")
            print(f"Available tests: {list(test_mapping.keys())}")
            return False
        
        self.reporter.start_testing()
        
        result = test_mapping[test_name]()
        self.reporter.add_result(result)
        
        self.reporter.end_testing()
        self.reporter.print_summary()
        
        return result.status == "passed"

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Super Admin Tools Test Runner")
    parser.add_argument(
        '--test-types',
        nargs='+',
        choices=['unit', 'functional', 'performance', 'integration'],
        default=['unit', 'functional', 'integration'],
        help='Test types to run'
    )
    parser.add_argument(
        '--specific-test',
        type=str,
        help='Run a specific test'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (unit and functional)'
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = SuperAdminToolsTestRunner()
    
    # Determine test types
    if args.quick:
        test_types = ['unit', 'functional']
    elif args.specific_test:
        success = runner.run_specific_test(args.specific_test)
        exit(0 if success else 1)
    else:
        test_types = args.test_types
    
    # Run tests
    success = runner.run_all_tests(test_types)
    
    if success:
        print("\n🎉 All tests passed successfully!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)

if __name__ == "__main__":
    main()