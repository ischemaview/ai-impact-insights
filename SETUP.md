# Setup Instructions for GitHub Copilot Analysis

## Quick Start

1. **Copy and configure the config file:**
   ```bash
   cp config.json.example config.json
   ```

2. **Edit `config.json` with your details:**
   - Add your GitHub token
   - Set your organization name
   - List repositories to analyze
   - Set your Copilot adoption date

3. **Run the analysis:**
   ```bash
   python scripts/copilot_before_after_analyzer.py
   ```

## Configuration Details

### Required Settings in `config.json`:

```json
{
  "github": {
    "token": "ghp_YOUR_ACTUAL_TOKEN_HERE",
    "organization": "your-company",
    "repositories": ["repo1", "repo2", "repo3"]
  },
  "analysis": {
    "copilot_adoption_date": "2024-01-15",
    "before_period_weeks": 8,
    "after_period_weeks": 8,
    "min_commits_for_analysis": 5
  }
}
```

### How to Get Your GitHub Token:

#### Option 1: Fine-Grained Personal Access Token (Recommended)
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Generate new token with these permissions:
   
   **Repository permissions** (for each repo in your analysis):
   - Contents: `Read`
   - Metadata: `Read`
   - Pull requests: `Read` (optional, for future enhancements)
   
   **Organization permissions** (⚠️ **May require org admin approval**):
   - **"GitHub Copilot Business": `Read`** OR
   - **"Administration": `Read`**
   
   **Note**: You need at least one of the Copilot Business or Administration permissions to access Copilot Usage API.

#### Option 2: Classic Token (For Copilot API access)
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with these scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read organization data)
   - `copilot` (Access Copilot usage data) - **⚠️ This scope may not exist yet**

**To test if your classic token works with Copilot API:**
```bash
python scripts/test_copilot_api.py
```

This will tell you exactly what Copilot APIs you can access.

### Setting the Copilot Adoption Date:

This should be when your team/organization first started using Copilot. The script will compare:
- **Before**: 8 weeks before this date
- **After**: 8 weeks after this date

## What the Analysis Will Show:

### Individual Developer Comparison:
```
john-doe: 12.3 → 16.7 commits/week (+35.8%)
jane-smith: 8.1 → 11.2 commits/week (+38.3%)
```

### Team Summary:
```
Commits per week: Average improvement +25.4%
Users improved: 12/15 (80%)
Lines of code per week: Average improvement +18.2%
```

## Example Output:

```
COPILOT BEFORE/AFTER ANALYSIS SUMMARY
====================================
Organization: your-company
Copilot Adoption: 2024-01-15
Analysis Period: 8 weeks before/after

Users Analyzed: 15 (min 5 commits)

PRODUCTIVITY IMPROVEMENTS:
Commits Per Week: Average improvement: +25.4%
Users improved: 12/15 (80%)
```

## Troubleshooting:

### "Config file not found"
- Make sure you copied `config.json.example` to `config.json`

### "Error 401: Bad credentials"  
- Check your GitHub token is correct and has the right permissions

### "Error 403: API rate limit"
- GitHub has rate limits. Try reducing the number of repositories or analysis period

### "No qualified users found"
- Reduce `min_commits_for_analysis` in config
- Check if your adoption date is correct
- Verify repositories have sufficient activity

## Advanced Usage:

```bash
# Use custom config file
python scripts/copilot_before_after_analyzer.py --config my-config.json

# Save to specific output file  
python scripts/copilot_before_after_analyzer.py --output results.json
```

## Requirements:

```bash
pip install requests pandas
```