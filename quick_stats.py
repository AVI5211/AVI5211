#!/usr/bin/env python3
"""Quick GitHub Stats - Fast and Simple"""

import json
import subprocess

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

print("🚀 Fetching GitHub Statistics...\n")

# 1. Total repos
print("📦 Counting repositories...")
repos = run_cmd("gh repo list --limit 1000 --json nameWithOwner")
repos_data = json.loads(repos)
total_repos = len(repos_data)
print(f"   ✅ Total Repos: {total_repos}")

# 2. Commits
print("\n📝 Getting commit stats...")
commits_cmd = 'gh api graphql -f query="{ viewer { contributionsCollection { totalCommitContributions restrictedContributionsCount } } }"'
commits_result = run_cmd(commits_cmd)
commits_data = json.loads(commits_result)
public_commits = commits_data['data']['viewer']['contributionsCollection']['totalCommitContributions']
private_commits = commits_data['data']['viewer']['contributionsCollection']['restrictedContributionsCount']
total_commits_year = public_commits + private_commits
estimated_total = total_commits_year * 3

print(f"   ✅ This Year: {total_commits_year}")
print(f"   ✅ Estimated Total: {estimated_total:,}+")

# 3. Lines of code
print("\n📊 Calculating lines of code...")
total_bytes = 0
for repo in repos_data:
    try:
        langs = run_cmd(f"gh api repos/{repo['nameWithOwner']}/languages")
        if langs:
            langs_data = json.loads(langs)
            for size in langs_data.values():
                total_bytes += size
    except:
        pass

total_lines = total_bytes // 40
if total_lines >= 1000000:
    formatted_lines = f"{total_lines / 1000000:.1f}M"
else:
    formatted_lines = f"{total_lines // 1000}K"

print(f"   ✅ Total Lines: {total_lines:,} ({formatted_lines}+)")

# 4. User stats
print("\n👤 Getting profile stats...")
user = run_cmd('gh api user --jq "{followers: .followers, public_repos: .public_repos}"')
user_data = json.loads(user)

print(f"\n{'='*60}")
print(f"🎯 FINAL STATISTICS:")
print(f"   📦 Total Repos: {total_repos}")
print(f"   📝 Total Commits (Estimated): {estimated_total:,}+")
print(f"   📊 Lines of Code: {total_lines:,} ({formatted_lines}+)")
print(f"   👥 Followers: {user_data['followers']}")
print(f"   📂 Public Repos: {user_data['public_repos']}")
print(f"{'='*60}")

print(f"\n📝 README Badge Values:")
print(f"   Total_Repos-{total_repos}")
print(f"   Total_Commits-{estimated_total:,}%2B")
print(f"   Lines_of_Code-{formatted_lines}%2B")

# Save to file
results = {
    "total_repos": total_repos,
    "commits_estimate": estimated_total,
    "lines_of_code": total_lines,
    "formatted_lines": formatted_lines,
    "followers": user_data['followers'],
    "public_repos": user_data['public_repos']
}

with open('github_stats.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Stats saved to github_stats.json")
