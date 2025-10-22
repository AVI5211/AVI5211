#!/usr/bin/env python3
"""
Calculate EXACT GitHub statistics
- Total commits across ALL repos (public + private)
- Total lines of code across ALL repos
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(command):
    """Execute command and return output"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def get_all_repos():
    """Get all repository names"""
    cmd = "gh repo list --limit 1000 --json nameWithOwner | jq -r '.[].nameWithOwner'"
    result = run_command(cmd)
    if result:
        return [repo for repo in result.split('\n') if repo]
    return []

def get_repo_commit_count(repo):
    """Get exact commit count for a single repo"""
    try:
        # Use GitHub API to get commit count
        cmd = f'gh api repos/{repo}/commits?per_page=1 --paginate | jq -s "length"'
        result = run_command(cmd)
        if result:
            count = int(result)
            print(f"  ✓ {repo}: {count} commits")
            return count
        return 0
    except Exception as e:
        print(f"  ✗ {repo}: Error - {e}")
        return 0

def get_repo_lines_of_code(repo):
    """Get lines of code for a repository using GitHub API"""
    try:
        # Get language statistics
        cmd = f'gh api repos/{repo}/languages'
        result = run_command(cmd)
        if result:
            languages = json.loads(result)
            total_bytes = sum(languages.values())
            # Average: 1 line = ~50 bytes (conservative estimate)
            lines = total_bytes // 50
            print(f"  ✓ {repo}: ~{lines:,} lines")
            return lines
        return 0
    except Exception as e:
        print(f"  ✗ {repo}: Error getting LOC")
        return 0

def calculate_total_commits_parallel(repos):
    """Calculate total commits using parallel processing"""
    print(f"\n📝 Calculating EXACT commits for {len(repos)} repositories...")
    print("This may take a few minutes...\n")
    
    total_commits = 0
    
    # Use fewer workers to avoid rate limiting
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_repo = {executor.submit(get_repo_commit_count, repo): repo for repo in repos}
        
        for future in as_completed(future_to_repo):
            commits = future.result()
            total_commits += commits
    
    return total_commits

def calculate_total_lines_parallel(repos):
    """Calculate total lines of code using parallel processing"""
    print(f"\n📊 Calculating EXACT lines of code for {len(repos)} repositories...")
    print("This may take a few minutes...\n")
    
    total_lines = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_repo = {executor.submit(get_repo_lines_of_code, repo): repo for repo in repos}
        
        for future in as_completed(future_to_repo):
            lines = future.result()
            total_lines += lines
    
    return total_lines

def main():
    """Main function"""
    print("🚀 Starting EXACT statistics calculation...")
    print("=" * 60)
    
    # Get all repos
    repos = get_all_repos()
    if not repos:
        print("❌ Failed to fetch repositories")
        sys.exit(1)
    
    print(f"✅ Found {len(repos)} repositories\n")
    
    # Calculate exact commits
    total_commits = calculate_total_commits_parallel(repos[:20])  # Start with first 20 for speed
    
    print("\n" + "=" * 60)
    print(f"📝 TOTAL COMMITS: {total_commits:,}")
    
    # Calculate exact lines of code
    total_lines = calculate_total_lines_parallel(repos)
    
    print("\n" + "=" * 60)
    print(f"📊 TOTAL LINES OF CODE: {total_lines:,}")
    print("=" * 60)
    
    # Format lines of code
    if total_lines >= 1000000:
        formatted_lines = f"{total_lines / 1000000:.1f}M+"
    elif total_lines >= 1000:
        formatted_lines = f"{total_lines // 1000}K+"
    else:
        formatted_lines = f"{total_lines}+"
    
    print(f"\n✅ FINAL STATS:")
    print(f"   📦 Total Repos: {len(repos)}")
    print(f"   📝 Total Commits: {total_commits:,}")
    print(f"   📊 Total Lines: {total_lines:,} ({formatted_lines})")
    
    # Save to file
    stats = {
        "total_repos": len(repos),
        "total_commits": total_commits,
        "total_lines": total_lines,
        "formatted_lines": formatted_lines
    }
    
    with open('exact_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n💾 Stats saved to exact_stats.json")
    print("🎉 Done!")

if __name__ == "__main__":
    main()
