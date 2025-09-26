#!/usr/bin/env python3
"""
Test GitHub Copilot API Access with Different Token Types
"""

import requests
import json

def test_copilot_api_access(token: str, org: str):
    """Test different Copilot API endpoints to see what works"""
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    endpoints_to_test = [
        {
            'name': 'Copilot Usage Summary',
            'url': f'https://api.github.com/orgs/{org}/copilot/usage',
            'description': 'Organization-level Copilot usage metrics'
        },
        {
            'name': 'Copilot Billing Seats',  
            'url': f'https://api.github.com/orgs/{org}/copilot/billing/seats',
            'description': 'Copilot seat assignments and billing info'
        },
        {
            'name': 'Copilot Usage by Team',
            'url': f'https://api.github.com/orgs/{org}/team/1/copilot/usage',  # Need real team ID
            'description': 'Team-level Copilot usage (if teams exist)'
        }
    ]
    
    print(f"Testing Copilot API access for organization: {org}")
    print("=" * 60)
    
    results = {}
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        
        try:
            response = requests.get(endpoint['url'], headers=headers)
            
            results[endpoint['name']] = {
                'status_code': response.status_code,
                'accessible': response.status_code == 200,
                'error_message': None
            }
            
            if response.status_code == 200:
                print("✅ SUCCESS - API accessible")
                # Print a sample of the data structure (without sensitive info)
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   Sample data structure: {list(data[0].keys())}")
                    elif isinstance(data, dict):
                        print(f"   Data structure keys: {list(data.keys())}")
                except:
                    print("   Response received but couldn't parse JSON structure")
                    
            elif response.status_code == 401:
                print("❌ AUTHENTICATION ERROR - Token invalid or insufficient permissions")
                results[endpoint['name']]['error_message'] = "Authentication failed"
                
            elif response.status_code == 403:
                print("❌ FORBIDDEN - Token lacks required permissions")
                results[endpoint['name']]['error_message'] = "Insufficient permissions"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        print(f"   GitHub says: {error_data['message']}")
                        results[endpoint['name']]['error_message'] = error_data['message']
                except:
                    pass
                    
            elif response.status_code == 404:
                print("❌ NOT FOUND - Endpoint doesn't exist or org doesn't have Copilot")
                results[endpoint['name']]['error_message'] = "Not found - may not have Copilot enabled"
                
            else:
                print(f"❌ ERROR {response.status_code}")
                results[endpoint['name']]['error_message'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results[endpoint['name']] = {
                'status_code': None,
                'accessible': False,
                'error_message': str(e)
            }
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    accessible_apis = [name for name, result in results.items() if result['accessible']]
    
    if accessible_apis:
        print(f"✅ Accessible APIs: {', '.join(accessible_apis)}")
        print("\nYour token has sufficient permissions for Copilot Usage API!")
        return True
    else:
        print("❌ No Copilot APIs accessible")
        print("\nRequired scopes for classic tokens:")
        print("  - 'copilot' scope (if it exists)")
        print("  - 'read:org' scope")
        print("  - Organization must have Copilot enabled")
        print("  - You must be an organization owner or have appropriate permissions")
        return False

def main():
    print("GitHub Copilot API Access Tester")
    print("================================")
    
    # Get inputs
    token = input("Enter your GitHub token: ").strip()
    org = input("Enter your organization name: ").strip()
    
    if not token or not org:
        print("Both token and organization are required!")
        return 1
    
    # Test access
    success = test_copilot_api_access(token, org)
    
    if success:
        print(f"\n🎉 Great! You can use the full Copilot analytics script.")
        print("Run: python scripts/copilot_before_after_analyzer.py")
    else:
        print(f"\n💡 Consider using the fine-grained compatible version instead.")
        print("Run: python scripts/productivity_analyzer_fine_grained.py")
    
    return 0

if __name__ == '__main__':
    exit(main())