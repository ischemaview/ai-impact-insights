#!/usr/bin/env python3
"""
GitHub Team Members Fetcher
Gets list of team members from a GitHub organization team
"""

import requests
import json

def get_team_members(token, org, team_slug):
    """Get all members of a GitHub team"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    # First, get team ID
    teams_url = f"https://api.github.com/orgs/{org}/teams"
    response = requests.get(teams_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching teams: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error message: {error_data.get('message', 'Unknown error')}")
        except:
            pass
        return []
    
    teams = response.json()
    team_id = None
    
    print(f"Available teams in {org}:")
    for team in teams:
        members_count = team.get('members_count', 'unknown')
        print(f"  - {team['slug']} ({team['name']}) - {members_count} members")
        if team['slug'] == team_slug:
            team_id = team['id']
    
    if not team_id:
        print(f"\nTeam '{team_slug}' not found!")
        return []
    
    # Get team members
    members_url = f"https://api.github.com/teams/{team_id}/members"
    response = requests.get(members_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching team members: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error message: {error_data.get('message', 'Unknown error')}")
        except:
            pass
        return []
    
    members = response.json()
    usernames = [member['login'] for member in members]
    
    print(f"\nMembers of '{team_slug}' team:")
    for username in usernames:
        print(f"  - {username}")
    
    return usernames

def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    token = config['github']['token']
    org = config['github']['organization']
    team_slug = 'apps-team'
    
    print(f"🔍 Fetching members of '{team_slug}' team in {org} organization...")
    
    usernames = get_team_members(token, org, team_slug)
    
    if usernames:
        print(f"\n✅ Found {len(usernames)} team members")
        return usernames
    else:
        print("❌ No team members found or unable to access team")
        return []

if __name__ == '__main__':
    main()