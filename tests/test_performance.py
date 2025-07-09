"""
Performance Testing Module for Super Admin Tools
===============================================

This module focuses on performance testing of Super Admin tools functionality:
1. Bulk upload performance with large datasets
2. Discover page load times with many tools
3. Search performance with large datasets
4. Database query optimization validation
5. Memory usage monitoring

Author: MarketMindAI Testing Suite
Version: 1.0.0
"""

import time
import psutil
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
import json
import csv
import io
import tempfile
import os
from test_super_admin_tools import TestClient, AuthManager, TestDataGenerator, TestConfig

class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'timestamps': []
        }
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Monitor loop"""
        while self.monitoring:
            self.metrics['cpu_usage'].append(psutil.cpu_percent())
            self.metrics['memory_usage'].append(psutil.virtual_memory().percent)
            self.metrics['timestamps'].append(time.time())
            time.sleep(0.1)  # Monitor every 100ms
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.metrics['cpu_usage']:
            return {}
        
        return {
            'cpu_avg': statistics.mean(self.metrics['cpu_usage']),
            'cpu_max': max(self.metrics['cpu_usage']),
            'memory_avg': statistics.mean(self.metrics['memory_usage']),
            'memory_max': max(self.metrics['memory_usage']),
            'duration': self.metrics['timestamps'][-1] - self.metrics['timestamps'][0] if len(self.metrics['timestamps']) > 1 else 0
        }

class PerformanceTest:
    """Performance testing suite"""
    
    def __init__(self):
        self.client = TestClient()
        self.auth = AuthManager(self.client)
        self.data_generator = TestDataGenerator()
        self.super_admin_token = None
        self.test_categories = []
        self.created_tools = []
        self.monitor = PerformanceMonitor()
    
    def setup(self):
        """Setup test environment"""
        print("Setting up performance test environment...")
        
        # Get super admin token
        self.super_admin_token = self.auth.get_super_admin_token()
        
        # Get test categories
        response = self.client.get("/api/categories")
        if response.status_code == 200:
            self.test_categories = response.json()
        
        print(f"✅ Setup complete - Found {len(self.test_categories)} categories")
    
    def cleanup(self):
        """Cleanup test environment"""
        print("Cleaning up performance test environment...")
        
        # Delete created tools
        for tool_id in self.created_tools:
            try:
                self.client.delete(
                    f"/api/tools/{tool_id}",
                    headers=self.auth.get_auth_headers(self.super_admin_token)
                )
            except:
                pass
        
        self.created_tools.clear()
        print("✅ Cleanup complete")
    
    def test_bulk_upload_performance(self, sizes: List[int] = [10, 50, 100, 250]) -> Dict[str, Any]:
        """Test bulk upload performance with different sizes"""
        print("\n" + "="*80)
        print("BULK UPLOAD PERFORMANCE TEST")
        print("="*80)
        
        if not self.test_categories:
            print("❌ No categories available for testing")
            return {}
        
        category_id = self.test_categories[0]["id"]
        results = {}
        
        for size in sizes:
            print(f"\n--- Testing bulk upload with {size} tools ---")
            
            # Generate CSV data
            csv_data = self.data_generator.generate_csv_data(size)
            
            # Add category_id to CSV data
            csv_lines = csv_data.split('\n')
            headers = csv_lines[0].split(',')
            headers.append('category_id')
            csv_lines[0] = ','.join(headers)
            
            for i in range(1, len(csv_lines)):
                if csv_lines[i].strip():
                    csv_lines[i] += f",{category_id}"
            
            modified_csv = '\n'.join(csv_lines)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(modified_csv)
                tmp_file_path = tmp_file.name
            
            try:
                # Start monitoring
                self.monitor.start_monitoring()
                
                # Measure upload time
                start_time = time.time()
                
                with open(tmp_file_path, 'rb') as file:
                    response = self.client.post(
                        "/api/tools/bulk-upload",
                        files={"file": (f"test_tools_{size}.csv", file, "text/csv")},
                        headers=self.auth.get_auth_headers(self.super_admin_token)
                    )
                
                end_time = time.time()
                upload_time = end_time - start_time
                
                # Stop monitoring
                self.monitor.stop_monitoring()
                
                # Get performance stats
                perf_stats = self.monitor.get_stats()
                
                # Process results
                if response.status_code == 200:
                    upload_result = response.json()
                    created_count = upload_result.get("created_count", 0)
                    
                    results[size] = {
                        'status': 'success',
                        'upload_time': upload_time,
                        'created_count': created_count,
                        'tools_per_second': created_count / upload_time if upload_time > 0 else 0,
                        'performance': perf_stats
                    }
                    
                    print(f"✅ Upload completed in {upload_time:.2f}s - {created_count} tools created")
                    print(f"   Rate: {created_count / upload_time:.2f} tools/second")
                    print(f"   CPU: {perf_stats.get('cpu_avg', 0):.1f}% avg, {perf_stats.get('cpu_max', 0):.1f}% max")
                    print(f"   Memory: {perf_stats.get('memory_avg', 0):.1f}% avg, {perf_stats.get('memory_max', 0):.1f}% max")
                    
                    # Store tool IDs for cleanup
                    tools_response = self.client.get("/api/tools")
                    if tools_response.status_code == 200:
                        all_tools = tools_response.json()
                        for tool in all_tools:
                            if tool["name"] in upload_result.get("created_tools", []):
                                self.created_tools.append(tool["id"])
                else:
                    results[size] = {
                        'status': 'failed',
                        'error': response.text,
                        'upload_time': upload_time
                    }
                    print(f"❌ Upload failed: {response.text}")
                
            finally:
                # Clean up temp file
                os.unlink(tmp_file_path)
                # Reset monitor
                self.monitor = PerformanceMonitor()
        
        return results
    
    def test_discover_page_performance(self, tool_counts: List[int] = [100, 500, 1000]) -> Dict[str, Any]:
        """Test discover page performance with different tool counts"""
        print("\n" + "="*80)
        print("DISCOVER PAGE PERFORMANCE TEST")
        print("="*80)
        
        results = {}
        
        for count in tool_counts:
            print(f"\n--- Testing discover page with {count} tools ---")
            
            # Ensure we have enough tools
            current_tools_response = self.client.get("/api/tools")
            if current_tools_response.status_code == 200:
                current_count = len(current_tools_response.json())
                print(f"Current tools in database: {current_count}")
                
                # Create additional tools if needed
                if current_count < count:
                    tools_needed = count - current_count
                    print(f"Creating {tools_needed} additional tools...")
                    
                    # Use bulk upload to create tools quickly
                    self._create_tools_bulk(tools_needed)
            
            # Test different discover page endpoints
            endpoints = [
                ("/api/tools/search", "Search endpoint"),
                ("/api/tools/search?per_page=50", "Search with pagination"),
                ("/api/tools/search?is_featured=true", "Search featured"),
                ("/api/tools/search?sort_by=rating", "Search by rating"),
                ("/api/tools/analytics", "Analytics endpoint"),
                ("/api/categories/analytics", "Categories analytics")
            ]
            
            endpoint_results = {}
            
            for endpoint, description in endpoints:
                print(f"  Testing {description}...")
                
                # Start monitoring
                self.monitor.start_monitoring()
                
                # Measure response time
                start_time = time.time()
                response = self.client.get(endpoint)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Stop monitoring
                self.monitor.stop_monitoring()
                
                # Get performance stats
                perf_stats = self.monitor.get_stats()
                
                if response.status_code == 200:
                    endpoint_results[endpoint] = {
                        'status': 'success',
                        'response_time': response_time,
                        'response_size': len(response.content),
                        'performance': perf_stats
                    }
                    print(f"    ✅ {response_time:.3f}s - {len(response.content)} bytes")
                else:
                    endpoint_results[endpoint] = {
                        'status': 'failed',
                        'response_time': response_time,
                        'error': response.text
                    }
                    print(f"    ❌ {response_time:.3f}s - Failed: {response.text}")
                
                # Reset monitor
                self.monitor = PerformanceMonitor()
            
            results[count] = endpoint_results
        
        return results
    
    def test_concurrent_access_performance(self, concurrent_users: int = 10, requests_per_user: int = 10) -> Dict[str, Any]:
        """Test concurrent access performance"""
        print("\n" + "="*80)
        print(f"CONCURRENT ACCESS PERFORMANCE TEST ({concurrent_users} users, {requests_per_user} requests each)")
        print("="*80)
        
        def make_concurrent_request(user_id: int) -> List[Dict[str, Any]]:
            """Make concurrent requests for a user"""
            client = TestClient()
            results = []
            
            for request_id in range(requests_per_user):
                start_time = time.time()
                response = client.get("/api/tools/search?per_page=20")
                end_time = time.time()
                
                results.append({
                    'user_id': user_id,
                    'request_id': request_id,
                    'response_time': end_time - start_time,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                })
            
            return results
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Execute concurrent requests
        start_time = time.time()
        all_results = []
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_concurrent_request, user_id) for user_id in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"❌ Concurrent request failed: {e}")
        
        end_time = time.time()
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Analyze results
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r['success'])
        failed_requests = total_requests - successful_requests
        
        response_times = [r['response_time'] for r in all_results if r['success']]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            total_time = end_time - start_time
            
            results = {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': successful_requests / total_requests * 100,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'min_response_time': min_response_time,
                'total_time': total_time,
                'requests_per_second': total_requests / total_time,
                'performance': self.monitor.get_stats()
            }
            
            print(f"✅ Concurrent test completed:")
            print(f"   Total requests: {total_requests}")
            print(f"   Successful: {successful_requests}")
            print(f"   Failed: {failed_requests}")
            print(f"   Success rate: {results['success_rate']:.1f}%")
            print(f"   Avg response time: {avg_response_time:.3f}s")
            print(f"   Max response time: {max_response_time:.3f}s")
            print(f"   Min response time: {min_response_time:.3f}s")
            print(f"   Requests/second: {results['requests_per_second']:.2f}")
            
            return results
        
        return {'error': 'No successful requests'}
    
    def _create_tools_bulk(self, count: int):
        """Create tools in bulk for testing"""
        if not self.test_categories:
            return
        
        category_id = self.test_categories[0]["id"]
        
        # Generate CSV data
        csv_data = self.data_generator.generate_csv_data(count)
        
        # Add category_id to CSV data
        csv_lines = csv_data.split('\n')
        headers = csv_lines[0].split(',')
        headers.append('category_id')
        csv_lines[0] = ','.join(headers)
        
        for i in range(1, len(csv_lines)):
            if csv_lines[i].strip():
                csv_lines[i] += f",{category_id}"
        
        modified_csv = '\n'.join(csv_lines)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(modified_csv)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as file:
                response = self.client.post(
                    "/api/tools/bulk-upload",
                    files={"file": (f"perf_test_{count}.csv", file, "text/csv")},
                    headers=self.auth.get_auth_headers(self.super_admin_token)
                )
            
            if response.status_code == 200:
                upload_result = response.json()
                # Store tool IDs for cleanup
                tools_response = self.client.get("/api/tools")
                if tools_response.status_code == 200:
                    all_tools = tools_response.json()
                    for tool in all_tools:
                        if tool["name"] in upload_result.get("created_tools", []):
                            self.created_tools.append(tool["id"])
        
        finally:
            os.unlink(tmp_file_path)
    
    def run_all_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        print("\n" + "="*100)
        print("SUPER ADMIN TOOLS PERFORMANCE TEST SUITE")
        print("="*100)
        
        try:
            # Setup
            self.setup()
            
            # Run performance tests
            results = {}
            
            # Bulk upload performance
            print("\n🚀 Running bulk upload performance tests...")
            results['bulk_upload'] = self.test_bulk_upload_performance()
            
            # Discover page performance  
            print("\n🚀 Running discover page performance tests...")
            results['discover_page'] = self.test_discover_page_performance()
            
            # Concurrent access performance
            print("\n🚀 Running concurrent access performance tests...")
            results['concurrent_access'] = self.test_concurrent_access_performance()
            
            # Generate performance report
            self._generate_performance_report(results)
            
            return results
            
        except Exception as e:
            print(f"❌ Performance test execution failed: {e}")
            return {}
        finally:
            # Cleanup
            self.cleanup()
    
    def _generate_performance_report(self, results: Dict[str, Any]):
        """Generate performance report"""
        print("\n" + "="*100)
        print("PERFORMANCE TEST REPORT")
        print("="*100)
        
        # Bulk upload report
        if 'bulk_upload' in results:
            print("\n📊 BULK UPLOAD PERFORMANCE:")
            print("-" * 50)
            for size, result in results['bulk_upload'].items():
                if result['status'] == 'success':
                    print(f"  {size:>3} tools: {result['upload_time']:>6.2f}s ({result['tools_per_second']:>5.1f} tools/s)")
                else:
                    print(f"  {size:>3} tools: FAILED")
        
        # Discover page report
        if 'discover_page' in results:
            print("\n📊 DISCOVER PAGE PERFORMANCE:")
            print("-" * 50)
            for count, endpoints in results['discover_page'].items():
                print(f"  With {count} tools:")
                for endpoint, result in endpoints.items():
                    if result['status'] == 'success':
                        print(f"    {endpoint:<40}: {result['response_time']:>6.3f}s")
                    else:
                        print(f"    {endpoint:<40}: FAILED")
        
        # Concurrent access report
        if 'concurrent_access' in results:
            print("\n📊 CONCURRENT ACCESS PERFORMANCE:")
            print("-" * 50)
            result = results['concurrent_access']
            if 'error' not in result:
                print(f"  Success rate: {result['success_rate']:>6.1f}%")
                print(f"  Avg response: {result['avg_response_time']:>6.3f}s")
                print(f"  Max response: {result['max_response_time']:>6.3f}s")
                print(f"  Requests/sec: {result['requests_per_second']:>6.2f}")
            else:
                print(f"  ERROR: {result['error']}")

def main():
    """Main function to run performance tests"""
    test_suite = PerformanceTest()
    results = test_suite.run_all_performance_tests()
    
    if results:
        print("\n🎉 Performance tests completed successfully!")
        
        # Save results to file
        with open('/app/tests/performance_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("📁 Results saved to /app/tests/performance_results.json")
        exit(0)
    else:
        print("\n💥 Performance tests failed!")
        exit(1)

if __name__ == "__main__":
    main()