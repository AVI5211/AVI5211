#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast GitHub Stats Calculator - Complete Profile Statistics
Includes: personal repos, private repos, AI/ML projects, commits, LOC, stars
Also updates README.md with the latest statistics
"""

import json
import subprocess
import sys
import re
import io

# Fix encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return result.stdout.strip()
    except:
        return None

print("🚀 Fetching Complete GitHub Statistics...\n")

# 1. Get all repositories (personal + organizations)
print("📦 Fetching all repositories...")

# Get personal repos
personal_cmd = "gh repo list --limit 1000 --json name,description,url,stargazerCount,primaryLanguage,isPrivate,owner"
personal_result = run_cmd(personal_cmd)

if personal_result:
    repos = json.loads(personal_result)
else:
    repos = []

# Fetch organizations
print("   📋 Fetching organizations...")
org_cmd = "gh api user/orgs"
org_result = run_cmd(org_cmd)
orgs_list = []
org_repos = []

if org_result:
    try:
        orgs_data = json.loads(org_result)
        orgs_list = [org.get('login') for org in orgs_data if org.get('login')]
        print(f"   ✅ Found {len(orgs_list)} organizations: {', '.join(orgs_list)}")
        
        # Fetch repos from each organization
        for org in orgs_list:
            org_repos_cmd = f"gh repo list {org} --limit 1000 --json name,description,url,stargazerCount,primaryLanguage,isPrivate,owner"
            org_repos_result = run_cmd(org_repos_cmd)
            if org_repos_result:
                try:
                    org_data = json.loads(org_repos_result)
                    org_repos.extend(org_data)
                    print(f"      - {org}: {len(org_data)} repos")
                except:
                    pass
    except:
        print("   ⚠️  Could not parse organizations")

# Combine all repos
repos.extend(org_repos)

total_repos = len(repos)
public_repos = sum(1 for r in repos if not r.get('isPrivate', False))
private_repos = total_repos - public_repos
personal_count = len([r for r in repos if r.get('owner', {}).get('login') == 'AVI5211'])
org_count = len(org_repos)

print(f"   ✅ Total Repos: {total_repos}")
print(f"      - Personal: {personal_count}")
print(f"      - Organizations: {org_count}")
print(f"      - Public: {public_repos}")
print(f"      - Private: {private_repos}")

# 2. Identify AI/ML projects
print("\n🤖 Identifying AI/ML Projects...")
ai_ml_keywords = ['ml', 'ai', 'machine', 'learning', 'neural', 'deep', 'model', 'tensorflow', 
                  'pytorch', 'scikit', 'nlp', 'llm', 'agent', 'data science', 'langchain', 'rag']

ai_ml_projects = []
for repo in repos:
    name = repo.get('name', '').lower()
    desc = (repo.get('description') or '').lower()
    lang = repo.get('primaryLanguage', {})
    lang_name = lang.get('name', '') if isinstance(lang, dict) else ''
    
    # Check if it's an AI/ML project
    if any(keyword in name or keyword in desc for keyword in ai_ml_keywords):
        ai_ml_projects.append({
            'name': repo.get('name'),
            'url': repo.get('url'),
            'language': lang_name,
            'stars': repo.get('stargazerCount', 0)
        })

print(f"   ✅ AI/ML Projects: {len(ai_ml_projects)}")
if ai_ml_projects:
    for project in ai_ml_projects[:5]:
        print(f"      - {project['name']} ({project['language']}) ⭐ {project['stars']}")

# 3. Get commits (including organization repos)
print("\n📝 Getting commit stats...")

# First get viewer's general contribution stats
graphql_query = '{ viewer { contributionsCollection { totalCommitContributions restrictedContributionsCount } } }'
commits_result = run_cmd(f'gh api graphql -f query="{graphql_query}"')

viewer_public_commits = 0
viewer_private_commits = 0

if commits_result:
    try:
        commits_data = json.loads(commits_result)
        if 'data' in commits_data:
            viewer_public_commits = commits_data['data']['viewer']['contributionsCollection']['totalCommitContributions']
            viewer_private_commits = commits_data['data']['viewer']['contributionsCollection']['restrictedContributionsCount']
    except:
        pass

viewer_total = viewer_public_commits + viewer_private_commits
print(f"   ✅ Your Personal Commits (This Year): {viewer_total}")
print(f"      - Public: {viewer_public_commits}")
print(f"      - Private: {viewer_private_commits}")

# Estimate total commits across all repos using repo size as proxy
print(f"\n📊 Estimating total commits from all repos...")
total_size = 0
repo_count_with_size = 0

for repo in repos:
    size = repo.get('size', 0)  # Size in KB
    if size > 0:
        total_size += size
        repo_count_with_size += 1

# Average commits per KB: ~1 commit per 20KB (based on typical repo density)
# More conservative estimate
estimated_commits_from_size = (total_size // 50) if total_size > 0 else 0

# Also consider repo count * average activity
# Average repo has ~20 commits
estimated_commits_from_count = len(repos) * 20

# Take average of both methods
estimated_total_commits = max(estimated_commits_from_size, estimated_commits_from_count)

# Add your personal contributions
estimated_total_commits = estimated_total_commits + (viewer_total * 2)  # Multiply personal by 2 for all-time estimate

print(f"   ✅ Estimated Total Commits (Personal + Orgs, All-Time): {estimated_total_commits:,}")
print(f"   (Based on {repo_count_with_size} repos with size data)")

# 4. Calculate lines of code from language API
print("\n📊 Calculating total lines of code...")
total_bytes = 0
language_stats = {}
processed_count = 0

for repo in repos[:50]:  # Sample first 50 repos to speed up
    repo_name = repo.get('name', '')
    try:
        # Fetch languages API for this repo
        langs_cmd = f"gh api repos/AVI5211/{repo_name}/languages"
        langs_result = run_cmd(langs_cmd)
        if langs_result:
            langs_data = json.loads(langs_result)
            for lang_name, size in langs_data.items():
                total_bytes += size
                language_stats[lang_name] = language_stats.get(lang_name, 0) + size
        processed_count += 1
    except:
        pass

# Extrapolate from sample to all repos
if processed_count > 0:
    avg_bytes_per_repo = total_bytes / processed_count
    total_bytes = int(avg_bytes_per_repo * len(repos))

total_lines = total_bytes // 40 if total_bytes > 0 else 0

# Use full numbers with commas (no shorthand)
formatted_lines = f"{total_lines:,}"

print(f"   ✅ Total Lines of Code: {formatted_lines}")
print(f"   (Sampled {processed_count} repos and extrapolated)")

# 5. Calculate stars
total_stars = sum(r.get('stargazerCount', 0) for r in repos)
print(f"\n⭐ Total Stars: {total_stars}")

# 6. Top languages
print(f"\n💻 Top Programming Languages:")
sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:5]
for lang, size in sorted_langs:
    print(f"   - {lang}: {size // 1024}KB")

# Final summary
print(f"\n{'='*60}")
print(f"🎯 COMPLETE STATISTICS:")
print(f"   📦 Total Repos: {total_repos}")
print(f"      - Public: {public_repos}")
print(f"      - Private: {private_repos}")
print(f"   🤖 AI/ML Projects: {len(ai_ml_projects)}")
print(f"   📝 Total Commits (Est): {estimated_total_commits:,}")
print(f"   📊 Total Lines of Code: {formatted_lines}")
print(f"   ⭐ Total Stars: {total_stars}")
print(f"{'='*60}")

# Save results
results = {
    "total_repos": total_repos,
    "public_repos": public_repos,
    "private_repos": private_repos,
    "organizations": len(orgs_list),
    "ai_ml_projects": len(ai_ml_projects),
    "ai_ml_projects_list": ai_ml_projects[:10],
    "commits_this_year": viewer_public_commits + viewer_private_commits,
    "estimated_total_commits": estimated_total_commits,
    "total_lines": total_lines,
    "formatted_lines": formatted_lines,
    "total_stars": total_stars,
    "top_languages": [{"lang": lang, "size": size} for lang, size in sorted_langs[:5]]
}

with open('github_stats.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Stats saved to github_stats.json")

# Update README.md with latest statistics
print(f"\n📝 Updating README.md...")
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()
    
    # Update various badge patterns
    readme = re.sub(
        r'Total_Repos-\d+',
        f'Total_Repos-{total_repos}',
        readme
    )
    readme = re.sub(
        r'AI_ML_Projects-\d+',
        f'AI_ML_Projects-{len(ai_ml_projects)}',
        readme
    )
    readme = re.sub(
        r'Total_Commits-[\d,]+(?:%2B)?',
        f'Total_Commits-{estimated_total_commits:,}',
        readme
    )
    readme = re.sub(
        r'Lines_of_Code-[\d,\.KMB]+(?:%2B)?',
        f'Lines_of_Code-{formatted_lines}',
        readme
    )
    readme = re.sub(
        r'Total_Stars-\d+',
        f'Total_Stars-{total_stars}',
        readme
    )
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"   ✅ README.md updated successfully!")
    print(f"\n📊 Updated badges:")
    print(f"      • Total_Repos: {total_repos}")
    print(f"      • AI_ML_Projects: {len(ai_ml_projects)}")
    print(f"      • Total_Commits: {estimated_total_commits:,}")
    print(f"      • Lines_of_Code: {formatted_lines}")
    print(f"      • Total_Stars: {total_stars}")
except Exception as e:
    print(f"   ⚠️  Could not update README: {e}")

print(f"\n🎉 All done!")

