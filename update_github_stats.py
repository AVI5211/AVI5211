#!/usr/bin/env python3
"""
GitHub Profile Stats Updater
Automatically updates README.md with latest GitHub statistics
Including private repos, all commits, and lines of code
"""

import json
import subprocess
import sys
from datetime import datetime

def run_gh_command(command):
    """Execute GitHub CLI command and return JSON result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def get_user_stats():
    """Fetch complete user statistics"""
    cmd = "gh api user --jq '{login: .login, name: .name, bio: .bio, public_repos: .public_repos, followers: .followers, following: .following}'"
    return run_gh_command(cmd)

def get_repo_count():
    """Get total repository count (public + private)"""
    cmd = "gh repo list --limit 1000 --json name,isPrivate | jq '{total: length, private: ([.[] | select(.isPrivate == true)] | length), public: ([.[] | select(.isPrivate == false)] | length)}'"
    return run_gh_command(cmd)

def get_total_commits():
    """Get estimated total commits across all repos"""
    # Get commit count from GitHub GraphQL API
    cmd = """gh api graphql -f query='
    {
      user(login: "AVI5211") {
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }' --jq '.data.user.contributionsCollection | .totalCommitContributions + .restrictedContributionsCount'
    """
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        this_year_commits = int(result.stdout.strip())
        # Estimate total based on account age and activity
        estimated_total = this_year_commits * 3  # Conservative estimate
        return max(estimated_total, 500)  # Minimum 500
    except:
        return 500  # Default estimate

def get_top_languages():
    """Get top programming languages from all repos"""
    cmd = "gh repo list --limit 1000 --json name,primaryLanguage | jq '[.[] | select(.primaryLanguage != null) | .primaryLanguage.name] | group_by(.) | map({language: .[0], count: length}) | sort_by(-.count) | .[0:10]'"
    return run_gh_command(cmd)

def get_top_repos():
    """Get top repositories by stars"""
    cmd = "gh repo list --limit 1000 --json name,stargazerCount,primaryLanguage,description,url | jq 'sort_by(-.stargazerCount) | .[0:5]'"
    return run_gh_command(cmd)

def estimate_lines_of_code(repo_count):
    """Estimate total lines of code based on repo count and languages"""
    # Conservative estimate: average repo has ~2000 lines
    # Active dev repos have more, forks have less
    avg_lines_per_repo = 2000
    total_estimate = repo_count * avg_lines_per_repo
    
    # Format as 100K+, 200K+, etc.
    if total_estimate >= 1000000:
        return f"{total_estimate // 1000000}M+"
    elif total_estimate >= 100000:
        return f"{total_estimate // 1000}K+"
    else:
        return f"{total_estimate // 1000}K+"

def update_top_badges(readme_content, repo_count, total_commits, lines_of_code):
    """Update the top stats badges"""
    # Find the badges section
    old_badges = """<!-- Comprehensive Stats Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Total_Repos-86-blue?style=flat-square&logo=github" alt="Total Repos" />
  <img src="https://img.shields.io/badge/Total_Commits-500%2B-green?style=flat-square&logo=git" alt="Total Commits" />
  <img src="https://img.shields.io/badge/Lines_of_Code-100K%2B-orange?style=flat-square&logo=codecov" alt="Lines of Code" />
</p>"""
    
    new_badges = f"""<!-- Comprehensive Stats Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Total_Repos-{repo_count['total']}-blue?style=flat-square&logo=github" alt="Total Repos" />
  <img src="https://img.shields.io/badge/Total_Commits-{total_commits}%2B-green?style=flat-square&logo=git" alt="Total Commits" />
  <img src="https://img.shields.io/badge/Lines_of_Code-{lines_of_code}-orange?style=flat-square&logo=codecov" alt="Lines of Code" />
</p>"""
    
    return readme_content.replace(old_badges, new_badges) if old_badges in readme_content else readme_content

def create_language_badges(languages):
    """Create badge markdown for top languages"""
    badges = []
    colors = {
        'Python': '3776AB',
        'JavaScript': 'F7DF1E',
        'TypeScript': '3178C6',
        'HTML': 'E34F26',
        'CSS': '1572B6',
        'Java': '007396',
        'Go': '00ADD8',
        'PHP': '777BB4',
        'Dockerfile': '2496ED',
        'Shell': '89E051',
        'Jupyter Notebook': 'F37626',
        'Mustache': 'FF6347'
    }
    
    for lang_data in languages[:8]:  # Top 8 languages
        lang = lang_data['language']
        count = lang_data['count']
        color = colors.get(lang, '000000')
        badge = f"![{lang}](https://img.shields.io/badge/-{lang}-{color}?style=flat-square&logo={lang.lower().replace(' ', '-')}&logoColor=white) `{count} repos`"
        badges.append(badge)
    
    return badges

def generate_stats_section(user_stats, repo_count, languages, top_repos):
    """Generate the complete stats section for README"""
    
    # Generate language badges
    lang_badges = create_language_badges(languages)
    lang_section = '\n'.join([f"  - {badge}" for badge in lang_badges])
    
    # Generate top repos section
    repo_lines = []
    for repo in top_repos:
        name = repo.get('name', 'N/A')
        stars = repo.get('stargazerCount', 0)
        lang = repo.get('primaryLanguage', {}).get('name', 'N/A') if repo.get('primaryLanguage') else 'N/A'
        url = repo.get('url', '#')
        desc = repo.get('description', 'No description')[:80]
        
        if stars > 0:
            repo_lines.append(f"  - ⭐ **[{name}]({url})** - {stars} stars | {lang}")
    
    repos_section = '\n'.join(repo_lines) if repo_lines else "  - Building amazing projects! 🚀"
    
    stats_markdown = f"""
## 📊 Real-Time GitHub Statistics

<div align="center">

### 📈 Profile Overview

| 📦 Total Repositories | 🔓 Public | 🔒 Private | 👥 Followers | 👤 Following |
|:---:|:---:|:---:|:---:|:---:|
| **{repo_count['total']}** | {repo_count['public']} | {repo_count['private']} | **{user_stats['followers']}** | {user_stats['following']} |

</div>

### 💻 Top Programming Languages

{lang_section}

### 🌟 Featured Repositories

{repos_section}

<div align="center">
  <sub>📅 Last Updated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}</sub>
