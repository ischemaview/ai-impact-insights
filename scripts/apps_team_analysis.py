#!/usr/bin/env python3
"""
Apps Team Analysis - Last 90 Days
Analyzes all apps-team members' productivity over the past 90 days
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from individual_developer_analyzer import IndividualDeveloperAnalyzer
from get_team_members import get_team_members
from datetime import datetime
import json

def main():
    print("🔍 Apps Team Individual Analysis - Last 90 Days")
    print("=" * 60)
    
    analyzer = IndividualDeveloperAnalyzer()
    
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
    
    print(f"\n🎯 Analyzing {len(usernames)} apps-team members...")
    
    all_user_data = []
    
    for username in usernames:
        try:
            user_data = analyzer.analyze_user_activity(username, days=90)
            all_user_data.append(user_data)
            analyzer.print_user_summary(user_data)
            
            # Add some spacing between users
            print("\n" + "-" * 60)
            
        except Exception as e:
            print(f"❌ Error analyzing {username}: {e}")
            continue
    
    # Comparative analysis
    print(f"\n📈 APPS TEAM COMPARATIVE ANALYSIS")
    print("=" * 60)
    
    # Filter out users with no commits
    productive_users = [(data['username'], data['totals']) for data in all_user_data if data['totals']['commits'] > 0]
    
    if not productive_users:
        print("No productive users found in the analysis period.")
        return
    
    # Sort by different metrics
    print(f"\n🏆 RANKING BY TOTAL CODE CHANGES (Last 90 days):")
    changes_ranking = sorted(productive_users, key=lambda x: x[1]['total_changes'], reverse=True)
    
    for i, (username, totals) in enumerate(changes_ranking, 1):
        changes_per_day = totals['total_changes'] / 90
        commits_per_day = totals['commits'] / 90
        avg_per_commit = totals['total_changes'] / totals['commits'] if totals['commits'] > 0 else 0
        
        print(f"  {i:2d}. {username:<20} | {totals['total_changes']:>6,} changes | {changes_per_day:>5.1f}/day | {totals['commits']:>3d} commits | {avg_per_commit:>5.1f} avg/commit")
    
    print(f"\n🚀 RANKING BY COMMIT FREQUENCY (Last 90 days):")
    commit_ranking = sorted(productive_users, key=lambda x: x[1]['commits'], reverse=True)
    
    for i, (username, totals) in enumerate(commit_ranking, 1):
        commits_per_day = totals['commits'] / 90
        print(f"  {i:2d}. {username:<20} | {totals['commits']:>3d} commits | {commits_per_day:>5.1f}/day | {totals['total_changes']:>6,} changes")
    
    # Pattern analysis
    print(f"\n🔍 PATTERN ANALYSIS:")
    
    # High volume, low frequency (big commits)
    big_committers = [(name, totals) for name, totals in productive_users if totals['commits'] > 0]
    big_committers.sort(key=lambda x: x[1]['total_changes'] / x[1]['commits'], reverse=True)
    
    print(f"\nMost Code per Commit (Big Committers):")
    for i, (username, totals) in enumerate(big_committers[:5], 1):
        avg_per_commit = totals['total_changes'] / totals['commits']
        print(f"  {i}. {username}: {avg_per_commit:.1f} changes/commit ({totals['commits']} commits)")
    
    # High frequency committers
    frequent_committers = sorted(productive_users, key=lambda x: x[1]['commits'] / 90, reverse=True)
    
    print(f"\nMost Frequent Committers:")
    for i, (username, totals) in enumerate(frequent_committers[:5], 1):
        commits_per_day = totals['commits'] / 90
        print(f"  {i}. {username}: {commits_per_day:.1f} commits/day ({totals['commits']} total)")
    
    # Activity distribution
    total_team_commits = sum(totals['commits'] for _, totals in productive_users)
    total_team_changes = sum(totals['total_changes'] for _, totals in productive_users)
    
    print(f"\n📊 TEAM SUMMARY:")
    print(f"Team Size Analyzed: {len(productive_users)} active developers")
    print(f"Total Team Commits: {total_team_commits:,} (last 90 days)")
    print(f"Total Team Changes: {total_team_changes:,} lines")
    print(f"Average per Developer: {total_team_commits / len(productive_users):.1f} commits, {total_team_changes / len(productive_users):,.1f} changes")
    print(f"Team Daily Output: {total_team_commits / 90:.1f} commits/day, {total_team_changes / 90:,.1f} changes/day")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"apps_team_analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'team': 'apps-team',
            'period_days': 90,
            'team_members': usernames,
            'active_members': len(productive_users),
            'team_totals': {
                'commits': total_team_commits,
                'changes': total_team_changes
            },
            'detailed_results': all_user_data,
            'rankings': {
                'by_changes': [(name, totals['total_changes']) for name, totals in changes_ranking],
                'by_commits': [(name, totals['commits']) for name, totals in commit_ranking]
            }
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == '__main__':
    main()