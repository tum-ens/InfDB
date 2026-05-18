javascript
#!/usr/bin/env node

/**
 * @file Automated remediation script for leaked GitLab personal access tokens.
 *
 * Steps performed:
 * 1. Instructs the user to manually revoke the leaked token in GitLab.
 * 2. Instructs the user to create a new token (rotation) and store it securely.
 * 3. Checks for required dependencies (git, git-filter-repo).
 * 4. Verifies the script is run from a git repository root.
 * 5. Checks for uncommitted changes and prompts the user to proceed.
 * 6. Validates that the sensitive file exists in git history before scrubbing.
 * 7. Warns about force-push implications for shared repositories.
 * 8. Asks for user confirmation before rewriting history.
 * 9. Removes the sensitive file from git history using `git filter-repo`.
 * 10. Deletes the working-tree `.env` file.
 * 11. Adds the file pattern to `.gitignore`.
 * 12. Outputs summary and force-push instructions.
 *
 * @module fix-leak
 * @requires child_process
 * @requires fs/promises
 * @requires path
 * @requires readline
 */

import { execFile } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import readline from 'readline';
import { promisify } from 'util';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** The sensitive file that was leaked. */
const SENSITIVE_FILE = 'tools/sunpot/.env';

/** Path to `.gitignore` in the repository root. */
const GITIGNORE_PATH = path.resolve('.gitignore');

/** The pattern to add to `.gitignore` for the sensitive file. */
const GITIGNORE_PATTERN = `${SENSITIVE_FILE}`;

/** Prefix for informational logs. */
const LOG_INFO = '[INFO]';

/** Prefix for warning logs. */
const LOG_WARN = '[WARN]';

/** Prefix for error logs. */
const LOG_ERROR = '[ERROR]';

/** Exit code for success. */
const EXIT_SUCCESS = 0;

/** Exit code for failure. */
const EXIT_FAILURE = 1;

// ---------------------------------------------------------------------------
// Custom error classes
// ---------------------------------------------------------------------------

/** Error thrown when a required system dependency is missing. */
class DependencyError extends Error {
  /**
   * @param {string} message – Human‑readable description.
   * @param {string} [command] – The missing command name.
   */
  constructor(message, command) {
    super(message);
    this.name = 'DependencyError';
    /** @type {string|undefined} */
    this.command = command;
  }
}

/** Error thrown when a git operation fails. */
class GitError extends Error {
  /**
   * @param {string} message – Error description.
   * @param {string} [command] – The git command that failed.
   * @param {number} [exitCode] – The process exit code.
   */
  constructor(message, command, exitCode) {
    super(message);
    this.name = 'GitError';
    /** @type {string|undefined} */
    this.command = command;
    /** @type {number|undefined} */
    this.exitCode = exitCode;
  }
}

/** Error thrown when the user cancels the operation. */
class UserCancelError extends Error {
  constructor(message = 'Operation cancelled by user.') {
    super(message);
    this.name = 'UserCancelError';
  }
}

// ---------------------------------------------------------------------------
// Promisified utilities
// ---------------------------------------------------------------------------

/** Promisified version of child_process.execFile. */
const execFileAsync = promisify(execFile);

/**
 * Simple logger with levels.
 * @type {{ info: (msg: string) => void, warn: (msg: string) => void, error: (msg: string) => void }}
 */
const logger = {
  /** @param {string} msg */
  info: (msg) => console.log(`${LOG_INFO} ${msg}`),
  /** @param {string} msg */
  warn: (msg) => console.warn(`${LOG_WARN} ${msg}`),
  /** @param {string} msg */
  error: (msg) => console.error(`${LOG_ERROR} ${msg}`),
};

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

/**
 * Check whether a command is available in the system PATH.
 *
 * @param {string} command – The command to check.
 * @returns {Promise<boolean>} `true` if the command is found.
 */
async function commandExists(command) {
  try {
    await execFileAsync('which', [command]);
    return true;
  } catch {
    return false;
  }
}

/**
 * Run a command with arguments and return trimmed stdout.
 *
 * @param {string} cmd – The executable path.
 * @param {string[]} args – Arguments for the command.
 * @returns {Promise<string>} Trimmed stdout.
 * @throws {GitError} If the command exits with a non‑zero status.
 */
