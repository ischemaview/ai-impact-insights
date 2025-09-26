# GitHub Token Permissions Guide

## For Copilot Usage Metrics API Access

### Fine-Grained Personal Access Token (Preferred)

**Organization Permissions** (choose one):
- ✅ **"GitHub Copilot Business"**: `Read` 
- ✅ **"Administration"**: `Read`

**Repository Permissions** (for each repo you want to analyze):
- ✅ **Contents**: `Read`
- ✅ **Metadata**: `Read`
- ✅ **Pull requests**: `Read` (optional)

### Classic Personal Access Token

**Required Scopes**:
- ✅ `read:org` - Read organization data
- ✅ `repo` - Repository access (for commit data)

**Note**: Classic tokens rely on organization-level permissions rather than specific Copilot scopes.

## Important Notes

### Organization Admin Approval
Fine-grained tokens with organization permissions typically require approval from your organization administrators. The request will be pending until approved.

### Fallback Strategy
If you can't get Copilot API permissions:
1. Use `productivity_analyzer_fine_grained.py` (works with basic repository permissions)
2. Still provides excellent before/after productivity analysis
3. Uses commit message analysis to detect AI assistance patterns

### Testing Your Token
Always test your token first:
```bash
python scripts/test_copilot_api.py
```

This will show you exactly which APIs you can access with your current token.

## Permission Hierarchy

| Permission Level | What You Can Access | Script to Use |
|-----------------|-------------------|---------------|
| **Copilot Business/Admin** | Full Copilot Usage API + Commit Analysis | `copilot_before_after_analyzer.py` |
| **Repository Only** | Commit Analysis + AI Pattern Detection | `productivity_analyzer_fine_grained.py` |
| **No Access** | Run analysis on public repositories only | Limited functionality |

## Troubleshooting

### "Request requires organization admin approval"
- Your fine-grained token request is pending
- Ask your GitHub org admin to approve the token
- Or use a classic token as temporary workaround

### "403 Forbidden" on Copilot API
- Token lacks "GitHub Copilot Business" or "Administration" permissions
- Organization may not have Copilot Business subscription
- User may not have sufficient org-level permissions

### "404 Not Found" on Copilot API  
- Organization doesn't have GitHub Copilot enabled
- API endpoint may not be available for your plan
- Check if organization has Copilot Business/Enterprise