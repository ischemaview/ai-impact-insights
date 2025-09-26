#!/usr/bin/env python3
"""
Individual Developer Analysis - Last 90 Days
Analyzes specific developers' commit patterns and code volume over the past 90 days
"""

import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time

class IndividualDeveloperAnalyzer:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.token = self.config['github']['token']
        self.org = self.config['github']['organization']
        self.repositories = self.config['github']['repositories']
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }

    def get_commits_for_user(self, repo, username, since_date):
        """Get all commits for a specific user in a repository since a date"""
        url = f"https://api.github.com/repos/{self.org}/{repo}/commits"
        params = {
            'author': username,
            'since': since_date.isoformat(),
            'per_page': 100
        }
        
        all_commits = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"    Error fetching commits for {username}: {response.status_code}")
                break
                
            commits = response.json()
            if not commits:
                break
                
            all_commits.extend(commits)
            page += 1
            
            # Rate limiting protection
            if len(all_commits) > 300:
                break
                
        return all_commits

    def get_commit_details(self, repo, sha):
        """Get detailed stats for a specific commit"""
        url = f"https://api.github.com/repos/{self.org}/{repo}/commits/{sha}"
        
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def analyze_user_activity(self, username, days=90):
        """Analyze a specific user's activity across all repositories"""
        since_date = datetime.now() - timedelta(days=days)
        
        print(f"\n🔍 Analyzing {username} (last {days} days)")
        print(f"   Period: {since_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        
        user_data = {
            'username': username,
            'analysis_period': days,
            'repositories': {},
            'totals': {
                'commits': 0,
                'additions': 0,
                'deletions': 0,
                'total_changes': 0,
                'files_changed': 0
            },
            'daily_activity': defaultdict(lambda: {'commits': 0, 'changes': 0}),
            'commit_messages': []
        }
        
        for repo in self.repositories:
            print(f"   📁 Checking {repo}...")
            
            commits = self.get_commits_for_user(repo, username, since_date)
            if not commits:
                print(f"      No commits found")
                continue
                
            print(f"      Found {len(commits)} commits")
            
            repo_stats = {
                'commits': len(commits),
                'additions': 0,
                'deletions': 0,
                'total_changes': 0,
                'files_changed': 0,
                'commit_details': []
            }
            
            # Get detailed stats for up to 20 recent commits
            for i, commit in enumerate(commits[:20]):
                details = self.get_commit_details(repo, commit['sha'])
                if details and 'stats' in details:
                    stats = details['stats']
                    additions = stats.get('additions', 0)
                    deletions = stats.get('deletions', 0)
                    total = stats.get('total', 0)
                    files = len(details.get('files', []))
                    
                    repo_stats['additions'] += additions
                    repo_stats['deletions'] += deletions
                    repo_stats['total_changes'] += total
                    repo_stats['files_changed'] += files
                    
                    # Daily activity tracking
                    commit_date = datetime.fromisoformat(
                        commit['commit']['author']['date'].replace('Z', '+00:00')
                    ).date()
                    user_data['daily_activity'][str(commit_date)]['commits'] += 1
                    user_data['daily_activity'][str(commit_date)]['changes'] += total
                    
                    # Store commit message for pattern analysis
                    message = commit['commit']['message']
                    user_data['commit_messages'].append(message)
                    
                    repo_stats['commit_details'].append({
                        'sha': commit['sha'][:8],
                        'date': commit_date.strftime('%Y-%m-%d'),
                        'message': message[:60] + ('...' if len(message) > 60 else ''),
                        'additions': additions,
                        'deletions': deletions,
                        'total': total,
                        'files': files
                    })
                
                # Rate limiting
                if (i + 1) % 10 == 0:
                    time.sleep(1)
                    
            user_data['repositories'][repo] = repo_stats
            user_data['totals']['commits'] += repo_stats['commits']
            user_data['totals']['additions'] += repo_stats['additions']
            user_data['totals']['deletions'] += repo_stats['deletions']
            user_data['totals']['total_changes'] += repo_stats['total_changes']
            user_data['totals']['files_changed'] += repo_stats['files_changed']
            
        # Calculate derived metrics
        if user_data['totals']['commits'] > 0:
            user_data['metrics'] = {
                'avg_changes_per_commit': user_data['totals']['total_changes'] / user_data['totals']['commits'],
                'avg_additions_per_commit': user_data['totals']['additions'] / user_data['totals']['commits'],
                'avg_deletions_per_commit': user_data['totals']['deletions'] / user_data['totals']['commits'],
                'avg_files_per_commit': user_data['totals']['files_changed'] / user_data['totals']['commits'],
                'commits_per_day': user_data['totals']['commits'] / days,
                'changes_per_day': user_data['totals']['total_changes'] / days
            }
        
        return user_data

    def analyze_commit_patterns(self, user_data):
        """Analyze patterns in commit messages for AI usage indicators"""
        messages = user_data['commit_messages']
        
        patterns = {
            'ai_indicators': 0,
            'bulk_operations': 0,
            'feature_development': 0,
            'bug_fixes': 0,
            'refactoring': 0,
            'documentation': 0
        }
        
        ai_keywords = ['copilot', 'ai-generated', 'ai-assisted', 'auto-generated', 'gpt', 'claude']
        bulk_keywords = ['bulk', 'mass', 'multiple', 'batch', 'auto']
        feature_keywords = ['feature', 'add', 'implement', 'create', 'new']
        bug_keywords = ['fix', 'bug', 'issue', 'resolve', 'patch']
        refactor_keywords = ['refactor', 'cleanup', 'reorganize', 'restructure']
        doc_keywords = ['doc', 'documentation', 'readme', 'comment', 'docstring']
        
        for message in messages:
            message_lower = message.lower()
            
            if any(keyword in message_lower for keyword in ai_keywords):
                patterns['ai_indicators'] += 1
            if any(keyword in message_lower for keyword in bulk_keywords):
                patterns['bulk_operations'] += 1
            if any(keyword in message_lower for keyword in feature_keywords):
                patterns['feature_development'] += 1
            if any(keyword in message_lower for keyword in bug_keywords):
                patterns['bug_fixes'] += 1
            if any(keyword in message_lower for keyword in refactor_keywords):
                patterns['refactoring'] += 1
            if any(keyword in message_lower for keyword in doc_keywords):
                patterns['documentation'] += 1
        
        return patterns

    def print_user_summary(self, user_data):
        """Print a comprehensive summary for a user"""
        username = user_data['username']
        totals = user_data['totals']
        
        print(f"\n📊 SUMMARY FOR {username.upper()}")
        print("=" * 50)
        
        if totals['commits'] == 0:
            print("   No commits found in the analysis period")
            return
            
        print(f"Total Commits: {totals['commits']:,}")
        print(f"Lines Added: {totals['additions']:,}")
        print(f"Lines Deleted: {totals['deletions']:,}")
        print(f"Total Changes: {totals['total_changes']:,}")
        print(f"Files Modified: {totals['files_changed']:,}")
        
        if 'metrics' in user_data:
            metrics = user_data['metrics']
            print(f"\nProductivity Metrics:")
            print(f"  Commits per day: {metrics['commits_per_day']:.1f}")
            print(f"  Changes per day: {metrics['changes_per_day']:.1f}")
            print(f"  Avg changes per commit: {metrics['avg_changes_per_commit']:.1f}")
            print(f"  Avg files per commit: {metrics['avg_files_per_commit']:.1f}")
        
        # Repository breakdown
        print(f"\nRepository Activity:")
        for repo, stats in user_data['repositories'].items():
            if stats['commits'] > 0:
                print(f"  {repo}: {stats['commits']} commits, {stats['total_changes']:,} changes")
        
        # Commit patterns
        patterns = self.analyze_commit_patterns(user_data)
        if any(patterns.values()):
            print(f"\nCommit Patterns:")
            for pattern, count in patterns.items():
                if count > 0:
                    print(f"  {pattern.replace('_', ' ').title()}: {count}")
        
        # Recent activity sample
        if user_data['repositories']:
            print(f"\nRecent Commits Sample:")
            all_commits = []
            for repo, stats in user_data['repositories'].items():
                for commit in stats['commit_details'][:5]:
                    all_commits.append((repo, commit))
            
            # Sort by date and show most recent
            for repo, commit in all_commits[:5]:
                print(f"  {commit['date']} [{repo}] {commit['message']} ({commit['total']} changes)")

def main():
    print("🔍 Individual Developer Analysis - Last 90 Days")
    print("=" * 60)
    
    analyzer = IndividualDeveloperAnalyzer()
    
    # Get usernames to analyze
    # First try to get from apps-team
    try:
        from get_team_members import get_team_members
        print("🔍 Fetching apps-team members...")
        usernames = get_team_members(
            analyzer.config['github']['token'],
            analyzer.config['github']['organization'],
            'apps-team'
        )
        
        if not usernames:
            print("No team members found. Please specify usernames manually:")
            usernames_input = input("> ").strip()
            if usernames_input:
                usernames = [name.strip() for name in usernames_input.split(',')]
            else:
                print("No usernames provided. Exiting.")
                return
    except:
        print("Please specify GitHub usernames to analyze (comma-separated):")
        usernames_input = input("> ").strip()
        
        if not usernames_input:
            print("No usernames provided. Exiting.")
            return
        
        usernames = [name.strip() for name in usernames_input.split(',')]
    
    print(f"\nAnalyzing {len(usernames)} developers...")
    
    all_user_data = []
    
    for username in usernames:
        user_data = analyzer.analyze_user_activity(username, days=90)
        all_user_data.append(user_data)
        analyzer.print_user_summary(user_data)
        
        # Add some spacing between users
        print("\n" + "-" * 60)
    
    # Comparative analysis
    print(f"\n📈 COMPARATIVE ANALYSIS")
    print("=" * 60)
    
    # Sort users by total productivity
    productive_users = [(data['username'], data['totals']) for data in all_user_data if data['totals']['commits'] > 0]
    productive_users.sort(key=lambda x: x[1]['total_changes'], reverse=True)
    
    print(f"Ranking by Total Code Changes:")
    for i, (username, totals) in enumerate(productive_users, 1):
        changes_per_day = totals['total_changes'] / 90
        print(f"  {i}. {username}: {totals['total_changes']:,} changes ({changes_per_day:.1f}/day, {totals['commits']} commits)")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"individual_analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'users_analyzed': usernames,
            'period_days': 90,
            'detailed_results': all_user_data
        }, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == '__main__':
    main()