#!/usr/bin/env node
/**
 * Git Large File Cleanup Tool
 * 
 * An intuitive TUI for removing large files from git history.
 * Uses git-filter-repo for safe and efficient history rewriting.
 */

import { select, checkbox, confirm, input } from '@inquirer/prompts';
import chalk from 'chalk';
import { spawn, execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Table from 'cli-table3';
import ora from 'ora';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Utility functions
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function execCommand(cmd, cwd = process.cwd()) {
  try {
    return execSync(cmd, { cwd, encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 }).trim();
  } catch (error) {
    throw new Error(`Command failed: ${cmd}\n${error.message}`);
  }
}

function checkGitRepo() {
  try {
    execCommand('git rev-parse --git-dir');
    return true;
  } catch {
    return false;
  }
}

function checkGitFilterRepo() {
  try {
    execCommand('git-filter-repo --version');
    return true;
  } catch {
    return false;
  }
}

async function installGitFilterRepo() {
  const spinner = ora('Installing git-filter-repo...').start();
  try {
    // Try pip3 first, then pip
    try {
      execCommand('pip3 install --user git-filter-repo');
    } catch {
      execCommand('pip install --user git-filter-repo');
    }
    spinner.succeed('git-filter-repo installed successfully!');
    return true;
  } catch (error) {
    spinner.fail('Failed to install git-filter-repo');
    console.error(chalk.red(`\nError: ${error.message}`));
    console.log(chalk.yellow('\nPlease install git-filter-repo manually:'));
    console.log(chalk.cyan('  pip3 install --user git-filter-repo'));
    console.log(chalk.cyan('  # or'));
    console.log(chalk.cyan('  pip install --user git-filter-repo'));
    return false;
  }
}

function analyzeLargeFiles(minSize = 1024 * 1024) {
  const spinner = ora('Analyzing git history for large files...').start();
  
  try {
    // Get all blobs with their sizes
    const output = execCommand(
      'git rev-list --all --objects | ' +
      'git cat-file --batch-check="%(objecttype) %(objectname) %(objectsize) %(rest)" | ' +
      'grep "^blob" | ' +
      'sort -k3 -n -r'
    );
    
    const files = [];
    const lines = output.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      const parts = line.split(/\s+/);
      if (parts.length < 4) continue;
      
      const size = parseInt(parts[2]);
      if (size < minSize) break; // Stop when files are smaller than threshold
      
      const filepath = parts.slice(3).join(' ');
      if (!filepath) continue;
      
      files.push({
        hash: parts[1],
        size: size,
        path: filepath,
        formattedSize: formatBytes(size)
      });
    }
    
    spinner.succeed(`Found ${files.length} large files in git history`);
    return files;
  } catch (error) {
    spinner.fail('Failed to analyze git history');
    throw error;
  }
}

function displayLargeFiles(files, limit = 50) {
  if (files.length === 0) {
    console.log(chalk.green('\n✓ No large files found in git history!'));
    return;
  }
  
  const table = new Table({
    head: [
      chalk.cyan('#'),
      chalk.cyan('Size'),
      chalk.cyan('File Path')
    ],
    colWidths: [6, 15, 80],
    wordWrap: true
  });
  
  const displayFiles = files.slice(0, limit);
  displayFiles.forEach((file, idx) => {
    table.push([
      (idx + 1).toString(),
      chalk.yellow(file.formattedSize),
      file.path
    ]);
  });
  
  console.log(chalk.bold('\n📊 Large Files in Git History:\n'));
  console.log(table.toString());
  
  if (files.length > limit) {
    console.log(chalk.gray(`\n... and ${files.length - limit} more files`));
  }
  
  const totalSize = files.reduce((sum, f) => sum + f.size, 0);
  console.log(chalk.bold(`\n💾 Total size: ${chalk.yellow(formatBytes(totalSize))}`));
}

async function selectFilesToRemove(files) {
  const choices = files.map((file, idx) => ({
    name: `${file.formattedSize.padEnd(12)} - ${file.path}`,
    value: file.path,
    description: `Remove ${file.path} from git history`
  }));
  
  const selected = await checkbox({
    message: 'Select files to remove from git history:',
    choices,
    pageSize: 20,
    loop: false,
    instructions: chalk.gray('\nSpace to select, Enter to confirm, A to toggle all')
  });
  
  return selected;
}

async function confirmRemoval(files) {
  console.log(chalk.yellow('\n⚠️  Warning: This operation will rewrite git history!'));
  console.log(chalk.gray('You will need to force-push to remote repositories.'));
  console.log(chalk.gray(`Files to be removed: ${files.length}`));
  
  return await confirm({
    message: 'Are you sure you want to proceed?',
    default: false
  });
}

async function createBackup() {
  const spinner = ora('Creating backup...').start();
  
  try {
    const backupDir = path.join(process.cwd(), '.git-cleanup-backup');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = path.join(backupDir, `backup-${timestamp}`);
    
    // Create backup directory
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
    }
    
    // Create backup using git bundle
    execCommand(`git bundle create "${backupPath}.bundle" --all`);
    
    spinner.succeed(`Backup created at: ${chalk.cyan(backupPath + '.bundle')}`);
    return backupPath + '.bundle';
  } catch (error) {
    spinner.fail('Failed to create backup');
    throw error;
  }
}

