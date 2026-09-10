# OuterClient v5.6

## Offline account
The Microsoft Accounts page now includes an Offline Account card.

You can:
- edit the Offline nickname at any time,
- press Save nickname,
- press Enter in the nickname field,
- switch to Offline and immediately edit the nickname.

Offline nickname validation:
- 3–16 characters
- letters, numbers and `_`

The sidebar/account card refreshes immediately after saving.

## CurseForge API
The CurseForge API Key field has been removed from Settings.

OuterClient no longer reads CurseForge credentials from `~/.outerclient.json`.

For public GitHub builds the key is injected at build time from:

`GitHub Actions Secret: CURSEFORGE_API_KEY`

The secret itself is NOT stored in:
- outerclient.py
- build-binaries.yml
- the repository

### One-time GitHub setup
Repository:
Settings → Secrets and variables → Actions → New repository secret

Name:
`CURSEFORGE_API_KEY`

Paste your CurseForge key as the value.

Then run:
`Build and Release OuterClient 5.6`

The workflow creates a temporary `outerclient_build_secrets.py`,
bundles it into AppImage/EXE and does not require the user to enter a key.

For local source development you may instead set:
`OUTERCLIENT_CURSEFORGE_API_KEY`

## Build
Expected assets:
- `OuterClient-v5.6-x86_64.AppImage`
- `OuterClient-v5.6.exe`
