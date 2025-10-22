# GitHub Profile Auto-Updater 🚀

This repository automatically updates your GitHub profile stats including:
- ✅ All 86 repositories (public + private)
- ✅ Real-time commit counts
- ✅ Top programming languages
- ✅ Featured repositories
- ✅ Follower/Following stats

## 🔧 Setup Complete!

### What's Been Set Up:

1. **`update_github_stats.py`** - Python script that fetches and updates your GitHub stats
2. **`.github/workflows/update-stats.yml`** - GitHub Actions workflow for automatic daily updates

### 📊 Current Stats:
- **Total Repos**: 86 (45 public, 41 private)
- **Top Language**: Python (20 repos)
- **Followers**: 15

## 🎯 How to Use:

### Manual Update:
```bash
# Run the update script anytime
python3 update_github_stats.py
```

### Automatic Updates:
The GitHub Actions workflow will automatically:
- Run daily at midnight UTC
- Update your README with latest stats
- Commit and push changes automatically

### First Time Setup for GitHub Actions:
1. Push these files to your repository:
   ```bash
   git add .
   git commit -m "✨ Add auto-update GitHub stats"
   git push origin main
   ```

2. Go to your repository → **Settings** → **Actions** → **General**
3. Scroll to "Workflow permissions"
4. Select "Read and write permissions"
5. Click "Save"

## 🎨 Customization:

### Update Frequency:
Edit `.github/workflows/update-stats.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Run every 6 hours
  - cron: '0 0 * * *'    # Run daily at midnight
  - cron: '0 */12 * * *' # Run every 12 hours
```

### Number of Featured Repos:
Edit `update_github_stats.py` line 52:
```python
cmd = "gh repo list --limit 1000 --json name,stargazerCount,primaryLanguage,description,url | jq 'sort_by(-.stargazerCount) | .[0:10]'"  # Change 5 to 10
```

## 📁 Files Structure:
```
AVI5211/
├── README.md                          # Your awesome profile
├── update_github_stats.py            # Stats updater script
└── .github/
    └── workflows/
        └── update-stats.yml          # Auto-update workflow
```

## 🔍 Troubleshooting:

### Script fails locally:
```bash
# Make sure you're authenticated
gh auth login

# Check authentication status
gh auth status
```

### Workflow fails in GitHub Actions:
- Ensure workflow permissions are set to "Read and write"
- Check Actions tab for detailed error logs

## 🎉 That's It!

Your profile now shows **ALL 86 repos** including private ones, and updates automatically! 

---

**Made with ❤️ by Aviraj Kawade**
