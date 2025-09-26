#!/usr/bin/env python3
"""
GitHub Copilot Metrics & Code Production Correlation Analysis
Extracts Copilot usage data and correlates with code production metrics
"""

import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import argparse
from typing import Dict, List, Optional

class CopilotMetricsAnalyzer:
    def __init__(self, github_token: str, org: str):
        self.github_token = github_token
        self.org = org
        self.headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self.base_url = 'https://api.github.com'

    def get_copilot_usage_summary(self, since: str, until: str) -> Dict:
        """
        Get Copilot usage summary for the organization
        https://docs.github.com/en/rest/copilot/copilot-usage
        """
        url = f"{self.base_url}/orgs/{self.org}/copilot/usage"
        params = {
            'since': since,
            'until': until
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching Copilot usage: {response.status_code} - {response.text}")
            return {}

    def get_copilot_seat_details(self) -> List[Dict]:
        """
        Get details about Copilot seat assignments
        """
        url = f"{self.base_url}/orgs/{self.org}/copilot/billing/seats"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get('seats', [])
        else:
            print(f"Error fetching Copilot seats: {response.status_code} - {response.text}")
            return []

    def get_repository_commits(self, repo: str, since: str, until: str) -> List[Dict]:
        """
        Get commits for a specific repository in the date range
        """
        url = f"{self.base_url}/repos/{self.org}/{repo}/commits"
        params = {
            'since': since,
            'until': until,
            'per_page': 100
        }
        
        all_commits = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                break
                
            commits = response.json()
            if not commits:
                break
                
            all_commits.extend(commits)
            page += 1
            
            # GitHub API rate limiting
            if page > 10:  # Limit for demo purposes
                break
                
        return all_commits

    def get_org_repositories(self) -> List[str]:
        """
        Get list of repositories in the organization
        """
        url = f"{self.base_url}/orgs/{self.org}/repos"
        params = {'per_page': 100, 'type': 'all'}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            repos = response.json()
            return [repo['name'] for repo in repos if not repo['archived']]
        else:
            print(f"Error fetching repositories: {response.status_code}")
            return []

    def analyze_commit_patterns(self, commits: List[Dict]) -> Dict:
        """
        Analyze commit patterns to extract productivity metrics
        """
        if not commits:
            return {}
            
        commit_data = []
        
        for commit in commits:
            commit_info = {
                'sha': commit['sha'],
                'author': commit.get('author', {}).get('login', 'unknown'),
                'date': commit['commit']['author']['date'],
                'message': commit['commit']['message'],
                'additions': 0,
                'deletions': 0,
                'total_changes': 0
            }
            
            # Get detailed commit stats (requires additional API call)
            # For efficiency, we'll estimate based on message patterns
            message_lower = commit_info['message'].lower()
            
            # Simple heuristics for AI-assisted commits
            ai_indicators = ['copilot', 'ai-generated', 'auto-complete', 'suggested']
            commit_info['likely_ai_assisted'] = any(indicator in message_lower for indicator in ai_indicators)
            
            commit_data.append(commit_info)
            
        # Aggregate metrics
        total_commits = len(commit_data)
        unique_authors = len(set(c['author'] for c in commit_data))
        ai_assisted_commits = sum(1 for c in commit_data if c['likely_ai_assisted'])
        
        # Group by author
        author_stats = {}
        for commit in commit_data:
            author = commit['author']
            if author not in author_stats:
                author_stats[author] = {
                    'commits': 0,
                    'ai_assisted_commits': 0
                }
            author_stats[author]['commits'] += 1
            if commit['likely_ai_assisted']:
                author_stats[author]['ai_assisted_commits'] += 1
                
        return {
            'total_commits': total_commits,
            'unique_authors': unique_authors,
            'ai_assisted_commits': ai_assisted_commits,
            'ai_assistance_rate': (ai_assisted_commits / total_commits * 100) if total_commits > 0 else 0,
            'author_stats': author_stats,
            'commits_per_author': total_commits / unique_authors if unique_authors > 0 else 0
        }

    def correlate_copilot_and_productivity(self, weeks: int = 4) -> Dict:
        """
        Main analysis function to correlate Copilot usage with code production
        """
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        since = start_date.isoformat()
        until = end_date.isoformat()
        
        print(f"Analyzing Copilot impact from {start_date.date()} to {end_date.date()}")
        
        # Get Copilot data
        print("Fetching Copilot usage data...")
        copilot_usage = self.get_copilot_usage_summary(since, until)
        copilot_seats = self.get_copilot_seat_details()
        
        # Get repository data
        print("Fetching repository data...")
        repositories = self.get_org_repositories()[:5]  # Limit for demo
        
        all_commit_stats = {}
        total_commits = 0
        
        for repo in repositories:
            print(f"Analyzing repository: {repo}")
            commits = self.get_repository_commits(repo, since, until)
            commit_stats = self.analyze_commit_patterns(commits)
            
            if commit_stats:
                all_commit_stats[repo] = commit_stats
                total_commits += commit_stats['total_commits']
        
        # Correlation analysis
        analysis = {
            'analysis_period': {
                'start_date': since,
                'end_date': until,
                'weeks': weeks
            },
            'copilot_data': {
                'total_seats': len(copilot_seats),
                'active_users': len([s for s in copilot_seats if s.get('last_activity_at')]),
                'usage_summary': copilot_usage
            },
            'code_production': {
                'total_repositories_analyzed': len(repositories),
                'total_commits': total_commits,
                'repository_stats': all_commit_stats
            },
            'correlations': self.calculate_correlations(copilot_seats, all_commit_stats)
        }
        
        return analysis

    def calculate_correlations(self, copilot_seats: List[Dict], commit_stats: Dict) -> Dict:
        """
        Calculate correlations between Copilot usage and productivity
        """
        # Extract user productivity data
        user_productivity = {}
        
        for repo, stats in commit_stats.items():
            for author, author_stats in stats.get('author_stats', {}).items():
                if author not in user_productivity:
                    user_productivity[author] = {
                        'total_commits': 0,
                        'ai_assisted_commits': 0,
                        'repositories': []
                    }
                user_productivity[author]['total_commits'] += author_stats['commits']
                user_productivity[author]['ai_assisted_commits'] += author_stats['ai_assisted_commits']
                user_productivity[author]['repositories'].append(repo)
        
        # Match with Copilot seats
        copilot_users = {seat['assignee']['login'] for seat in copilot_seats}
        
        correlations = {
            'users_with_copilot': len(copilot_users),
            'users_in_commit_data': len(user_productivity),
            'overlap_users': len(copilot_users.intersection(user_productivity.keys())),
            'productivity_comparison': {}
        }
        
        # Compare productivity: Copilot users vs non-Copilot users
        copilot_user_commits = []
        non_copilot_user_commits = []
        
        for user, data in user_productivity.items():
            if user in copilot_users:
                copilot_user_commits.append(data['total_commits'])
            else:
                non_copilot_user_commits.append(data['total_commits'])
        
        if copilot_user_commits and non_copilot_user_commits:
            avg_copilot_commits = sum(copilot_user_commits) / len(copilot_user_commits)
            avg_non_copilot_commits = sum(non_copilot_user_commits) / len(non_copilot_user_commits)
            
            correlations['productivity_comparison'] = {
                'avg_commits_copilot_users': avg_copilot_commits,
                'avg_commits_non_copilot_users': avg_non_copilot_commits,
                'productivity_uplift': ((avg_copilot_commits - avg_non_copilot_commits) / avg_non_copilot_commits * 100) if avg_non_copilot_commits > 0 else 0
            }
        
        return correlations

def main():
    parser = argparse.ArgumentParser(description='Analyze GitHub Copilot impact on code production')
    parser.add_argument('--token', required=True, help='GitHub API token with org access')
    parser.add_argument('--org', required=True, help='GitHub organization name')
    parser.add_argument('--weeks', type=int, default=4, help='Analysis period in weeks')
    parser.add_argument('--output', default='copilot_analysis.json', help='Output file')
    
    args = parser.parse_args()
    
    analyzer = CopilotMetricsAnalyzer(args.token, args.org)
    
    try:
        analysis = analyzer.correlate_copilot_and_productivity(args.weeks)
        
        # Print summary
        print("\n=== COPILOT IMPACT ANALYSIS ===")
        print(f"Organization: {args.org}")
        print(f"Analysis Period: {analysis['analysis_period']['weeks']} weeks")
        print(f"Copilot Seats: {analysis['copilot_data']['total_seats']}")
        print(f"Active Users: {analysis['copilot_data']['active_users']}")
        print(f"Total Commits: {analysis['code_production']['total_commits']}")
        
        correlations = analysis['correlations']
        if correlations.get('productivity_comparison'):
            comp = correlations['productivity_comparison']
            print(f"\nPRODUCTIVITY COMPARISON:")
            print(f"Avg commits (Copilot users): {comp['avg_commits_copilot_users']:.1f}")
            print(f"Avg commits (Non-Copilot users): {comp['avg_commits_non_copilot_users']:.1f}")
            print(f"Productivity uplift: {comp['productivity_uplift']:.1f}%")
        
        # Save detailed results
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\nDetailed analysis saved to: {args.output}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())