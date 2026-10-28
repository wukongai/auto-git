[中文](README.md) | [English](README.en.md)

# Auto Git

**Tell your agent what you want to accomplish. Auto Git uses standard Git to do it safely.**

Auto Git is an Agent Skill for people who do not want to memorize Git commands. Tell Codex,
Claude Code, or another compatible agent to inspect a project, prepare a Commit, connect a
remote repository, Push a branch, or publish a version. Auto Git reads the real repository
state, explains the impact, runs the project's own checks, and asks for approval before a
write or public action.

Current version: **0.1.0-dev.1 safety candidate**. A GitHub backup is recorded; the standard
installation trial remains unverified. The Gitee mirror, formal Tag/Release, and host trials
are still pending. See [verification and result states](references/verification-status.md).

## What you can do

- Check Python, Git, and GitHub CLI capabilities;
- Get guided Git installation and verify your Commit name and email;
- Initialize a standard Git repository in a new folder;
- Inspect the current branch, changes, index, and remotes;
- Include only approved files in a Commit;
- Connect GitHub, Gitee, or another standard Git Remote;
- Check tests, upstream, ahead/behind, and divergence before Push;
- Prepare a version, Tag, Push, and GitHub Release as separate stages;
- Preserve your files and resume or recover after a failed operation.

## What Auto Git does not do

- It does not watch folders in the background;
- It does not automatically Commit or Push;
- It does not create a remote repository, Tag, or Release without approval;
- It does not run `git add -A`, force push, `reset --hard`, or delete unknown files;
- It does not accept, print, or store tokens, passwords, cookies, or private keys;
- It does not require Skill Engineering, a separate Auto Git CLI, or an MCP Server.

## Install Auto Git

You need an Agent Skills-compatible host, a Node.js environment that can run `npx`, and
system Git. The repository-based Skills CLI uses Git to acquire Auto Git, so you must
**install Git before Auto Git**. You do not need to know Git commands. Ask your current
host agent:

> My computer may not have Git. Check and guide installation through the official
> operating-system path. Explain permissions and impact, then verify with git --version.
> Do not initialize a project, Commit, or Push yet.

This bootstrap happens before Auto Git is installed. Once installed, Auto Git reruns doctor
and manages Git checks, plans, verification, and recovery for future projects.

> **Installation notice:** A GitHub backup is recorded. This safety candidate has not been
> pushed, and this run has not checked live source availability. The installation trial
> remains unverified; check the source and access rather than choosing a namesake.

### Install for the current project

```bash
npx skills add wukongai/auto-git
```

This installs Auto Git from the [primary GitHub repository](https://github.com/wukongai/auto-git).
Without `-g`, the installation is scoped to the current project.

### Install for all your projects

```bash
npx skills add wukongai/auto-git -g -a codex -a claude-code
```

- `-g`: install at user scope so multiple projects can use the Skill;
- `-a codex`: expose it to Codex;
- `-a claude-code`: expose it to Claude Code; WorkBuddy uses this Claude Code channel.

A global installation affects multiple projects. Confirm that scope before installation.

### Gitee mirror

Auto Git uses GitHub as the primary source and Gitee as a same-commit mirror. The verified
Gitee installation URL will be added after the first mirror repository is created and
validated. Do not install from an unverified repository with the same name.

Auto Git does not ship an operating-system installer. Installation, updates, and removal
use the standard Skills CLI or the host's native Skill manager.

## First use

Open a project and send this to your agent:

> Use Auto Git to inspect this project. Only check the environment and repository state.
> Tell me what is missing and do not modify anything yet.

Auto Git reports:

1. Whether the current agent discovered the Skill;
2. Whether Python, Git, and GitHub CLI are available;
3. Whether the current folder is a Git repository;
4. The current branch and file changes;
5. The recommended next step and any required approval.

If Git is missing, say:

> Prepare a Git installation plan for this operating system. Explain permissions and impact.
> Wait for my approval, then install it and verify again.

## Everyday use

### Prepare a Commit

> Review these changes with Auto Git. Include only files I approve. Run the project checks
> and show me the Commit plan first.

Auto Git shows the exact files, test results, Commit message, and recovery path. It stages
and commits only after you approve that same plan.

### Connect a remote repository

> Connect this GitHub or Gitee repository. Check the URL, account, and whether the remote is
> empty. Do not Push yet.

Connecting a Remote and pushing code are separate actions. Adding a URL never publishes
your code automatically.

### Push

> Check whether this branch is safe to Push. Fetch first, inspect ahead/behind, run the tests,
> and show me the plan.

If the remote is ahead, histories diverge, tests fail, or the repository changes, Auto Git
stops instead of pulling, rebasing, merging, or force-pushing automatically.

### Publish a version

> Check whether 0.1.0 is ready for Release. Verify the version, changelog, tests, build, and
> Tag. Do not publish yet.

The Release Commit, annotated Tag, branch Push, Tag Push, and GitHub Release require separate
approval. If publication stops halfway, Auto Git reads the public facts and resumes only the
unfinished stages.

## Update and remove

Update:

```bash
npx skills update auto-git
```

This checks and updates the installed Auto Git Skill. Verify host discovery, version, and
doctor after the update.

Remove:

```bash
npx skills remove auto-git
```

This removes files owned by the standard Skill installer. It does not delete your project
files, Git history, or remote repositories. Confirm the scope before removing a global
installation.

## User manual

For a step-by-step installation, Commit, Remote, Push, Release, and recovery Playbook, read:

[Auto Git User Manual (Chinese)](docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md)

The README helps you start quickly. The manual provides copyable prompts, expected results,
and troubleshooting for each operation.

## Support status

- Skill hosts: Codex and Claude Code; WorkBuddy uses the Claude Code channel;
- System guidance: macOS, Windows, Debian/Ubuntu, and Fedora/RHEL;
- Remotes: standard Git Remote; GitHub is the first dedicated repository and Release adapter;
- Historical evidence: 114 root-project tests, 91 pure-Skill candidate tests, and
  temporary-repository scenarios pass;
- Pending release checks: real GitHub/Gitee dual remotes, official Tag/Release, and
  cross-host installation trials.

## Get help

- Usage questions: [GitHub Issues](https://github.com/wukongai/auto-git/issues) after publication;
- Product and safety boundaries:
  [Chinese user manual](docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md);
- Developer sources of truth: [PRD](docs/product/prd/auto-git-v0.1.0.md), [Architecture](docs/engineering/architecture/auto-git.md), and
  [Roadmap](docs/product/roadmap.md).

Give the original error to your agent and ask it to diagnose first, preserve your files,
explain the impact, and then propose a repair plan.