async function runCommand(cmd, args) {
  try {
    const { stdout, stderr } = await execFileAsync(cmd, args, {
      timeout: 30000,
    });
    if (stderr && !stderr.includes('warning')) {
      logger.warn(`Command produced stderr: ${stderr.trim()}`);
    }
    return stdout.trim();
  } catch (/** @type {any} */ error) {
    throw new GitError(
      `Command failed: "${cmd} ${args.join(' ')}"`,
      cmd,
      error.code ?? error.status ?? undefined
    );
  }
}

/**
 * Prompt the user for a yes/no answer.
 *
 * @param {string} question – The question to display.
 * @returns {Promise<boolean>} `true` if the user answered yes.
 */
async function askYesNo(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(`${question} (y/N) `, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
    });
  });
}

// ---------------------------------------------------------------------------
// Validation functions
// ---------------------------------------------------------------------------

/**
 * Ensure the script is running from a git repository root.
 *
 * @returns {Promise<void>}
 * @throws {GitError} If not inside a git repo or not at the root.
 */
async function ensureGitRepo() {
  const gitDir = await runCommand('git', ['rev-parse', '--git-dir']);
  if (gitDir !== '.git') {
    throw new GitError(
      'Script must be run from the repository root. ' +
      `Expected '.git', got '${gitDir}'.`,
      'git rev-parse --git-dir'
    );
  }
}

/**
 * Check that `git-filter-repo` is installed.
 *
 * @returns {Promise<void>}
 * @throws {DependencyError} If `git-filter-repo` is not found.
 */
async function ensureFilterRepo() {
  const exists = await commandExists('git-filter-repo');
  if (!exists) {
    throw new DependencyError(
      'git-filter-repo is not installed. Install it via:\n' +
      '  - macOS: brew install git-filter-repo\n' +
      '  - Linux: pip install git-filter-repo\n' +
      '  - Windows: pip install git-filter-repo\n' +
      'After installation, run this script again.',
      'git-filter-repo'
    );
  }
}

/**
 * Check if the sensitive file exists in the working tree.
 *
 * @returns {Promise<boolean>} `true` if the file exists.
 */
