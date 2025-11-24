"""
Test all API endpoints to verify they're working correctly.
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "12345678-1234-1234-1234-123456789012"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_health():
    """Test health check endpoint."""
    print(f"\n{BLUE}Testing Health Check{RESET}")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Health check passed{RESET}")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database', {}).get('status')}")
            return True
        else:
            print(f"{RED}❌ Health check failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


def test_create_goal():
    """Test creating a learning goal."""
    print(f"\n{BLUE}Testing Create Goal{RESET}")
    print("-" * 50)
    
    try:
        payload = {
            "goal_text": "Learn about large language models, RAG systems, and vector databases",
            "difficulty_level": "intermediate",
            "frequency": "weekly"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/goals",
            headers={"x-user-id": USER_ID, "Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"{GREEN}✅ Goal created successfully{RESET}")
            print(f"   Goal ID: {data.get('goal_id')}")
            print(f"   Goal Text: {data.get('goal_text')}")
            return True, data.get('goal_id')
        else:
            print(f"{RED}❌ Failed to create goal: {response.status_code}{RESET}")
            print(f"   Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False, None


def test_get_active_goal():
    """Test getting active goal."""
    print(f"\n{BLUE}Testing Get Active Goal{RESET}")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/goals/active",
            headers={"x-user-id": USER_ID}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Active goal retrieved{RESET}")
            print(f"   Goal: {data.get('goal_text')}")
            return True
        elif response.status_code == 404:
            print(f"{YELLOW}⚠️  No active goal found{RESET}")
            return True
        else:
            print(f"{RED}❌ Failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


def test_add_source():
    """Test adding a content source."""
    print(f"\n{BLUE}Testing Add Source{RESET}")
    print("-" * 50)
    
    try:
        payload = {
            "source_type": "rss",
            "value": "https://test-feed.example.com/rss.xml",
            "status": "active"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sources",
            headers={"x-user-id": USER_ID, "Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"{GREEN}✅ Source added successfully{RESET}")
            print(f"   Source ID: {data.get('source_id')}")
            print(f"   Type: {data.get('source_type')}")
            return True
        else:
            print(f"{RED}❌ Failed to add source: {response.status_code}{RESET}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


def test_get_sources():
    """Test getting all sources."""
    print(f"\n{BLUE}Testing Get Sources{RESET}")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/sources",
            headers={"x-user-id": USER_ID}
        )
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get('sources', [])
            print(f"{GREEN}✅ Sources retrieved{RESET}")
            print(f"   Total sources: {len(sources)}")
            if sources:
                print(f"   First source: {sources[0].get('source_type')} - {sources[0].get('value')[:50]}...")
            return True
        else:
            print(f"{RED}❌ Failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


def test_get_current_digest():
    """Test getting current digest."""
    print(f"\n{BLUE}Testing Get Current Digest{RESET}")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/digests/current",
            headers={"x-user-id": USER_ID}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Digest retrieved{RESET}")
            print(f"   Total items: {data.get('total_items')}")
            return True
        elif response.status_code == 404:
            print(f"{YELLOW}⚠️  No digest available yet{RESET}")
            print(f"   Note: Digests are generated weekly on Sundays at 6 AM")
            return True
        else:
            print(f"{RED}❌ Failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


def test_get_digest_history():
    """Test getting digest history."""
    print(f"\n{BLUE}Testing Get Digest History{RESET}")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/digests/history?limit=10&offset=0",
            headers={"x-user-id": USER_ID}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Digest history retrieved{RESET}")
            print(f"   Total count: {data.get('total_count')}")
            return True
        else:
            print(f"{RED}❌ Failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


def run_all_tests():
    """Run all API tests."""
    print(f"\n{'='*50}")
    print(f"{BLUE}🧪 AI Learning Coach - API Testing{RESET}")
    print(f"{'='*50}")
    print(f"Base URL: {BASE_URL}")
    print(f"User ID: {USER_ID}")
    
    results = {
        "Health Check": test_health(),
        "Create Goal": test_create_goal()[0],
        "Get Active Goal": test_get_active_goal(),
        "Add Source": test_add_source(),
        "Get Sources": test_get_sources(),
        "Get Current Digest": test_get_current_digest(),
        "Get Digest History": test_get_digest_history(),
    }
    
    # Summary
    print(f"\n{'='*50}")
    print(f"{BLUE}📊 Test Summary{RESET}")
    print(f"{'='*50}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}🎉 All tests passed! API is working correctly.{RESET}")
    else:
        print(f"\n{YELLOW}⚠️  Some tests failed. Check the output above for details.{RESET}")
    
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run_all_tests()
