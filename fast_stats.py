#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast GitHub Stats Calculator - Complete Profile Statistics
Includes: personal repos, private repos, AI/ML projects, commits, LOC, stars
"""

import json
import subprocess
import sys
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

# 3. Get commits
print("\n📝 Getting commit stats...")
graphql_query = '{ viewer { contributionsCollection { totalCommitContributions restrictedContributionsCount } } }'
commits_result = run_cmd(f'gh api graphql -f query="{graphql_query}"')

if commits_result:
    try:
        commits_data = json.loads(commits_result)
        if 'data' in commits_data:
            public_commits = commits_data['data']['viewer']['contributionsCollection']['totalCommitContributions']
            private_commits = commits_data['data']['viewer']['contributionsCollection']['restrictedContributionsCount']
            total_commits_year = public_commits + private_commits
            estimated_total = total_commits_year * 3
        else:
            total_commits_year = 0
            estimated_total = 0
    except:
        total_commits_year = 0
        estimated_total = 0
else:
    total_commits_year = 0
    estimated_total = 0

print(f"   ✅ This Year: {total_commits_year}")
print(f"   ✅ Estimated Total: {estimated_total:,}+")

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

if total_lines >= 1000000:
    formatted_lines = f"{total_lines / 1000000:.1f}M"
elif total_lines >= 1000:
    formatted_lines = f"{total_lines // 1000}K"
else:
    formatted_lines = str(total_lines)

print(f"   ✅ Total Lines of Code: {total_lines:,} ({formatted_lines}+)")
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
print(f"   📝 Total Commits (Est): {estimated_total:,}+")
print(f"   📊 Total Lines of Code: {total_lines:,} ({formatted_lines}+)")
print(f"   ⭐ Total Stars: {total_stars}")
print(f"{'='*60}")

# Save results
results = {
    "total_repos": total_repos,
    "public_repos": public_repos,
    "private_repos": private_repos,
    "ai_ml_projects": len(ai_ml_projects),
    "ai_ml_projects_list": ai_ml_projects[:10],
    "commits_this_year": total_commits_year,
    "estimated_total_commits": estimated_total,
    "total_lines": total_lines,
    "formatted_lines": formatted_lines,
    "total_stars": total_stars,
    "top_languages": [{"lang": lang, "size": size} for lang, size in sorted_langs[:5]]
}

with open('github_stats.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Stats saved to github_stats.json")
print(f"\n📝 README Update Values:")
print(f"   Total_Repos: {total_repos}")
print(f"   AI_ML_Projects: {len(ai_ml_projects)}")
print(f"   Total_Commits: {estimated_total:,}+")
print(f"   Lines_of_Code: {formatted_lines}+")
print(f"   Total_Stars: {total_stars}")

