#!/usr/bin/env python3
"""
Enhanced GitHub Analysis with Detailed Line Changes
Fetches detailed commit stats including additions/deletions for more accurate productivity metrics
"""

import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time

def get_detailed_commit_stats(token, org, repo, commits, max_commits=100):
    """
    Fetch detailed stats (additions/deletions) for commits
    Limited to avoid rate limiting
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    detailed_stats = []
    processed = 0
    
    print(f"    Fetching detailed stats (max {max_commits} commits)...")
    
    for commit in commits[:max_commits]:  # Limit to avoid rate limits
        sha = commit['sha']
        url = f"https://api.github.com/repos/{org}/{repo}/commits/{sha}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                commit_details = response.json()
                stats = commit_details.get('stats', {})
                
                detailed_stats.append({
                    'sha': sha,
                    'author': commit.get('author', {}).get('login') if commit.get('author') else None,
                    'date': commit.get('commit', {}).get('author', {}).get('date'),
                    'message': commit.get('commit', {}).get('message', ''),
                    'additions': stats.get('additions', 0),
                    'deletions': stats.get('deletions', 0),
                    'total_changes': stats.get('total', 0),
                    'files_changed': len(commit_details.get('files', []))
                })
                processed += 1
                
                # Rate limiting - GitHub allows 5000 requests per hour
                if processed % 20 == 0:
                    print(f"      Processed {processed}/{min(len(commits), max_commits)} commits...")
                    time.sleep(1)  # Brief pause
                    
            elif response.status_code == 403:
                print(f"      Rate limit hit at commit {processed}")
                break
            else:
                print(f"      Error {response.status_code} for commit {sha[:8]}")
                
        except Exception as e:
            print(f"      Exception processing commit {sha[:8]}: {e}")
            continue
    
    print(f"    Successfully processed {len(detailed_stats)} commits with detailed stats")
    return detailed_stats

def analyze_repository_changes(token, org, repos, before_start, before_end, after_start, after_end):
    """
    Analyze line changes for repositories with detailed commit stats
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    results = {}
    
    for repo in repos:
        print(f"\n--- Analyzing {repo} with detailed line changes ---")
        
        repo_results = {
            'before': {'commits': 0, 'total_additions': 0, 'total_deletions': 0, 'total_changes': 0, 'files_changed': 0},
            'after': {'commits': 0, 'total_additions': 0, 'total_deletions': 0, 'total_changes': 0, 'files_changed': 0},
            'user_stats': defaultdict(lambda: {
                'before': {'commits': 0, 'additions': 0, 'deletions': 0, 'changes': 0, 'files': 0},
                'after': {'commits': 0, 'additions': 0, 'deletions': 0, 'changes': 0, 'files': 0}
            })
        }
        
        # Fetch basic commits for both periods
        url = f"https://api.github.com/repos/{org}/{repo}/commits"
        
        # Before period
        print("  Fetching 'before' commits...")
        before_commits = []
        page = 1
        while len(before_commits) < 200 and page <= 5:  # Limit pages
            params = {
                'since': before_start.isoformat(),
                'until': before_end.isoformat(),
                'per_page': 100,
                'page': page
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                commits = response.json()
                if not commits:
                    break
                before_commits.extend(commits)
                page += 1
            else:
                break
        
        # After period
        print("  Fetching 'after' commits...")
        after_commits = []
        page = 1
        while len(after_commits) < 200 and page <= 5:  # Limit pages
            params = {
                'since': after_start.isoformat(),
                'until': after_end.isoformat(),
                'per_page': 100,
                'page': page
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                commits = response.json()
                if not commits:
                    break
                after_commits.extend(commits)
                page += 1
            else:
                break
        
        print(f"  Found {len(before_commits)} before commits, {len(after_commits)} after commits")
        
        # Get detailed stats for a sample of commits
        before_detailed = get_detailed_commit_stats(token, org, repo, before_commits, max_commits=50)
        after_detailed = get_detailed_commit_stats(token, org, repo, after_commits, max_commits=50)
        
        # Analyze before period
        for commit_detail in before_detailed:
            author = commit_detail['author']
            if author:
                repo_results['before']['commits'] += 1
                repo_results['before']['total_additions'] += commit_detail['additions']
                repo_results['before']['total_deletions'] += commit_detail['deletions']
                repo_results['before']['total_changes'] += commit_detail['total_changes']
                repo_results['before']['files_changed'] += commit_detail['files_changed']
                
                repo_results['user_stats'][author]['before']['commits'] += 1
                repo_results['user_stats'][author]['before']['additions'] += commit_detail['additions']
                repo_results['user_stats'][author]['before']['deletions'] += commit_detail['deletions']
                repo_results['user_stats'][author]['before']['changes'] += commit_detail['total_changes']
                repo_results['user_stats'][author]['before']['files'] += commit_detail['files_changed']
        
        # Analyze after period
        for commit_detail in after_detailed:
            author = commit_detail['author']
            if author:
                repo_results['after']['commits'] += 1
                repo_results['after']['total_additions'] += commit_detail['additions']
                repo_results['after']['total_deletions'] += commit_detail['deletions']
                repo_results['after']['total_changes'] += commit_detail['total_changes']
                repo_results['after']['files_changed'] += commit_detail['files_changed']
                
                repo_results['user_stats'][author]['after']['commits'] += 1
                repo_results['user_stats'][author]['after']['additions'] += commit_detail['additions']
                repo_results['user_stats'][author]['after']['deletions'] += commit_detail['deletions']
                repo_results['user_stats'][author]['after']['changes'] += commit_detail['total_changes']
                repo_results['user_stats'][author]['after']['files'] += commit_detail['files_changed']
        
        results[repo] = repo_results
        
        # Print repository summary
        before = repo_results['before']
        after = repo_results['after']
        
        print(f"  Repository Summary:")
        print(f"    Commits: {before['commits']} → {after['commits']} ({(after['commits']/before['commits']-1)*100:+.1f}% change)" if before['commits'] > 0 else "    No before commits with details")
        print(f"    Lines added: {before['total_additions']:,} → {after['total_additions']:,} ({(after['total_additions']/before['total_additions']-1)*100:+.1f}% change)" if before['total_additions'] > 0 else "    Lines added: 0 → {:,}".format(after['total_additions']))
        print(f"    Lines deleted: {before['total_deletions']:,} → {after['total_deletions']:,} ({(after['total_deletions']/before['total_deletions']-1)*100:+.1f}% change)" if before['total_deletions'] > 0 else "    Lines deleted: 0 → {:,}".format(after['total_deletions']))
        print(f"    Total changes: {before['total_changes']:,} → {after['total_changes']:,} ({(after['total_changes']/before['total_changes']-1)*100:+.1f}% change)" if before['total_changes'] > 0 else "    Total changes: 0 → {:,}".format(after['total_changes']))
    
    return results

def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    token = config['github']['token']
    org = config['github']['organization']
    repos = config['github']['repositories']
    
    # Date ranges
    adoption_date = datetime.fromisoformat(config['analysis']['copilot_adoption_date'])
    before_weeks = config['analysis']['before_period_weeks']
    after_weeks = config['analysis']['after_period_weeks']
    
    before_start = adoption_date - timedelta(weeks=before_weeks)
    before_end = adoption_date
    after_start = adoption_date
    after_end = adoption_date + timedelta(weeks=after_weeks)
    
    print("=== Enhanced GitHub Line Changes Analysis ===")
    print(f"Organization: {org}")
    print(f"AI Adoption Date: {adoption_date.date()}")
    print(f"Before: {before_start.date()} to {before_end.date()} ({before_weeks} weeks)")
    print(f"After: {after_start.date()} to {after_end.date()} ({after_weeks} weeks)")
    
    # Run analysis
    results = analyze_repository_changes(token, org, repos, before_start, before_end, after_start, after_end)
    
    # Overall summary
    print(f"\n" + "="*60)
    print("OVERALL ORGANIZATION SUMMARY")
    print("="*60)
    
    total_before_changes = sum(r['before']['total_changes'] for r in results.values())
    total_after_changes = sum(r['after']['total_changes'] for r in results.values())
    total_before_commits = sum(r['before']['commits'] for r in results.values())
    total_after_commits = sum(r['after']['commits'] for r in results.values())
    
    print(f"Total Commits: {total_before_commits} → {total_after_commits} ({(total_after_commits/total_before_commits-1)*100:+.1f}% change)" if total_before_commits > 0 else f"Total Commits: 0 → {total_after_commits}")
    print(f"Total Line Changes: {total_before_changes:,} → {total_after_changes:,} ({(total_after_changes/total_before_changes-1)*100:+.1f}% change)" if total_before_changes > 0 else f"Total Line Changes: 0 → {total_after_changes:,}")
    
    if total_before_changes > 0 and total_before_commits > 0:
        before_changes_per_commit = total_before_changes / total_before_commits
        after_changes_per_commit = total_after_changes / total_after_commits if total_after_commits > 0 else 0
        print(f"Average Changes per Commit: {before_changes_per_commit:.1f} → {after_changes_per_commit:.1f} ({(after_changes_per_commit/before_changes_per_commit-1)*100:+.1f}% change)" if before_changes_per_commit > 0 else f"Average Changes per Commit: N/A → {after_changes_per_commit:.1f}")
    
    # Top performers by line changes
    all_users = defaultdict(lambda: {'before_changes': 0, 'after_changes': 0, 'before_commits': 0, 'after_commits': 0})
    
    for repo, repo_data in results.items():
        for user, user_data in repo_data['user_stats'].items():
            all_users[user]['before_changes'] += user_data['before']['changes']
            all_users[user]['after_changes'] += user_data['after']['changes']
            all_users[user]['before_commits'] += user_data['before']['commits']
            all_users[user]['after_commits'] += user_data['after']['commits']
    
    # Filter users with significant activity
    qualified_users = {
        user: data for user, data in all_users.items()
        if data['before_commits'] >= 3 and data['after_commits'] >= 3
    }
    
    print(f"\nTOP PERFORMERS BY LINE CHANGES ({len(qualified_users)} qualified users):")
    
    # Sort by improvement percentage
    sorted_users = []
    for user, data in qualified_users.items():
        if data['before_changes'] > 0:
            improvement = (data['after_changes'] - data['before_changes']) / data['before_changes'] * 100
            sorted_users.append((user, data, improvement))
    
    sorted_users.sort(key=lambda x: x[2], reverse=True)
    
    for user, data, improvement in sorted_users[:10]:
        print(f"  {user}: {data['before_changes']:,} → {data['after_changes']:,} lines ({improvement:+.1f}%)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"enhanced_line_changes_analysis_{timestamp}.json"
    
    output_data = {
        'metadata': {
            'organization': org,
            'analysis_date': datetime.now().isoformat(),
            'ai_adoption_date': adoption_date.isoformat(),
            'before_period': f"{before_start.date()} to {before_end.date()}",
            'after_period': f"{after_start.date()} to {after_end.date()}",
        },
        'summary': {
            'total_before_commits': total_before_commits,
            'total_after_commits': total_after_commits,
            'total_before_changes': total_before_changes,
            'total_after_changes': total_after_changes,
            'qualified_users': len(qualified_users)
        },
        'repository_details': results,
        'top_performers': sorted_users[:10]
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == '__main__':
    main()