#!/usr/bin/env python3
"""
Apps Team Before/After AI Adoption Analysis
Compares individual developer productivity before and after AI adoption date
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from individual_developer_analyzer import IndividualDeveloperAnalyzer
from get_team_members import get_team_members
from datetime import datetime, timedelta
import json

class BeforeAfterAnalyzer(IndividualDeveloperAnalyzer):
    def __init__(self, config_path="config.json"):
        super().__init__(config_path)
        self.ai_adoption_date = datetime.fromisoformat(
            self.config['analysis']['copilot_adoption_date']
        )

    def analyze_user_before_after(self, username, weeks_before=8, weeks_after=8):
        """Analyze a user's productivity before and after AI adoption"""
        
        # Calculate date ranges
        before_end = self.ai_adoption_date
        before_start = before_end - timedelta(weeks=weeks_before)
        after_start = self.ai_adoption_date
        after_end = after_start + timedelta(weeks=weeks_after)
        
        print(f"\n🔍 Analyzing {username} - Before/After AI Adoption")
        print(f"   AI Adoption Date: {self.ai_adoption_date.strftime('%Y-%m-%d')}")
        print(f"   Before: {before_start.strftime('%Y-%m-%d')} to {before_end.strftime('%Y-%m-%d')} ({weeks_before} weeks)")
        print(f"   After:  {after_start.strftime('%Y-%m-%d')} to {after_end.strftime('%Y-%m-%d')} ({weeks_after} weeks)")
        
        # Analyze both periods
        before_data = self.analyze_user_period(username, before_start, before_end, "BEFORE")
        after_data = self.analyze_user_period(username, after_start, after_end, "AFTER")
        
        # Calculate improvements
        comparison = self.calculate_improvements(username, before_data, after_data, weeks_before, weeks_after)
        
        return {
            'username': username,
            'ai_adoption_date': self.ai_adoption_date.isoformat(),
            'before_period': {
                'start': before_start.isoformat(),
                'end': before_end.isoformat(),
                'weeks': weeks_before
            },
            'after_period': {
                'start': after_start.isoformat(),
                'end': after_end.isoformat(),
                'weeks': weeks_after
            },
            'before_data': before_data,
            'after_data': after_data,
            'comparison': comparison
        }

    def analyze_user_period(self, username, start_date, end_date, period_name):
        """Analyze a user's activity for a specific period"""
        
        print(f"      📊 {period_name} period...")
        
        period_data = {
            'commits': 0,
            'additions': 0,
            'deletions': 0,
            'total_changes': 0,
            'files_changed': 0,
            'repositories': {},
            'ai_indicators': 0
        }
        
        for repo in self.repositories:
            commits = self.get_commits_for_user_period(repo, username, start_date, end_date)
            if not commits:
                continue
                
            repo_stats = {
                'commits': len(commits),
                'additions': 0,
                'deletions': 0,
                'total_changes': 0,
                'files_changed': 0
            }
            
            # Get detailed stats for up to 15 commits per repo per period
            for i, commit in enumerate(commits[:15]):
                details = self.get_commit_details(repo, commit['sha'])
                if details and 'stats' in details:
                    stats = details['stats']
                    repo_stats['additions'] += stats.get('additions', 0)
                    repo_stats['deletions'] += stats.get('deletions', 0)
                    repo_stats['total_changes'] += stats.get('total', 0)
                    repo_stats['files_changed'] += len(details.get('files', []))
                    
                    # Check for AI indicators
                    message = commit['commit']['message'].lower()
                    if any(keyword in message for keyword in ['copilot', 'ai-generated', 'ai-assisted', 'auto-generated']):
                        period_data['ai_indicators'] += 1
            
            period_data['repositories'][repo] = repo_stats
            period_data['commits'] += repo_stats['commits']
            period_data['additions'] += repo_stats['additions']
            period_data['deletions'] += repo_stats['deletions']
            period_data['total_changes'] += repo_stats['total_changes']
            period_data['files_changed'] += repo_stats['files_changed']
        
        print(f"         {period_data['commits']} commits, {period_data['total_changes']:,} changes")
        return period_data

    def get_commits_for_user_period(self, repo, username, start_date, end_date):
        """Get commits for a user in a specific date range"""
        url = f"https://api.github.com/repos/{self.org}/{repo}/commits"
        params = {
            'author': username,
            'since': start_date.isoformat(),
            'until': end_date.isoformat(),
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
            
            if len(all_commits) > 100:  # Reasonable limit
                break
                
        return all_commits

    def calculate_improvements(self, username, before, after, weeks_before, weeks_after):
        """Calculate percentage improvements between before and after periods"""
        
        # Normalize to weekly rates
        before_weekly = {
            'commits_per_week': before['commits'] / weeks_before if weeks_before > 0 else 0,
            'changes_per_week': before['total_changes'] / weeks_before if weeks_before > 0 else 0,
            'additions_per_week': before['additions'] / weeks_before if weeks_before > 0 else 0,
            'files_per_week': before['files_changed'] / weeks_before if weeks_before > 0 else 0
        }
        
        after_weekly = {
            'commits_per_week': after['commits'] / weeks_after if weeks_after > 0 else 0,
            'changes_per_week': after['total_changes'] / weeks_after if weeks_after > 0 else 0,
            'additions_per_week': after['additions'] / weeks_after if weeks_after > 0 else 0,
            'files_per_week': after['files_changed'] / weeks_after if weeks_after > 0 else 0
        }
        
        # Calculate percentage changes
        improvements = {}
        for metric in before_weekly:
            before_val = before_weekly[metric]
            after_val = after_weekly[metric]
            
            if before_val > 0:
                improvement = ((after_val - before_val) / before_val) * 100
            elif after_val > 0:
                improvement = 100  # Started from zero
            else:
                improvement = 0
                
            improvements[metric.replace('_per_week', '_improvement_pct')] = improvement
        
        # Changes per commit efficiency
        before_avg = before['total_changes'] / before['commits'] if before['commits'] > 0 else 0
        after_avg = after['total_changes'] / after['commits'] if after['commits'] > 0 else 0
        
        if before_avg > 0:
            improvements['changes_per_commit_improvement_pct'] = ((after_avg - before_avg) / before_avg) * 100
        elif after_avg > 0:
            improvements['changes_per_commit_improvement_pct'] = 100
        else:
            improvements['changes_per_commit_improvement_pct'] = 0
        
        # AI adoption indicator
        improvements['ai_indicators_change'] = after['ai_indicators'] - before['ai_indicators']
        
        return {
            'before_weekly': before_weekly,
            'after_weekly': after_weekly,
            'improvements': improvements,
            'summary': {
                'commits_change': f"{before_weekly['commits_per_week']:.1f} → {after_weekly['commits_per_week']:.1f} per week ({improvements['commits_improvement_pct']:+.1f}%)",
                'changes_change': f"{before_weekly['changes_per_week']:,.1f} → {after_weekly['changes_per_week']:,.1f} per week ({improvements['changes_improvement_pct']:+.1f}%)",
                'efficiency_change': f"{before_avg:.1f} → {after_avg:.1f} changes/commit ({improvements['changes_per_commit_improvement_pct']:+.1f}%)"
            }
        }

    def print_user_before_after_summary(self, analysis):
        """Print a summary of before/after analysis for a user"""
        username = analysis['username']
        comparison = analysis['comparison']
        improvements = comparison['improvements']
        
        print(f"\n📊 BEFORE/AFTER SUMMARY FOR {username.upper()}")
        print("=" * 60)
        
        if analysis['before_data']['commits'] == 0 and analysis['after_data']['commits'] == 0:
            print("   No commits found in either period")
            return
        
        print(f"Commits per week: {comparison['summary']['commits_change']}")
        print(f"Changes per week: {comparison['summary']['changes_change']}")
        print(f"Changes per commit: {comparison['summary']['efficiency_change']}")
        
        if improvements['ai_indicators_change'] > 0:
            print(f"AI indicators: +{improvements['ai_indicators_change']} (increased AI usage)")
        elif improvements['ai_indicators_change'] < 0:
            print(f"AI indicators: {improvements['ai_indicators_change']} (decreased AI usage)")
        
        # Repository activity changes
        before_repos = set(analysis['before_data']['repositories'].keys())
        after_repos = set(analysis['after_data']['repositories'].keys())
        
        if before_repos or after_repos:
            print(f"\nRepository Activity:")
            all_repos = before_repos.union(after_repos)
            for repo in sorted(all_repos):
                before_commits = analysis['before_data']['repositories'].get(repo, {}).get('commits', 0)
                after_commits = analysis['after_data']['repositories'].get(repo, {}).get('commits', 0)
                if before_commits > 0 or after_commits > 0:
                    change_pct = ((after_commits - before_commits) / before_commits * 100) if before_commits > 0 else (100 if after_commits > 0 else 0)
                    print(f"  {repo}: {before_commits} → {after_commits} commits ({change_pct:+.0f}%)")

def main():
    print("🔍 Apps Team Before/After AI Adoption Analysis")
    print("=" * 60)
    
    analyzer = BeforeAfterAnalyzer()
    
    # Get apps-team members
    print("Fetching apps-team members...")
    usernames = get_team_members(
        analyzer.config['github']['token'],
        analyzer.config['github']['organization'],
        'apps-team'
    )
    
    if not usernames:
        print("❌ Could not fetch team members. Exiting.")
        return
    
    print(f"\n🎯 Analyzing {len(usernames)} developers before/after AI adoption...")
    print(f"AI Adoption Date: {analyzer.ai_adoption_date.strftime('%Y-%m-%d')}")
    
    all_analyses = []
    team_improvements = {
        'commits_improvement_pct': [],
        'changes_improvement_pct': [],
        'changes_per_commit_improvement_pct': [],
        'developers_improved': 0,
        'developers_with_ai_indicators': 0
    }
    
    for username in usernames:
        try:
            analysis = analyzer.analyze_user_before_after(username, weeks_before=8, weeks_after=8)
            all_analyses.append(analysis)
            analyzer.print_user_before_after_summary(analysis)
            
            # Collect team-level improvements
            if analysis['before_data']['commits'] >= 3 and analysis['after_data']['commits'] >= 3:  # Minimum activity threshold
                improvements = analysis['comparison']['improvements']
                team_improvements['commits_improvement_pct'].append(improvements['commits_improvement_pct'])
                team_improvements['changes_improvement_pct'].append(improvements['changes_improvement_pct'])
                team_improvements['changes_per_commit_improvement_pct'].append(improvements['changes_per_commit_improvement_pct'])
                
                if improvements['changes_improvement_pct'] > 0:
                    team_improvements['developers_improved'] += 1
                
                if improvements['ai_indicators_change'] > 0:
                    team_improvements['developers_with_ai_indicators'] += 1
            
            print("\n" + "-" * 60)
            
        except Exception as e:
            print(f"❌ Error analyzing {username}: {e}")
            continue
    
    # Team-level analysis
    print(f"\n📈 APPS TEAM AI ADOPTION IMPACT ANALYSIS")
    print("=" * 60)
    
    qualified_developers = len(team_improvements['commits_improvement_pct'])
    
    if qualified_developers == 0:
        print("No developers with sufficient activity in both periods for comparison.")
        return
    
    # Calculate averages
    avg_commits_improvement = sum(team_improvements['commits_improvement_pct']) / len(team_improvements['commits_improvement_pct'])
    avg_changes_improvement = sum(team_improvements['changes_improvement_pct']) / len(team_improvements['changes_improvement_pct'])
    avg_efficiency_improvement = sum(team_improvements['changes_per_commit_improvement_pct']) / len(team_improvements['changes_per_commit_improvement_pct'])
    
    print(f"Developers Analyzed: {qualified_developers} (with sufficient activity in both periods)")
    print(f"")
    print(f"📊 TEAM PRODUCTIVITY CHANGES:")
    print(f"Average Commits Improvement: {avg_commits_improvement:+.1f}%")
    print(f"Average Changes Improvement: {avg_changes_improvement:+.1f}%")
    print(f"Average Efficiency Improvement: {avg_efficiency_improvement:+.1f}% (changes per commit)")
    print(f"")
    print(f"🎯 ADOPTION INDICATORS:")
    print(f"Developers with Productivity Gains: {team_improvements['developers_improved']}/{qualified_developers} ({team_improvements['developers_improved']/qualified_developers*100:.0f}%)")
    print(f"Developers with AI Usage Indicators: {team_improvements['developers_with_ai_indicators']}/{qualified_developers} ({team_improvements['developers_with_ai_indicators']/qualified_developers*100:.0f}%)")
    
    # Rank developers by improvement
    qualified_analyses = [a for a in all_analyses if a['before_data']['commits'] >= 3 and a['after_data']['commits'] >= 3]
    qualified_analyses.sort(key=lambda x: x['comparison']['improvements']['changes_improvement_pct'], reverse=True)
    
    print(f"\n🏆 TOP IMPROVERS (Changes per week):")
    for i, analysis in enumerate(qualified_analyses[:8], 1):
        username = analysis['username']
        improvements = analysis['comparison']['improvements']
        summary = analysis['comparison']['summary']
        print(f"  {i:2d}. {username:<20} | {summary['changes_change']}")
    
    if len(qualified_analyses) > 8:
        print(f"\n📉 DEVELOPERS WITH DECREASED PRODUCTIVITY:")
        negative_improvements = [a for a in qualified_analyses if a['comparison']['improvements']['changes_improvement_pct'] < 0]
        for analysis in negative_improvements[-5:]:
            username = analysis['username']
            summary = analysis['comparison']['summary']
            print(f"      {username:<20} | {summary['changes_change']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"apps_team_before_after_analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'team': 'apps-team',
            'ai_adoption_date': analyzer.ai_adoption_date.isoformat(),
            'qualified_developers': qualified_developers,
            'team_improvements': {
                'avg_commits_improvement': avg_commits_improvement,
                'avg_changes_improvement': avg_changes_improvement,
                'avg_efficiency_improvement': avg_efficiency_improvement,
                'developers_improved': team_improvements['developers_improved'],
                'developers_with_ai_indicators': team_improvements['developers_with_ai_indicators']
            },
            'individual_analyses': all_analyses
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == '__main__':
    import requests
    main()