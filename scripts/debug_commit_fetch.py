#!/usr/bin/env python3
"""
Simple GitHub Commit Analysis - Debug Version
"""

import requests
import json
from datetime import datetime, timedelta

def test_commit_fetch(token, org, repo, since, until):
    """Test fetching commits from a single repository"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f"https://api.github.com/repos/{org}/{repo}/commits"
    params = {
        'since': since,
        'until': until,
        'per_page': 10  # Small sample for testing
    }
    
    print(f"Testing commits for {org}/{repo}")
    print(f"Date range: {since} to {until}")
    
    response = requests.get(url, headers=headers, params=params)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        commits = response.json()
        print(f"Found {len(commits)} commits")
        
        if commits:
            print("Sample commit structure:")
            commit = commits[0]
            print(f"  - SHA: {commit.get('sha', 'N/A')}")
            print(f"  - Author: {commit.get('author')}")
            print(f"  - Message: {commit.get('commit', {}).get('message', 'N/A')[:50]}...")
            print(f"  - Date: {commit.get('commit', {}).get('author', {}).get('date', 'N/A')}")
        
        return commits
    else:
        print(f"Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error message: {error_data.get('message', 'Unknown error')}")
        except:
            print("Could not parse error response")
        
        return []

def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    token = config['github']['token']
    org = config['github']['organization']
    repos = config['github']['repositories']
    
    # Test date ranges
    adoption_date = datetime.fromisoformat(config['analysis']['copilot_adoption_date'])
    before_start = adoption_date - timedelta(weeks=4)  # Shorter period for testing
    before_end = adoption_date
    
    print("=== GitHub Commit Fetch Test ===")
    print(f"Organization: {org}")
    print(f"Test date range: {before_start.date()} to {before_end.date()}")
    
    for repo in repos:
        print(f"\n--- Testing {repo} ---")
        commits = test_commit_fetch(
            token, org, repo,
            before_start.isoformat(),
            before_end.isoformat()
        )
        
        if commits:
            print(f"✅ Successfully fetched commits from {repo}")
        else:
            print(f"❌ No commits found in {repo} for this period")

if __name__ == '__main__':
    main()