async function sensitiveFileInWorkingTree() {
  try {
    await fs.access(SENSITIVE_FILE);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if the sensitive file has ever been tracked in git history.
 *
 * @returns {Promise<boolean>} `true` if the file appears in any commit.
 */
async function sensitiveFileInHistory() {
  try {
    const output = await runCommand('git', [
      'log', '--oneline', '--', SENSITIVE_FILE,
    ]);
    return output.length > 0;
  } catch {
    return false;
  }
}

/**
 * Check for uncommitted changes (unstaged and uncommitted files).
 *
 * @returns {Promise<boolean>} `true` if there are uncommitted changes.
 */
async function hasUncommittedChanges() {
  const status = await runCommand('git', ['status', '--porcelain']);
  return status.length > 0;
}

/**
 * Check if the repository has a remote with commits pushed.
 *
 * @returns {Promise<boolean>} `true` if at least one remote branch exists.
 */
async function hasRemoteCommits() {
  try {
    const output = await runCommand('git', ['branch', '-r']);
    return output.length > 0;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Remediation actions
// ---------------------------------------------------------------------------

/**
 * Delete the sensitive file from the working tree.
 *
 * @returns {Promise<void>}
 */
async function deleteSensitiveFile() {
  try {
    await fs.unlink(SENSITIVE_FILE);
    logger.info(`Deleted working-tree file: ${SENSITIVE_FILE}`);
  } catch (/** @type {any} */ error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
    logger.info(`Working-tree file already absent: ${SENSITIVE_FILE}`);
  }
}

/**
 * Add the sensitive file pattern to `.gitignore`.
 *
 * @returns {Promise<void>}
 */
async function addToGitignore() {
  let content = '';
  try {
    content = await fs.readFile(GITIGNORE_PATH, 'utf8');
  } catch {
    // File doesn't exist, start fresh
  }

  const lines = content.split('\n');
  const patternLine = GITIGNORE_PATTERN;

  // Avoid duplicate entries
  if (lines.includes(patternLine)) {
    logger.info(`${GITIGNORE_PATTERN} already present in .gitignore`);
    return;
  }

  // Ensure it ends with newline
  const toAppend = content.endsWith('\n') ? `${patternLine}\n` : `\n${patternLine}\n`;
  await fs.appendFile(GITIGNORE_PATH, toAppend, 'utf8');
  logger.info(`Added '${GITIGNORE_PATTERN}' to .gitignore`);
}

/**
 * Remove the sensitive file from git history using git-filter-repo.
 *
 * @returns {Promise<void>}
 */
async function scrubHistory() {
  logger.info('Running git-filter-repo to remove sensitive file from history...');
  await runCommand('git', [
    'filter-repo',
    '--path', SENSITIVE_FILE,
    '--invert-paths',
    '--force',
  ]);
  logger.info('History rewritten successfully.');
}

// ---------------------------------------------------------------------------
// Main workflow
// ---------------------------------------------------------------------------

/**
 * Main entry point – orchestrates the entire remediation process.
 *
 * @returns {Promise<number>} Exit code.
 */
async function main() {
  try {
    logger.info('=== GitLab Token Leak Remediation Script ===\n');
    logger.info('Step 1: Manual revocation (you must do this in GitLab).');
    logger.info('Step 2: Create a new token and store it locally.\n');

    // -----------------------------------------------------------------------
    // Environment checks
    // -----------------------------------------------------------------------
    await ensureGitRepo();
    logger.info('Repository root confirmed.');

    await ensureFilterRepo();

    const hasUncommitted = await hasUncommittedChanges();
    if (hasUncommitted) {
      logger.warn('You have uncommitted changes.');
      const proceed = await askYesNo('Continue anyway? Uncommitted changes might interfere.');
      if (!proceed) {
        throw new UserCancelError();
      }
    }

    const historyExists = await sensitiveFileInHistory();
    if (!historyExists) {
      logger.info(`The file '${SENSITIVE_FILE}' was never committed. No history to scrub.`);
      const filePresent = await sensitiveFileInWorkingTree();
      if (filePresent) {
        await deleteSensitiveFile();
        await addToGitignore();
        logger.info('Cleanup complete. No git rewrite needed.');
      } else {
        logger.info('Nothing to do: file is not present and never was in history.');
      }
      return EXIT_SUCCESS;
    }

    // -----------------------------------------------------------------------
    // Warning about shared repository
    // -----------------------------------------------------------------------
    const hasRemote = await hasRemoteCommits();
    if (hasRemote) {
      logger.warn(
        'This repository has remote branches. If you already pushed commits containing the secret,\n' +
        'rewriting history will require a force push and all collaborators will need to rebase.\n' +
        'Please coordinate with your team before proceeding.'
      );
    }

    // -----------------------------------------------------------------------
    // Final confirmation
    // -----------------------------------------------------------------------
    logger.info(`Will remove '${SENSITIVE_FILE}' from entire git history`);
    const confirmed = await askYesNo(
      'Are you absolutely sure you want to rewrite the repository history?'
    );
    if (!confirmed) {
      throw new UserCancelError('User declined history rewrite.');
    }

    // -----------------------------------------------------------------------
    // Perform remediation
    // -----------------------------------------------------------------------
    await scrubHistory();
    await deleteSensitiveFile();
    await addToGitignore();

    // -----------------------------------------------------------------------
    // Summary
    // -----------------------------------------------------------------------
    logger.info('\n=== Remediation Complete ===');
    logger.info('Required manual steps:');
    logger.info('  1. Revoke the leaked token in GitLab (if not already done).');
    logger.info('  2. Create a new token and store it securely outside the repo.');
    if (hasRemote) {
      logger.info('\nNow force-push the rewritten history:');
      logger.info('  git push origin --force --all');
      logger.info('  git push origin --force --tags');
      logger.info('WARNING: All collaborators must clone fresh or rebase their work.');
    }
    logger.info(`\n${GITIGNORE_PATTERN} has been added to .gitignore`);

    return EXIT_SUCCESS;
  } catch (/** @type {any} */ error) {
    if (error instanceof UserCancelError) {
      logger.info('Operation cancelled. No changes made.');
      return EXIT_SUCCESS;
    }

    if (error instanceof DependencyError || error instanceof GitError) {
      logger.error(`${error.name}: ${error.message}`);
      if (error.command) {
        logger.error(`Failed command: ${error.command}`);
      }
    } else {
      logger.error(`Unexpected error: ${error.message ?? error}`);
      if (error.stack) {
        logger.error(error.stack);
      }
    }
    return EXIT_FAILURE;
  }
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

// Handle SIGINT gracefully
process.on('SIGINT', () => {
  logger.info('Received SIGINT. Exiting.');
  process.exit(EXIT_FAILURE);
});

main()
  .then((code) => process.exit(code))
  .catch((/** @type {any} */ error) => {
    logger.error(`Fatal: ${error.message ?? error}`);
    process.exit(EXIT_FAILURE);
  });