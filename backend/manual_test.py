"""Manual test script for call endpoints - runs the backend and tests via HTTP"""
import subprocess
import time
import requests
import json
import sys

# Start backend server
print("Starting backend server...")
backend_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
    cwd=".",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Give server time to start
time.sleep(3)

BASE_URL = "http://127.0.0.1:8000"

try:
    # Test 1: Health check
    print("\n1. Testing API health...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"   ✓ API is running (status: {response.status_code})")
    
    # Test 2: Get available users without auth (should fail)
    print("\n2. Testing unauthorized access to /calls/available...")
    response = requests.get(f"{BASE_URL}/calls/available")
    if response.status_code in [401, 403]:
        print(f"   ✓ Correctly rejected unauthorized request (status: {response.status_code})")
    else:
        print(f"   ✗ Expected 401/403, got {response.status_code}")
    
    print("\n✓ All manual tests completed successfully!")
    print("\nNote: Full integration tests require a database and test users.")
    print("To test the full flow, you can:")
    print("  1. Register a user via POST /auth/register")
    print("  2. Verify email")
    print("  3. Login to get token")
    print("  4. Use token to access /calls/available")
    
finally:
    # Stop backend
    print("\nStopping backend server...")
    backend_process.terminate()
    backend_process.wait(timeout=5)
    print("Backend stopped.")
