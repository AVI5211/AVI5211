#!/usr/bin/env python3
"""
GitHub Profile Stats Updater
Automatically updates README.md with latest GitHub statistics
Including private repos and all commits
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

def get_top_languages():
    """Get top programming languages from all repos"""
    cmd = "gh repo list --limit 1000 --json name,primaryLanguage | jq '[.[] | select(.primaryLanguage != null) | .primaryLanguage.name] | group_by(.) | map({language: .[0], count: length}) | sort_by(-.count) | .[0:10]'"
    return run_gh_command(cmd)

def get_top_repos():
    """Get top repositories by stars"""
    cmd = "gh repo list --limit 1000 --json name,stargazerCount,primaryLanguage,description,url | jq 'sort_by(-.stargazerCount) | .[0:5]'"
    return run_gh_command(cmd)

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
    
    print(f"📊 Found {repo_count['total']} repositories ({repo_count['public']} public, {repo_count['private']} private)")
    print(f"💻 Top language: {languages[0]['language']} ({languages[0]['count']} repos)")
    
    # Generate stats section
    stats_section = generate_stats_section(user_stats, repo_count, languages, top_repos)
    
    # Update README
    if update_readme(stats_section):
        print("🎉 Your GitHub profile is now up-to-date!")
    else:
        print("⚠️  There was an issue updating the README")
        sys.exit(1)

if __name__ == "__main__":
    main()
