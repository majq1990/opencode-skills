---
name: skill-publisher
version: 1.0.0
description: Push local skills to Skill Distribution Server with security scan
author: majianquan
category: support-dept
visibility: support-dept
---

# Skill Publisher

Push local skills to enterprise Skill Distribution Server with automatic security scanning.

## User Credentials

| Item | Value |
|------|-------|
| Username | majianquan |
| Role | Support Department |
| Server | https://demo.egova.com.cn/skill-api/ |

## Client Location

| Platform | Path |
|----------|------|
| Windows | `D:\opencode\file\2026-04-02\skill-sync\dist\skill-manager.exe` |
| macOS | `D:\opencode\file\2026-04-02\skill-sync\mac\skill-manager.sh` |
| Server Share | `\\demo.egova.com.cn\gc\skill-manager\` |

## Push Workflow

### Method 1: Interactive Menu (Recommended)

```powershell
# Run skill-manager
D:\opencode\file\2026-04-02\skill-sync\dist\skill-manager.exe

# If already logged in:
# Select option 4 [MAINTENANCE] Upload a skill
# Enter skill directory path

# If not logged in:
# Login with username: majianquan
# Then select upload option
```

### Method 2: Direct API Call

```powershell
# Login first (if not authenticated)
$body = @{username='majianquan';password='Egova@1234'} | ConvertTo-Json
$resp = Invoke-RestMethod -Uri 'https://demo.egova.com.cn/skill-api/auth/login' -Method POST -Body $body -ContentType 'application/json'
$token = $resp.token

# Create skill package (zip)
# SKILL.md must be in root with YAML frontmatter

# Upload
$form = @{package = Get-Item -Path "path\to\skill.zip"}
Invoke-RestMethod -Uri 'https://demo.egova.com.cn/skill-api/skills/{skill-name}/upload' -Method POST -Headers @{Authorization="Bearer $token"} -Form $form
```

### Method 3: Skill Package Directory

Prepare skill package structure:
```
skill-name/
├── SKILL.md          # Required: name, version, description in YAML frontmatter
├── prompts/          # Optional: prompt templates
├── tools/            # Optional: tool scripts
└── README.md         # Optional: documentation
```

SKILL.md format:
```markdown
---
name: skill-name
version: 1.0.0
description: Skill description
author: your-name
category: global | support-dept
visibility: global | support-dept
---

# Skill Title

Skill content...
```

## Security Scan

All uploaded skills are automatically scanned by `skill-security-auditor`:
- Exit code 0 = Pass → Published to `/egova/skill/skills/`
- Exit code 1 = Fail → Moved to `/egova/skill/unsafe/`

Scan results are returned in upload response.

## Post-Upload

After successful upload:
1. Skill is stored at: `/egova/skill/skills/{name}/{version}/`
2. Available for download via API
3. Visible to users based on visibility setting

## Commands

| Action | Command |
|--------|---------|
| Login | `.\skill-manager.exe login --username majianquan` |
| Status | `.\skill-manager.exe status` |
| List skills | `.\skill-manager.exe list` |
| Logout | `.\skill-manager.exe logout` |

## File Storage

| File | Path |
|------|------|
| Token | `~/.config/skill-sync/token.enc` |
| User Info | `~/.config/skill-sync/user_info.json` |
| Skills Dir | `~/.local/share/skill-sync/skills/` |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login failed | Check password: Egova@1234 |
| Upload failed | Check skill name matches SKILL.md |
| Scan failed | Review scan report for security issues |
| Token expired | Run `logout` then `login` again |