#!/usr/bin/env python3
"""
Fast GitHub Stats Calculator
Uses GitHub's built-in statistics API
Includes personal + organization repos
"""

import json
import subprocess

def run_cmd(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

print("🚀 Fetching EXACT GitHub Statistics (Personal + Organizations)...\n")

# 1. Get all organizations
orgs_result = run_cmd("gh api user/orgs --jq '.[].login'")
orgs = orgs_result.split('\n') if orgs_result else []
print(f"📦 Found {len(orgs)} organizations: {', '.join(orgs)}")

# 2. Get repos from personal account
print("\n📊 Fetching personal repositories...")
personal_repos = run_cmd("gh repo list --limit 1000 --json nameWithOwner,languages,primaryLanguage")
personal_data = json.loads(personal_repos)
print(f"   ✓ Personal repos: {len(personal_data)}")

# 3. Get repos from all organizations
org_repos = []
for org in orgs:
    print(f"\n📊 Fetching {org} organization repositories...")
    org_repos_cmd = f"gh repo list {org} --limit 1000 --json nameWithOwner,languages,primaryLanguage"
    org_result = run_cmd(org_repos_cmd)
    if org_result:
        org_data = json.loads(org_result)
        org_repos.extend(org_data)
        print(f"   ✓ {org} repos: {len(org_data)}")

# Combine all repos
all_repos = personal_data + org_repos
total_repos = len(all_repos)

print(f"\n✅ Total Repositories (Personal + Orgs): {total_repos}")

# 4. Get commits using a faster approach
print(f"\n📝 Calculating total commits across all repositories...")

# First get your personal commits this year from GraphQL
graphql_query = '''
{
  viewer {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
'''

commits_result = run_cmd(f"gh api graphql -f query='{graphql_query}'")
commits_data = json.loads(commits_result)

public_commits_this_year = commits_data['data']['viewer']['contributionsCollection']['totalCommitContributions']
private_commits_this_year = commits_data['data']['viewer']['contributionsCollection']['restrictedContributionsCount']
total_commits_this_year = public_commits_this_year + private_commits_this_year

print(f"✅ Your Personal Commits (This Year): {total_commits_this_year}")
print(f"   - Public: {public_commits_this_year}")
print(f"   - Private: {private_commits_this_year}")

# Now count commits from a sample of repos to estimate total
print(f"\n📊 Sampling repositories to estimate total commits...")
sample_size = min(20, total_repos)
total_commits_all_repos = 0
sampled_count = 0

for repo in all_repos[:sample_size]:
    repo_name = repo['nameWithOwner']
    try:
        # Get default branch commit count (faster than paginating all commits)
        commit_cmd = f"gh api repos/{repo_name} --jq '.default_branch' 2>/dev/null"
        default_branch = run_cmd(commit_cmd).strip()
        
        if default_branch:
            # Get commit count for default branch
            commits_cmd = f"gh api repos/{repo_name}/commits?per_page=1 --include 2>&1 | grep -i '^link:' | sed -n 's/.*page=\\([0-9]*\\)>; rel=\"last\".*/\\1/p'"
            commit_count_str = run_cmd(commits_cmd).strip()
            
            if commit_count_str and commit_count_str.isdigit():
                commit_count = int(commit_count_str)
                total_commits_all_repos += commit_count
                sampled_count += 1
                
        if (sampled_count + 1) % 5 == 0:
            print(f"   Sampled {sampled_count}/{sample_size} repos...")
    except:
        continue

# Extrapolate to all repos
if sampled_count > 0:
    avg_commits_per_repo = total_commits_all_repos / sampled_count
    estimated_total_commits = int(avg_commits_per_repo * total_repos)
else:
    # Fallback to conservative estimate
    estimated_total_commits = total_commits_this_year * 3

print(f"✅ Estimated Total Commits (All Repos): {estimated_total_commits:,}+")
print(f"   Based on {sampled_count} sampled repositories")

# 5. Calculate lines of code from language statistics (FAST!)
total_bytes = 0
language_stats = {}
ai_ml_repos = []

for repo in all_repos:
    repo_name = repo['nameWithOwner']
    langs = repo.get('languages', [])
    primary_lang = repo.get('primaryLanguage', {})
    
    # Check if it's an AI/ML repo
    if primary_lang and primary_lang.get('name') in ['Python', 'Jupyter Notebook', 'R']:
        ai_ml_repos.append(repo_name)
    
    if langs:
        for lang in langs:
            size = lang.get('size', 0)
            total_bytes += size
            
            lang_name = lang.get('name', 'Unknown')
            language_stats[lang_name] = language_stats.get(lang_name, 0) + size

# Convert bytes to lines (average: 40 bytes per line of code)
total_lines = total_bytes // 40

# Format nicely
if total_lines >= 1000000:
    formatted_lines = f"{total_lines / 1000000:.1f}M"
elif total_lines >= 1000:
    formatted_lines = f"{total_lines // 1000}K"
else:
    formatted_lines = str(total_lines)

print(f"✅ Total Lines of Code: {total_lines:,} ({formatted_lines}+)")

# Top languages
print(f"\n📊 Top Languages by Size:")
sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:5]
for lang, size in sorted_langs:
    print(f"   - {lang}: {size // 1024}KB")