async function removeFilesFromHistory(filePaths) {
  console.log(chalk.bold('\n🧹 Removing files from git history...\n'));
  
  // Create a temporary file with paths to remove
  const tempFile = path.join(process.cwd(), '.git-cleanup-paths.txt');
  fs.writeFileSync(tempFile, filePaths.join('\n'));
  
  return new Promise((resolve, reject) => {
    const args = [
      '--invert-paths',
      '--paths-from-file', tempFile,
      '--force'
    ];
    
    const proc = spawn('git-filter-repo', args, {
      cwd: process.cwd(),
      stdio: 'inherit'
    });
    
    proc.on('close', (code) => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempFile);
      } catch {}
      
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`git-filter-repo exited with code ${code}`));
      }
    });
    
    proc.on('error', (error) => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempFile);
      } catch {}
      reject(error);
    });
  });
}

async function showNextSteps() {
  console.log(chalk.green('\n✓ Git history successfully cleaned!\n'));
  console.log(chalk.bold('📝 Next Steps:\n'));
  console.log('1. Review the changes:');
  console.log(chalk.cyan('   git log --all --oneline'));
  console.log('');
  console.log('2. Force-push to remote (⚠️  WARNING: This rewrites history):');
  console.log(chalk.cyan('   git push origin --force --all'));
  console.log(chalk.cyan('   git push origin --force --tags'));
  console.log('');
  console.log('3. Team members must re-clone the repository:');
  console.log(chalk.cyan('   git clone <repository-url>'));
  console.log('');
  console.log(chalk.yellow('⚠️  Important: Coordinate with your team before force-pushing!'));
}

async function main() {
  console.log(chalk.bold.cyan('\n🗑️  Git Large File Cleanup Tool\n'));
  console.log(chalk.gray('Remove large files from git history with an intuitive interface\n'));
  
  // Check if we're in a git repository
  if (!checkGitRepo()) {
    console.error(chalk.red('❌ Error: Not a git repository!'));
    console.log(chalk.gray('Please run this tool from within a git repository.'));
    process.exit(1);
  }
  
  // Check if git-filter-repo is installed
  if (!checkGitFilterRepo()) {
    console.log(chalk.yellow('⚠️  git-filter-repo is not installed.'));
    const shouldInstall = await confirm({
      message: 'Would you like to install it now?',
      default: true
    });
    
    if (shouldInstall) {
      const installed = await installGitFilterRepo();
      if (!installed) {
        process.exit(1);
      }
    } else {
      console.log(chalk.red('\ngit-filter-repo is required. Exiting.'));
      process.exit(1);
    }
  }
  
  try {
    // Step 1: Choose analysis threshold
    const threshold = await select({
      message: 'Select minimum file size to analyze:',
      choices: [
        { name: '100 KB', value: 100 * 1024 },
        { name: '500 KB', value: 500 * 1024 },
        { name: '1 MB', value: 1024 * 1024 },
        { name: '5 MB', value: 5 * 1024 * 1024 },
        { name: '10 MB', value: 10 * 1024 * 1024 },
        { name: '50 MB', value: 50 * 1024 * 1024 },
        { name: 'Custom', value: 'custom' }
      ],
      default: 1024 * 1024
    });
    
    let minSize = threshold;
    if (threshold === 'custom') {
      const customSize = await input({
        message: 'Enter minimum size in MB:',
        default: '1',
        validate: (value) => {
          const num = parseFloat(value);
          if (isNaN(num) || num <= 0) {
            return 'Please enter a valid positive number';
          }
          return true;
        }
      });
      minSize = parseFloat(customSize) * 1024 * 1024;
    }
    
    // Step 2: Analyze repository
    const largeFiles = analyzeLargeFiles(minSize);
    
    if (largeFiles.length === 0) {
      console.log(chalk.green('\n✓ No large files found! Your repository is clean.'));
      process.exit(0);
    }
    
    // Step 3: Display files
    displayLargeFiles(largeFiles);
    
    // Step 4: Select files to remove
    const selectedFiles = await selectFilesToRemove(largeFiles);
    
    if (selectedFiles.length === 0) {
      console.log(chalk.yellow('\nNo files selected. Exiting.'));
      process.exit(0);
    }
    
    // Step 5: Confirm removal
    const confirmed = await confirmRemoval(selectedFiles);
    
    if (!confirmed) {
      console.log(chalk.yellow('\nOperation cancelled.'));
      process.exit(0);
    }
    
    // Step 6: Create backup
    const shouldBackup = await confirm({
      message: 'Create a backup before proceeding?',
      default: true
    });
    
    if (shouldBackup) {
      await createBackup();
    }
    
    // Step 7: Remove files from history
    await removeFilesFromHistory(selectedFiles);
    
    // Step 8: Show next steps
    await showNextSteps();
    
  } catch (error) {
    console.error(chalk.red(`\n❌ Error: ${error.message}`));
    process.exit(1);
  }
}

// Run if executed directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    console.error(chalk.red(`\nFatal error: ${error.message}`));
    process.exit(1);
  });
}

export { main, analyzeLargeFiles, formatBytes };
