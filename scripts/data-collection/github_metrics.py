#!/usr/bin/env python3
"""
GitHub Metrics Collection Script
Collects productivity and quality metrics from GitHub repositories
"""

import requests
import json
import csv
from datetime import datetime, timedelta
import argparse
import os
from typing import Dict, List, Optional

class GitHubMetricsCollector:
    def __init__(self, token: str, org: str, repo: str):
        self.token = token
        self.org = org
        self.repo = repo
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'

    def get_pull_requests(self, since: datetime, until: datetime) -> List[Dict]:
        """Fetch pull requests within date range"""
        url = f"{self.base_url}/repos/{self.org}/{self.repo}/pulls"
        params = {
            'state': 'all',
            'since': since.isoformat(),
            'per_page': 100
        }
        
        all_prs = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching PRs: {response.status_code}")
                break
                
            prs = response.json()
            if not prs:
                break
                
            # Filter by date range
            for pr in prs:
                created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                if since <= created_at <= until:
                    all_prs.append(pr)
                elif created_at < since:
                    # We've gone too far back
                    return all_prs
                    
            page += 1
            
        return all_prs

    def calculate_pr_metrics(self, prs: List[Dict]) -> Dict:
        """Calculate pull request metrics"""
        if not prs:
            return {}
            
        metrics = {
            'total_prs': len(prs),
            'merged_prs': 0,
            'closed_prs': 0,
            'avg_review_time_hours': 0,
            'avg_pr_size_lines': 0,
            'prs_with_ai_assistance': 0
        }
        
        review_times = []
        pr_sizes = []
        
        for pr in prs:
            if pr['merged_at']:
                metrics['merged_prs'] += 1
                
                # Calculate review time
                created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                merged_at = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                review_time = (merged_at - created_at).total_seconds() / 3600
                review_times.append(review_time)
                
            elif pr['closed_at']:
                metrics['closed_prs'] += 1
                
            # Check for AI assistance indicators
            body = pr['body'] or ''
            title = pr['title'] or ''
            if any(keyword in (body + title).lower() for keyword in 
                   ['copilot', 'ai-generated', 'ai-assisted', 'chatgpt', 'ai:']):
                metrics['prs_with_ai_assistance'] += 1
                
            # Get PR size (would need additional API call for accurate lines)
            metrics['avg_pr_size_lines'] += pr.get('additions', 0) + pr.get('deletions', 0)
            
        if review_times:
            metrics['avg_review_time_hours'] = sum(review_times) / len(review_times)
            
        if prs:
            metrics['avg_pr_size_lines'] = metrics['avg_pr_size_lines'] / len(prs)
            metrics['ai_assistance_rate'] = metrics['prs_with_ai_assistance'] / len(prs) * 100
            
        return metrics

    def get_commits(self, since: datetime, until: datetime) -> List[Dict]:
        """Fetch commits within date range"""
        url = f"{self.base_url}/repos/{self.org}/{self.repo}/commits"
        params = {
            'since': since.isoformat(),
            'until': until.isoformat(),
            'per_page': 100
        }
        
        all_commits = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching commits: {response.status_code}")
                break
                
            commits = response.json()
            if not commits:
                break
                
            all_commits.extend(commits)
            page += 1
            
        return all_commits

    def calculate_commit_metrics(self, commits: List[Dict]) -> Dict:
        """Calculate commit-based metrics"""
        if not commits:
            return {}
            
        metrics = {
            'total_commits': len(commits),
            'avg_commits_per_day': 0,
            'unique_contributors': 0,
            'commits_with_ai_indicators': 0
        }
        
        contributors = set()
        ai_commits = 0
        
        for commit in commits:
            # Track unique contributors
            author = commit.get('author', {})
            if author and author.get('login'):
                contributors.add(author['login'])
                
            # Check for AI assistance indicators in commit messages
            message = commit.get('commit', {}).get('message', '').lower()
            if any(keyword in message for keyword in 
                   ['ai-generated', 'copilot', 'ai-assisted', 'auto-generated']):
                ai_commits += 1
                
        metrics['unique_contributors'] = len(contributors)
        metrics['commits_with_ai_indicators'] = ai_commits
        
        if commits:
            # Calculate commits per day
            first_commit = datetime.fromisoformat(commits[-1]['commit']['author']['date'].replace('Z', '+00:00'))
            last_commit = datetime.fromisoformat(commits[0]['commit']['author']['date'].replace('Z', '+00:00'))
            days = max((last_commit - first_commit).days, 1)
            metrics['avg_commits_per_day'] = len(commits) / days
            metrics['ai_commit_rate'] = ai_commits / len(commits) * 100
            
        return metrics

    def get_issues(self, since: datetime, until: datetime) -> List[Dict]:
        """Fetch issues within date range"""
        url = f"{self.base_url}/repos/{self.org}/{self.repo}/issues"
        params = {
            'state': 'all',
            'since': since.isoformat(),
            'per_page': 100
        }
        
        all_issues = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching issues: {response.status_code}")
                break
                
            issues = response.json()
            if not issues:
                break
                
            # Filter out pull requests (they appear in issues endpoint)
            for issue in issues:
                if 'pull_request' not in issue:
                    created_at = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                    if since <= created_at <= until:
                        all_issues.append(issue)
                        
            page += 1
            
        return all_issues

    def calculate_issue_metrics(self, issues: List[Dict]) -> Dict:
        """Calculate issue-based quality metrics"""
        if not issues:
            return {}
            
        metrics = {
            'total_issues': len(issues),
            'bug_issues': 0,
            'enhancement_issues': 0,
            'closed_issues': 0,
            'avg_resolution_time_hours': 0
        }
        
        resolution_times = []
        
        for issue in issues:
            # Categorize by labels
            labels = [label['name'].lower() for label in issue.get('labels', [])]
            
            if any('bug' in label for label in labels):
                metrics['bug_issues'] += 1
            elif any(keyword in ' '.join(labels) for keyword in ['enhancement', 'feature', 'improvement']):
                metrics['enhancement_issues'] += 1
                
            # Calculate resolution time for closed issues
            if issue['closed_at']:
                metrics['closed_issues'] += 1
                created_at = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                closed_at = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                resolution_time = (closed_at - created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
                
        if resolution_times:
            metrics['avg_resolution_time_hours'] = sum(resolution_times) / len(resolution_times)
            
        if issues:
            metrics['bug_rate'] = metrics['bug_issues'] / len(issues) * 100
            metrics['resolution_rate'] = metrics['closed_issues'] / len(issues) * 100
            
        return metrics

    def collect_all_metrics(self, weeks: int = 4) -> Dict:
        """Collect all GitHub metrics for the specified period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        print(f"Collecting GitHub metrics from {start_date.date()} to {end_date.date()}")
        
        # Collect data
        prs = self.get_pull_requests(start_date, end_date)
        commits = self.get_commits(start_date, end_date)
        issues = self.get_issues(start_date, end_date)
        
        # Calculate metrics
        pr_metrics = self.calculate_pr_metrics(prs)
        commit_metrics = self.calculate_commit_metrics(commits)
        issue_metrics = self.calculate_issue_metrics(issues)
        
        # Combine all metrics
        all_metrics = {
            'collection_date': end_date.isoformat(),
            'period_weeks': weeks,
            'repository': f"{self.org}/{self.repo}",
            **pr_metrics,
            **commit_metrics,
            **issue_metrics
        }
        
        return all_metrics

def save_metrics_to_csv(metrics: Dict, filename: str):
    """Save metrics to CSV file"""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow(['Metric', 'Value'])
        
        # Write data
        for key, value in metrics.items():
            writer.writerow([key, value])
            
    print(f"Metrics saved to {filename}")

def save_metrics_to_json(metrics: Dict, filename: str):
    """Save metrics to JSON file"""
    with open(filename, 'w') as jsonfile:
        json.dump(metrics, jsonfile, indent=2)
        
    print(f"Metrics saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Collect GitHub repository metrics')
    parser.add_argument('--token', required=True, help='GitHub API token')
    parser.add_argument('--org', required=True, help='GitHub organization/owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to analyze')
    parser.add_argument('--output', default='github_metrics', help='Output file prefix')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both', 
                        help='Output format')
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = GitHubMetricsCollector(args.token, args.org, args.repo)
    
    # Collect metrics
    try:
        metrics = collector.collect_all_metrics(args.weeks)
        
        # Print summary
        print(f"\n--- GitHub Metrics Summary ---")
        print(f"Repository: {metrics['repository']}")
        print(f"Period: {metrics['period_weeks']} weeks")
        print(f"Total PRs: {metrics.get('total_prs', 0)}")
        print(f"Total Commits: {metrics.get('total_commits', 0)}")
        print(f"Total Issues: {metrics.get('total_issues', 0)}")
        print(f"AI Assistance Rate (PRs): {metrics.get('ai_assistance_rate', 0):.1f}%")
        print(f"Average Review Time: {metrics.get('avg_review_time_hours', 0):.1f} hours")
        print(f"Bug Rate: {metrics.get('bug_rate', 0):.1f}%")
        
        # Save to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if args.format in ['json', 'both']:
            filename = f"{args.output}_{timestamp}.json"
            save_metrics_to_json(metrics, filename)
            
        if args.format in ['csv', 'both']:
            filename = f"{args.output}_{timestamp}.csv"
            save_metrics_to_csv(metrics, filename)
            
    except Exception as e:
        print(f"Error collecting metrics: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main())