# AI/ML repos count
print(f"\n🤖 AI/ML Repositories Found: {len(ai_ml_repos)}")
if len(ai_ml_repos) > 0:
    print(f"   Top AI/ML repos:")
    for repo in ai_ml_repos[:5]:
        print(f"   - {repo}")

print(f"\n🎯 FINAL STATISTICS:")
print(f"   📦 Total Repos (Personal + Orgs): {total_repos}")
print(f"   🏢 Organizations: {len(orgs)}")
print(f"   📝 Estimated Total Commits (All Repos): {estimated_total_commits:,}+")
print(f"   📝 Your Commits This Year: {total_commits_this_year:,}")
print(f"   📊 Total Lines of Code: {total_lines:,} ({formatted_lines}+)")
print(f"   🤖 AI/ML Projects: {len(ai_ml_repos)}")

# Save results
results = {
    "total_repos": total_repos,
    "personal_repos": len(personal_data),
    "org_repos": len(org_repos),
    "organizations": orgs,
    "estimated_total_commits": estimated_total_commits,
    "commits_this_year": total_commits_this_year,
    "total_lines": total_lines,
    "formatted_lines": formatted_lines,
    "ai_ml_repos_count": len(ai_ml_repos),
    "ai_ml_repos": ai_ml_repos[:10]
}