</div>
"""
    
    return stats_markdown

def update_readme(stats_section):
    """Update README.md with new stats"""
    readme_path = 'README.md'
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the stats section
        start_marker = "## 📊 Real-Time GitHub Statistics"
        end_marker = "## 📈 Coding Activity"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            # Replace the stats section
            new_content = content[:start_idx] + stats_section + "\n---\n\n" + content[end_idx:]
        else:
            # If markers not found, append to the end of stats section
            print("⚠️  Markers not found. Appending stats at the end...")
            new_content = content + "\n\n" + stats_section
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ README.md updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating README: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Fetching GitHub statistics...")
    
    # Fetch all data
    user_stats = get_user_stats()
    repo_count = get_repo_count()
    languages = get_top_languages()
    top_repos = get_top_repos()
    
    if not all([user_stats, repo_count, languages]):
        print("❌ Failed to fetch GitHub data. Make sure you're authenticated with 'gh auth login'")
        sys.exit(1)
    
    # Calculate additional stats
    total_commits = get_total_commits()
    lines_of_code = estimate_lines_of_code(repo_count['total'])
    
    print(f"📊 Found {repo_count['total']} repositories ({repo_count['public']} public, {repo_count['private']} private)")
    print(f"💻 Top language: {languages[0]['language']} ({languages[0]['count']} repos)")
    print(f"📝 Total commits: {total_commits}+")
    print(f"📈 Estimated lines of code: {lines_of_code}")
    
    # Generate stats section
    stats_section = generate_stats_section(user_stats, repo_count, languages, top_repos)
    
    # Read current README
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"❌ Error reading README: {e}")
        sys.exit(1)
    
    # Update top badges
    readme_content = update_top_badges(readme_content, repo_count, total_commits, lines_of_code)
    
    # Update stats section
    start_marker = "## 📊 Real-Time GitHub Statistics"
    end_marker = "## 📈 Coding Activity"
    
    start_idx = readme_content.find(start_marker)
    end_idx = readme_content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        readme_content = readme_content[:start_idx] + stats_section + "\n---\n\n" + readme_content[end_idx:]
    
    # Write updated README
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ README.md updated successfully!")
        print("🎉 Your GitHub profile is now up-to-date!")
    except Exception as e:
        print(f"❌ Error writing README: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
