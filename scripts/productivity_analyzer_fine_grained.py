#!/usr/bin/env python3
"""
GitHub Productivity Before/After Analysis (Fine-Grained Token Compatible)
Focuses on commit-based productivity analysis that works with fine-grained tokens
"""

import requests
import json
import os
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Optional
from collections import defaultdict

class ProductivityAnalyzer:
    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration file"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.github_token = self.config['github']['token']
        self.org = self.config['github']['organization']
        self.repositories = self.config['github']['repositories']
        
        self.headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self.base_url = 'https://api.github.com'
        
        # Parse adoption date (could be any AI tool, not just Copilot)
        self.ai_adoption_date = datetime.fromisoformat(
            self.config['analysis']['copilot_adoption_date']  # Keep same config key for compatibility
        )

    def test_api_access(self) -> Dict[str, bool]:
        """Test what API endpoints we can access with current token"""
        tests = {}
        
        # Test basic repo access
        test_repo = self.repositories[0] if self.repositories else "test"
        url = f"{self.base_url}/repos/{self.org}/{test_repo}"
        response = requests.get(url, headers=self.headers)
        tests['repository_access'] = response.status_code == 200
        
        # Test org access
        url = f"{self.base_url}/orgs/{self.org}"
        response = requests.get(url, headers=self.headers)
        tests['organization_access'] = response.status_code == 200
        
        # Test Copilot API access (may fail with fine-grained tokens)
        url = f"{self.base_url}/orgs/{self.org}/copilot/usage"
        response = requests.get(url, headers=self.headers)
        tests['copilot_api_access'] = response.status_code == 200
        
        return tests

    def get_repository_commits(self, repo: str, since: str, until: str) -> List[Dict]:
        """Get commits for a repository in the specified date range"""
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
                print(f"Error fetching commits for {repo}: {response.status_code}")
                if response.status_code == 403:
                    print("Rate limit hit - waiting and continuing with collected data...")
                break
                
            commits = response.json()
            if not commits:
                break
                
            all_commits.extend(commits)
            page += 1
            
            # Reasonable limit to avoid rate limiting
            if len(all_commits) > 500:
                break
                
        return all_commits

    def get_commit_details(self, repo: str, sha: str) -> Optional[Dict]:
        """Get detailed commit information including line changes"""
        url = f"{self.base_url}/repos/{self.org}/{repo}/commits/{sha}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print("Rate limit hit on commit details - using basic stats")
        return None

    def detect_ai_assistance(self, commit: Dict) -> Dict:
        """
        Detect potential AI assistance in commits using various heuristics
        Works without Copilot API access
        """
        message = commit.get('commit', {}).get('message', '').lower()
        
        # AI tool indicators in commit messages
        ai_keywords = [
            'copilot', 'github copilot', 'ai-generated', 'ai-assisted', 'ai generated',
            'chatgpt', 'gpt', 'claude', 'ai suggested', 'auto-generated',
            'code completion', 'ai completion', 'suggested by ai'
        ]
        
        # Code generation patterns
        generation_patterns = [
            'generated boilerplate', 'auto-complete', 'scaffolded',
            'template generated', 'bulk generation'
        ]
        
        # Documentation assistance patterns
        docs_patterns = [
            'added docstrings', 'generated comments', 'auto-documented',
            'documentation update', 'comment generation'
        ]
        
        indicators = {
            'explicit_ai_mention': any(keyword in message for keyword in ai_keywords),
            'generation_pattern': any(pattern in message for pattern in generation_patterns),
            'docs_pattern': any(pattern in message for pattern in docs_patterns),
            'bulk_changes': 'bulk' in message or 'mass' in message or 'multiple files' in message
        }
        
        # Overall AI likelihood score
        score = sum([
            indicators['explicit_ai_mention'] * 3,  # Highest weight
            indicators['generation_pattern'] * 2,
            indicators['docs_pattern'] * 1,
            indicators['bulk_changes'] * 1
        ])
        
        indicators['ai_likelihood_score'] = score
        indicators['likely_ai_assisted'] = score >= 2
        
        return indicators

    def analyze_user_productivity(self, commits: List[Dict], repo: str) -> Dict:
        """Analyze productivity metrics from commits"""
        user_stats = defaultdict(lambda: {
            'commits': 0,
            'total_additions': 0,
            'total_deletions': 0,
            'total_changes': 0,
            'commit_dates': [],
            'files_changed': 0,
            'ai_assisted_commits': 0,
            'ai_likelihood_scores': []
        })
        
        for i, commit in enumerate(commits):
            author_login = None
            if commit.get('author') and isinstance(commit['author'], dict):
                author_login = commit['author'].get('login')
            
            if not author_login:
                # Skip commits without valid author information
                continue
                
            commit_date = datetime.fromisoformat(
                commit['commit']['author']['date'].replace('Z', '+00:00')
            )
            
            user_stats[author_login]['commits'] += 1
            user_stats[author_login]['commit_dates'].append(commit_date)
            
            # Detect AI assistance
            ai_indicators = self.detect_ai_assistance(commit)
            user_stats[author_login]['ai_likelihood_scores'].append(ai_indicators['ai_likelihood_score'])
            if ai_indicators['likely_ai_assisted']:
                user_stats[author_login]['ai_assisted_commits'] += 1
            
            # Get detailed stats for sample of commits (to avoid rate limits)
            if i < 50:  # Sample first 50 commits
                details = self.get_commit_details(repo, commit['sha'])
                if details and 'stats' in details:
                    stats = details['stats']
                    additions = stats.get('additions', 0)
                    deletions = stats.get('deletions', 0)
                    total = stats.get('total', 0)
                    
                    user_stats[author_login]['total_additions'] += additions
                    user_stats[author_login]['total_deletions'] += deletions
                    user_stats[author_login]['total_changes'] += total
                    user_stats[author_login]['files_changed'] += len(details.get('files', []))
        
        # Calculate derived metrics
        for user, stats in user_stats.items():
            if stats['commit_dates']:
                # Calculate active days
                dates = [d.date() for d in stats['commit_dates']]
                unique_dates = len(set(dates))
                stats['active_days'] = unique_dates
                stats['commits_per_active_day'] = stats['commits'] / unique_dates if unique_dates > 0 else 0
                
                # Estimate total changes for all commits
                sampled_commits = min(50, stats['commits'])
                if sampled_commits > 0 and stats['total_changes'] > 0:
                    avg_changes_per_commit = stats['total_changes'] / sampled_commits
                    stats['estimated_total_changes'] = avg_changes_per_commit * stats['commits']
                else:
                    stats['estimated_total_changes'] = stats['total_changes']
                
                # AI assistance metrics
                stats['ai_assistance_rate'] = (stats['ai_assisted_commits'] / stats['commits'] * 100) if stats['commits'] > 0 else 0
                stats['avg_ai_likelihood'] = sum(stats['ai_likelihood_scores']) / len(stats['ai_likelihood_scores']) if stats['ai_likelihood_scores'] else 0
        
        return dict(user_stats)

    def run_before_after_analysis(self) -> Dict:
        """Run the main before/after analysis"""
        # Test API access first
        print("Testing API access...")
        api_tests = self.test_api_access()
        print(f"Repository access: {'✓' if api_tests['repository_access'] else '✗'}")
        print(f"Organization access: {'✓' if api_tests['organization_access'] else '✗'}")
        print(f"Copilot API access: {'✓' if api_tests['copilot_api_access'] else '✗'}")
        
        if not api_tests['repository_access']:
            raise Exception("Cannot access repositories. Check your token permissions.")
        
        before_weeks = self.config['analysis']['before_period_weeks']
        after_weeks = self.config['analysis']['after_period_weeks']
        
        # Calculate date ranges
        before_end = self.ai_adoption_date
        before_start = before_end - timedelta(weeks=before_weeks)
        
        after_start = self.ai_adoption_date
        after_end = after_start + timedelta(weeks=after_weeks)
        
        print(f"\nAnalyzing productivity impact for organization: {self.org}")
        print(f"AI tool adoption date: {self.ai_adoption_date.date()}")
        print(f"Before period: {before_start.date()} to {before_end.date()}")
        print(f"After period: {after_start.date()} to {after_end.date()}")
        
        all_before_stats = {}
        all_after_stats = {}
        
        # Analyze each repository
        for repo in self.repositories:
            print(f"\nAnalyzing repository: {repo}")
            
            # Before period
            print("  Fetching 'before' commits...")
            before_commits = self.get_repository_commits(
                repo, 
                before_start.isoformat(), 
                before_end.isoformat()
            )
            before_stats = self.analyze_user_productivity(before_commits, repo)
            all_before_stats[repo] = before_stats
            
            # After period  
            print("  Fetching 'after' commits...")
            after_commits = self.get_repository_commits(
                repo,
                after_start.isoformat(),
                after_end.isoformat()
            )
            after_stats = self.analyze_user_productivity(after_commits, repo)
            all_after_stats[repo] = after_stats
            
            print(f"  Before: {len(before_commits)} commits, After: {len(after_commits)} commits")
        
        # Aggregate and compare
        analysis_results = self.compare_before_after(all_before_stats, all_after_stats)
        
        # Add metadata
        analysis_results['metadata'] = {
            'organization': self.org,
            'ai_adoption_date': self.ai_adoption_date.isoformat(),
            'analysis_periods': {
                'before': {
                    'start': before_start.isoformat(),
                    'end': before_end.isoformat(),
                    'weeks': before_weeks
                },
                'after': {
                    'start': after_start.isoformat(),
                    'end': after_end.isoformat(),
                    'weeks': after_weeks
                }
            },
            'repositories_analyzed': self.repositories,
            'api_access': api_tests,
            'analysis_date': datetime.now().isoformat()
        }
        
        return analysis_results

    def compare_before_after(self, before_stats: Dict, after_stats: Dict) -> Dict:
        """Compare user productivity before and after AI tool adoption"""
        
        # Aggregate user stats across all repositories
        user_before = defaultdict(lambda: {
            'commits': 0, 'total_changes': 0, 'active_days': 0, 'ai_assisted_commits': 0, 'repos': []
        })
        user_after = defaultdict(lambda: {
            'commits': 0, 'total_changes': 0, 'active_days': 0, 'ai_assisted_commits': 0, 'repos': []
        })
        
        # Aggregate before stats
        for repo, repo_stats in before_stats.items():
            for user, stats in repo_stats.items():
                user_before[user]['commits'] += stats['commits']
                user_before[user]['total_changes'] += stats['estimated_total_changes']
                user_before[user]['active_days'] += stats['active_days']
                user_before[user]['ai_assisted_commits'] += stats['ai_assisted_commits']
                user_before[user]['repos'].append(repo)
        
        # Aggregate after stats
        for repo, repo_stats in after_stats.items():
            for user, stats in repo_stats.items():
                user_after[user]['commits'] += stats['commits']
                user_after[user]['total_changes'] += stats['estimated_total_changes']
                user_after[user]['active_days'] += stats['active_days']
                user_after[user]['ai_assisted_commits'] += stats['ai_assisted_commits']
                user_after[user]['repos'].append(repo)
        
        # Find users who were active both before and after
        before_users = set(user_before.keys())
        after_users = set(user_after.keys())
        common_users = before_users.intersection(after_users)
        
        min_commits = self.config['analysis']['min_commits_for_analysis']
        qualified_users = [
            user for user in common_users 
            if user_before[user]['commits'] >= min_commits and 
               user_after[user]['commits'] >= min_commits
        ]
        
        print(f"\nFound {len(qualified_users)} users with sufficient activity in both periods")
        
        # Calculate improvements for qualified users
        user_comparisons = {}
        improvements = {
            'commits_per_week': [],
            'changes_per_week': [],
            'commits_per_active_day': [],
            'ai_assistance_adoption': []
        }
        
        for user in qualified_users:
            before = user_before[user]
            after = user_after[user]
            
            before_weeks = self.config['analysis']['before_period_weeks']
            after_weeks = self.config['analysis']['after_period_weeks']
            
            # Calculate weekly averages
            before_commits_per_week = before['commits'] / before_weeks
            after_commits_per_week = after['commits'] / after_weeks
            
            before_changes_per_week = before['total_changes'] / before_weeks
            after_changes_per_week = after['total_changes'] / after_weeks
            
            # Calculate daily averages
            before_commits_per_active_day = before['commits'] / before['active_days'] if before['active_days'] > 0 else 0
            after_commits_per_active_day = after['commits'] / after['active_days'] if after['active_days'] > 0 else 0
            
            # AI assistance rates
            before_ai_rate = (before['ai_assisted_commits'] / before['commits'] * 100) if before['commits'] > 0 else 0
            after_ai_rate = (after['ai_assisted_commits'] / after['commits'] * 100) if after['commits'] > 0 else 0
            
            # Calculate percentage improvements
            commits_improvement = ((after_commits_per_week - before_commits_per_week) / before_commits_per_week * 100) if before_commits_per_week > 0 else 0
            changes_improvement = ((after_changes_per_week - before_changes_per_week) / before_changes_per_week * 100) if before_changes_per_week > 0 else 0
            daily_commits_improvement = ((after_commits_per_active_day - before_commits_per_active_day) / before_commits_per_active_day * 100) if before_commits_per_active_day > 0 else 0
            ai_adoption_change = after_ai_rate - before_ai_rate
            
            user_comparisons[user] = {
                'before': {
                    'commits_per_week': before_commits_per_week,
                    'changes_per_week': before_changes_per_week,
                    'commits_per_active_day': before_commits_per_active_day,
                    'ai_assistance_rate': before_ai_rate,
                    'total_commits': before['commits'],
                    'active_days': before['active_days']
                },
                'after': {
                    'commits_per_week': after_commits_per_week,
                    'changes_per_week': after_changes_per_week,
                    'commits_per_active_day': after_commits_per_active_day,
                    'ai_assistance_rate': after_ai_rate,
                    'total_commits': after['commits'],
                    'active_days': after['active_days']
                },
                'improvements': {
                    'commits_per_week_pct': commits_improvement,
                    'changes_per_week_pct': changes_improvement,
                    'commits_per_active_day_pct': daily_commits_improvement,
                    'ai_adoption_change_pct': ai_adoption_change
                }
            }
            
            improvements['commits_per_week'].append(commits_improvement)
            improvements['changes_per_week'].append(changes_improvement)
            improvements['commits_per_active_day'].append(daily_commits_improvement)
            improvements['ai_assistance_adoption'].append(ai_adoption_change)
        
        # Calculate summary statistics
        summary = {}
        for metric, values in improvements.items():
            if values:
                summary[metric] = {
                    'avg_improvement_pct': sum(values) / len(values),
                    'median_improvement_pct': sorted(values)[len(values)//2],
                    'users_improved': len([v for v in values if v > 0]),
                    'users_declined': len([v for v in values if v < 0]),
                    'total_users': len(values)
                }
        
        return {
            'summary': summary,
            'user_comparisons': user_comparisons,
            'analysis_stats': {
                'total_users_before': len(before_users),
                'total_users_after': len(after_users),
                'common_users': len(common_users),
                'qualified_users': len(qualified_users),
                'min_commits_threshold': min_commits
            }
        }

    def print_summary(self, results: Dict):
        """Print a human-readable summary of the analysis"""
        print("\n" + "="*60)
        print("AI TOOLS PRODUCTIVITY ANALYSIS SUMMARY")
        print("="*60)
        
        metadata = results['metadata']
        print(f"Organization: {metadata['organization']}")
        print(f"AI Adoption: {metadata['ai_adoption_date'][:10]}")
        print(f"Analysis Period: {metadata['analysis_periods']['before']['weeks']} weeks before/after")
        
        api_access = metadata['api_access']
        print(f"Copilot API Available: {'Yes' if api_access['copilot_api_access'] else 'No (using commit analysis)'}")
        
        stats = results['analysis_stats']
        print(f"\nUsers Analyzed: {stats['qualified_users']} (min {stats['min_commits_threshold']} commits)")
        
        summary = results['summary']
        print(f"\nPRODUCTIVITY IMPROVEMENTS:")
        
        for metric, data in summary.items():
            metric_name = metric.replace('_', ' ').title()
            if 'ai_assistance' in metric:
                print(f"\n{metric_name}:")
                print(f"  Average change: {data['avg_improvement_pct']:+.1f} percentage points")
            else:
                print(f"\n{metric_name}:")
                print(f"  Average improvement: {data['avg_improvement_pct']:+.1f}%")
            print(f"  Users improved: {data['users_improved']}/{data['total_users']} ({data['users_improved']/data['total_users']*100:.0f}%)")
            
        # Show top performers
        user_comparisons = results['user_comparisons']
        if user_comparisons:
            print(f"\nTOP PERFORMERS (Commits per week improvement):")
            sorted_users = sorted(
                user_comparisons.items(), 
                key=lambda x: x[1]['improvements']['commits_per_week_pct'],
                reverse=True
            )[:5]
            
            for user, data in sorted_users:
                improvement = data['improvements']['commits_per_week_pct']
                before_rate = data['before']['commits_per_week']
                after_rate = data['after']['commits_per_week']
                ai_change = data['improvements']['ai_adoption_change_pct']
                print(f"  {user}: {before_rate:.1f} → {after_rate:.1f} commits/week ({improvement:+.1f}%) | AI usage: {ai_change:+.1f}pp")

def main():
    parser = argparse.ArgumentParser(description='Analyze AI tools productivity impact (Fine-grained token compatible)')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', help='Output file (optional)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        print("Please copy config.json.example to config.json and configure it.")
        return 1
    
    try:
        analyzer = ProductivityAnalyzer(args.config)
        results = analyzer.run_before_after_analysis()
        
        # Print summary
        analyzer.print_summary(results)
        
        # Save detailed results
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"ai_productivity_analysis_{timestamp}.json"
            
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())