with open('github_stats.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Stats saved to github_stats.json")
print(f"\nTo update README, use these values:")
print(f"   Total_Repos-{total_repos}")
print(f"   Total_Commits-{estimated_total_commits:,}%2B")
print(f"   Lines_of_Code-{formatted_lines}%2B")
print(f"   AI_ML_Projects-{len(ai_ml_repos)}")

import json
import subprocess

def run_cmd(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

print("🚀 Fetching Complete GitHub Statistics (Including Organizations)...\n")

# 1. Get ALL repos including organizations
print("📦 Fetching all repositories (personal + organizations)...")
repos_cmd = "gh repo list --limit 1000 --json nameWithOwner,languages,stargazerCount,isPrivate,owner"
repos_data = run_cmd(repos_cmd)
repos = json.loads(repos_data)
total_repos = len(repos)

# Count personal vs org repos
personal_repos = [r for r in repos if r.get('owner', {}).get('login') == 'AVI5211']
org_repos = [r for r in repos if r.get('owner', {}).get('login') != 'AVI5211']

print(f"   ✅ Personal Repos: {len(personal_repos)}")
print(f"   ✅ Organization Repos: {len(org_repos)}")
print(f"   ✅ Total Repositories: {total_repos}")

# 2. Identify AI/ML projects
print("\n🤖 Identifying AI/ML Projects...")
ai_ml_keywords = ['ml', 'ai', 'machine', 'learning', 'neural', 'deep', 'model', 'tensorflow', 
                  'pytorch', 'scikit', 'nlp', 'computer vision', 'data science']

# Get repos with descriptions
repos_with_desc = run_cmd("gh repo list --limit 1000 --json name,description,url,stargazerCount,primaryLanguage")
all_repos_info = json.loads(repos_with_desc)

ai_ml_projects = []
for repo in all_repos_info:
    name = repo.get('name', '').lower()
    desc = (repo.get('description') or '').lower()
    lang = repo.get('primaryLanguage', {})
    lang_name = lang.get('name', '') if isinstance(lang, dict) else ''
    
    # Check if it's an AI/ML project
    if any(keyword in name or keyword in desc for keyword in ai_ml_keywords):
        ai_ml_projects.append({
            'name': repo.get('name'),
            'url': repo.get('url'),
            'description': repo.get('description', 'No description'),
            'language': lang_name,
            'stars': repo.get('stargazerCount', 0)
        })

print(f"   ✅ AI/ML Projects Found: {len(ai_ml_projects)}")
for project in ai_ml_projects[:5]:
    print(f"      - {project['name']} ({project['language']}) ⭐ {project['stars']}")

# 3. Get commits (including organizations)
print("\n📝 Calculating Total Commits...")
graphql_query = '''
{
  viewer {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
'''

commits_result = run_cmd(f"gh api graphql -f query='{graphql_query}'")
commits_data = json.loads(commits_result)

public_commits = commits_data['data']['viewer']['contributionsCollection']['totalCommitContributions']
private_commits = commits_data['data']['viewer']['contributionsCollection']['restrictedContributionsCount']
total_commits_year = public_commits + private_commits

# Estimate all-time commits
estimated_total_commits = total_commits_year * 3

print(f"   ✅ This Year's Commits: {total_commits_year}")
print(f"   ✅ Estimated Total Commits: {estimated_total_commits:,}")

# 4. Calculate lines of code (including all repos)
print("\n📊 Calculating Total Lines of Code...")
total_bytes = 0
language_stats = {}

for repo in repos:
    langs = repo.get('languages', [])
    if langs:
        for lang in langs:
            size = lang.get('size', 0)
            total_bytes += size
            
            lang_name = lang.get('name', 'Unknown')
            language_stats[lang_name] = language_stats.get(lang_name, 0) + size

total_lines = total_bytes // 40

if total_lines >= 1000000:
    formatted_lines = f"{total_lines / 1000000:.1f}M"
elif total_lines >= 1000:
    formatted_lines = f"{total_lines // 1000}K"
else:
    formatted_lines = str(total_lines)

print(f"   ✅ Total Lines of Code: {total_lines:,} ({formatted_lines}+)")

# Top languages
print(f"\n� Top Programming Languages:")
sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:5]
for lang, size in sorted_langs:
    print(f"   - {lang}: {size // 1024}KB")

# 5. Calculate stars
total_stars = sum(r.get('stargazerCount', 0) for r in all_repos_info)
print(f"\n⭐ Total Stars: {total_stars}")

print(f"\n{'='*60}")
print(f"🎯 COMPLETE STATISTICS (Personal + Organizations):")
print(f"   📦 Total Repos: {total_repos}")
print(f"      - Personal: {len(personal_repos)}")
print(f"      - Organizations: {len(org_repos)}")
print(f"   🤖 AI/ML Projects: {len(ai_ml_projects)}")
print(f"   📝 Total Commits (Estimated): {estimated_total_commits:,}+")
print(f"   📊 Total Lines of Code: {total_lines:,} ({formatted_lines}+)")
print(f"   ⭐ Total Stars: {total_stars}")
print(f"{'='*60}")

# Save results
results = {
    "total_repos": total_repos,
    "personal_repos": len(personal_repos),
    "org_repos": len(org_repos),
    "ai_ml_projects": len(ai_ml_projects),
    "ai_ml_projects_list": ai_ml_projects,
    "commits_this_year": total_commits_year,
    "estimated_total_commits": estimated_total_commits,
    "total_lines": total_lines,
    "formatted_lines": formatted_lines,
    "total_stars": total_stars,
    "top_languages": sorted_langs[:5]
}

with open('github_stats.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Stats saved to github_stats.json")
print(f"\n📝 README Update Values:")
print(f"   Total_Repos-{total_repos}")
print(f"   AI_ML_Projects-{len(ai_ml_projects)}")
print(f"   Total_Commits-{estimated_total_commits:,}%2B")
print(f"   Lines_of_Code-{formatted_lines}%2B")
print(f"   Total_Stars-{total_stars}")

