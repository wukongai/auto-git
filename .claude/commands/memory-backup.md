# Memory Backup

Use this to snapshot local agent memory pointers without copying secrets.

## Steps

1. List memory files for this project.
2. Copy only non-secret project facts into docs or `.ai-native/profile.json`.
3. Keep credentials in Keychain, user MCP config, SSH config, or password manager.
4. Record what changed in `docs/project/logs/`.

Never commit real tokens, private keys, or raw private content.
