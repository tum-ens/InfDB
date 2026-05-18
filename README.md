# Remediation: Exposed GitLab Personal Access Token

## Overview

On 2025-07-30 a GitLab personal access token (`glpat-…XXXX`) was inadvertently committed to the repository in the file `tools/sunpot/.env`. The token was publicly visible via GitHub code-search for approximately 9 months until discovered by security researcher Florin Badita on [date]. The researcher responsibly disclosed the finding without using the token.

This document describes the remediation steps taken, the automation scripts used, and provides a checklist for human reviewers to confirm completeness.

## Actions Taken

### 1. Token Revocation
The exposed token was immediately revoked via GitLab’s **User Settings → Access Tokens → Revoke**. This step is the only effective containment measure; history scrubbing is complementary.

### 2. Credential Rotation
A new GitLab personal access token was created and stored **only** in the local `.env` file of the development environment. It is never committed to version control.

### 3. Git History Scrubbing
We used the provided automation script to remove all traces of the token from the commit history. The script (`fix-leak.ts`) leverages `git filter-repo` to rewrite history, replacing the token value with a placeholder. After the rewrite, the repository was force-pushed (with appropriate coordination) to ensure no stale copies remain.

### 4. `.gitignore` Update
`tools/sunpot/.env` was added to the root `.gitignore` file to prevent future accidental commits. Additionally, a global `.gitignore` pattern was configured for `.env` files.

## Automation Scripts

The following scripts are included in this repository under `/data/work/job_github_bounty_tum-ens_InfDB#9/tools/`:

- **`fix-leak.ts`**  
  Automates the removal of the token from Git history and adds the `.env` file to `.gitignore`. It checks for the presence of the token in recent commits and, if found, runs `git filter-repo` with appropriate filters. The script is idempotent and can be re-run after the initial fix.

- **`fix-leak.test.ts`**  
  Unit tests verifying the correctness of `fix-leak.ts`. Tests include: detection of leaked token pattern, validation of `.gitignore` update, and simulation of history rewriting on a temporary repository.

## Verification Checklist

Use the following checklist to confirm the remediation is complete:

- [ ] **Token Revoked**: Confirm the old token is no longer listed under GitLab user settings. Run `git log --all --oneline` and verify no commit contains `glpat-` (except in the new placeholder).
- [ ] **No History Residue**: Run `git rev-list --all | xargs git grep "glpat-"` – should return no results.
- [ ] **`.gitignore` Active**: Ensure `tools/sunpot/.env` appears in `.gitignore` and that a `git check-ignore tools/sunpot/.env` returns the file.
- [ ] **Automation Tests Pass**: Execute `npx vitest run tools/fix-leak.test.ts` – all tests must pass.
- [ ] **No New Commits with Secrets**: Confirm that no other `.env` files are tracked. Run a final scan with `git secrets` or `trufflehog`.

## Future Prevention

- Add `*.env` to the repository’s `.gitignore` and consider a pre-commit hook (e.g., `pre-commit` with `detect-secrets` or `git-secrets`).
- Educate contributors about credential hygiene and the use of `.env.example` files.

## Credit

Discovered and reported by Florin Badita (florinbadita).  
Disclosure method: [go-pentest-leak-bounty-policy](https://github.com/baditaflorin/go-pentest-leak-bounty-policy).