#!/usr/bin/env node
/**
 * Git Large File Cleanup Tool - Testable Version
 * 
 * Enhanced version with dependency injection for comprehensive testing
 * Maintains full compatibility with original while adding test capabilities
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

// Constants
const MAX_BUFFER_SIZE = 50 * 1024 * 1024;
const TEMP_FILE_PREFIX = '.git-cleanup-paths-';

export class GitCleanupTool {
  constructor(dependencies = {}) {
    // Dependency injection for testing
    this.deps = {
      execSync: dependencies.execSync || execSync,
      fs: dependencies.fs || fs,
      prompts: {
        select: dependencies.select || select,
        checkbox: dependencies.checkbox || checkbox,
        confirm: dependencies.confirm || confirm,
        input: dependencies.input || input
      },
      ora: dependencies.ora || ora,
      chalk: dependencies.chalk || chalk,
      console: dependencies.console || console,
      process: dependencies.process || process,
      ...dependencies
    };
    
    this.isTestMode = process.env.TUI_TEST_MODE === 'true';
    this.testId = process.env.TUI_TEST_ID || '';
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  execCommand(cmd, cwd = this.deps.process.cwd()) {
    try {
      return this.deps.execSync(cmd, { 
        cwd, 
        encoding: 'utf-8', 
        maxBuffer: MAX_BUFFER_SIZE 
      }).trim();
    } catch (error) {
      throw new Error(`Command failed: ${cmd}\n${error.message}`);
    }
  }

  checkGitRepo() {
    try {
      this.execCommand('git rev-parse --git-dir');
      return true;
    } catch {
      return false;
    }
  }

  checkGitFilterRepo() {
    try {
      this.execCommand('git-filter-repo --version');
      return true;
    } catch {
      return false;
    }
  }

  async getLargeFiles(minSizeBytes) {
    const spinner = this.deps.ora('Analyzing git repository for large files...').start();
    
    try {
      // Get all objects in git history
      const objects = this.execCommand('git rev-list --all --objects');
      
      if (!objects.trim()) {
        spinner.succeed('Analysis complete');
        return [];
      }

      // Get file sizes
      const batchCheck = this.execCommand(
        `git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)'`,
        undefined,
        objects
      );

      const files = [];
      const lines = batchCheck.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('blob ')) {
          const parts = line.split(' ');
          const size = parseInt(parts[2]);
          const filename = parts.slice(3).join(' ');
          
          if (size >= minSizeBytes && filename) {
            files.push({ filename, size });
          }
        }
      }

      // Sort by size (largest first)
      files.sort((a, b) => b.size - a.size);
      
      spinner.succeed(`Found ${files.length} large files`);
      return files;
      
    } catch (error) {
      spinner.fail('Failed to analyze repository');
      throw error;
    }
  }

  async selectThreshold() {
    const choices = [
      { name: '100 KB', value: 100 * 1024 },
      { name: '500 KB', value: 500 * 1024 },
      { name: '1 MB', value: 1024 * 1024 },
      { name: '5 MB', value: 5 * 1024 * 1024 },
      { name: '10 MB', value: 10 * 1024 * 1024 },
      { name: '50 MB', value: 50 * 1024 * 1024 },
      { name: 'Custom', value: 'custom' }
    ];

    const threshold = await this.deps.prompts.select({
      message: 'Select minimum file size to analyze:',
      choices
    });

    if (threshold === 'custom') {
      const customSize = await this.deps.prompts.input({
        message: 'Enter custom size (e.g., 2MB, 500KB):',
        validate: (input) => {
          const match = input.match(/^(\d+(?:\.\d+)?)\s*(KB|MB|GB)$/i);
          return match ? true : 'Please enter a valid size (e.g., 2MB, 500KB)';
        }
      });

      const match = customSize.match(/^(\d+(?:\.\d+)?)\s*(KB|MB|GB)$/i);
      const value = parseFloat(match[1]);
      const unit = match[2].toUpperCase();
      
      const multipliers = { KB: 1024, MB: 1024 * 1024, GB: 1024 * 1024 * 1024 };
      return value * multipliers[unit];
    }

    return threshold;
  }

  displayFilesTable(files) {
    if (files.length === 0) {
      this.deps.console.log(this.deps.chalk.yellow('No files found larger than the specified threshold.'));
      return;
    }

    const table = new Table({
      head: ['#', 'Size', 'File Path'],
      colWidths: [6, 15, 50]
    });

    files.forEach((file, index) => {
      table.push([
        index + 1,
        this.formatBytes(file.size),
        file.filename
      ]);
    });

    this.deps.console.log(this.deps.chalk.cyan('\n📊 Large Files in Git History:\n'));
    this.deps.console.log(table.toString());
    
    const totalSize = files.reduce((sum, file) => sum + file.size, 0);
    this.deps.console.log(this.deps.chalk.blue(`\n💾 Total size: ${this.formatBytes(totalSize)}\n`));
  }

  async selectFilesToRemove(files) {
    const choices = files.map((file, index) => ({
      name: `${this.formatBytes(file.size).padEnd(12)} - ${file.filename}`,
      value: index,
      checked: false
    }));

    const selectedIndices = await this.deps.prompts.checkbox({
      message: 'Select files to remove from git history:',
      choices,
      validate: (answer) => {
        return answer.length > 0 ? true : 'Please select at least one file to remove.';
      }
    });

    return selectedIndices.map(index => files[index]);
  }

  async createBackup() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = `backup-${timestamp}.bundle`;
    const backupDir = '.git-cleanup-backup';
    
    // Create backup directory if it doesn't exist
    if (!this.deps.fs.existsSync(backupDir)) {
      this.deps.fs.mkdirSync(backupDir);
    }
    
    const backupPath = path.join(backupDir, backupFile);
    
    const spinner = this.deps.ora('Creating backup...').start();
    
    try {
      this.execCommand(`git bundle create "${backupPath}" --all`);
      spinner.succeed(`Backup created at: ${backupPath}`);
      return backupPath;
    } catch (error) {
      spinner.fail('Failed to create backup');
      throw new Error(`Backup creation failed: ${error.message}`);
    }
  }

  async removeFilesFromHistory(selectedFiles) {
    // Create temporary file with paths to remove
    const timestamp = Date.now();
    const pid = this.deps.process.pid;
    const tempFile = `${TEMP_FILE_PREFIX}${timestamp}-${pid}.txt`;
    
    try {
      // Write file paths to temporary file
      const filePaths = selectedFiles.map(file => file.filename).join('\n');
      this.deps.fs.writeFileSync(tempFile, filePaths);
      
      const spinner = this.deps.ora('Removing files from git history...').start();
      
      // Use git-filter-repo to remove files
      this.execCommand(`git-filter-repo --invert-paths --paths-from-file "${tempFile}" --force`);
      
      spinner.succeed('Git history successfully cleaned!');
      
    } finally {
      // Clean up temporary file
      if (this.deps.fs.existsSync(tempFile)) {
        this.deps.fs.unlinkSync(tempFile);
      }
    }
  }

  displayNextSteps() {
    this.deps.console.log(this.deps.chalk.green('\n📝 Next Steps:\n'));
    this.deps.console.log('1. Review the changes with: git log --oneline');
    this.deps.console.log('2. If satisfied, force push to remote: git push --force-with-lease origin main');
    this.deps.console.log('3. Team members should re-clone the repository');
    this.deps.console.log('4. The backup bundle can be used to restore if needed\n');
    
    this.deps.console.log(this.deps.chalk.yellow('⚠️  Warning: All team members will need to re-clone the repository!'));
  }

  async run() {
    try {
      this.deps.console.log(this.deps.chalk.blue('🧹 Git Large File Cleanup Tool\n'));
      
      // Check if we're in a git repository
      if (!this.checkGitRepo()) {
        this.deps.console.log(this.deps.chalk.red('❌ Error: This directory is not a git repository.'));
        this.deps.process.exit(1);
      }
      
      // Check if git-filter-repo is installed
      if (!this.checkGitFilterRepo()) {
        this.deps.console.log(this.deps.chalk.red('❌ Error: git-filter-repo is not installed.'));
        this.deps.console.log('Install it with: pip install git-filter-repo');
        this.deps.process.exit(1);
      }
      
      // Get threshold from user
      const threshold = await this.selectThreshold();
      
      // Find large files
      const largeFiles = await this.getLargeFiles(threshold);
      
      if (largeFiles.length === 0) {
        this.deps.console.log(this.deps.chalk.green(`✅ No files found larger than ${this.formatBytes(threshold)}.`));
        return;
      }
      
      // Display files in a table
      this.displayFilesTable(largeFiles);
      
      // Let user select files to remove
      const selectedFiles = await this.selectFilesToRemove(largeFiles);
      
      if (selectedFiles.length === 0) {
        this.deps.console.log(this.deps.chalk.yellow('No files selected. Operation cancelled.'));
        return;
      }
      
      // Show warning and get confirmation
      this.deps.console.log(this.deps.chalk.red('\n⚠️  Warning: This operation will rewrite git history!'));
      this.deps.console.log('This will:');
      this.deps.console.log('• Remove selected files from ALL commits');
      this.deps.console.log('• Change commit hashes');
      this.deps.console.log('• Require force push to remote');
      this.deps.console.log('• Require team members to re-clone\n');
      
      const proceed = await this.deps.prompts.confirm({
        message: 'Are you sure you want to proceed?',
        default: false
      });
      
      if (!proceed) {
        this.deps.console.log(this.deps.chalk.yellow('Operation cancelled.'));
        return;
      }
      
      // Create backup
      await this.createBackup();
      
      // Final confirmation
      const finalConfirm = await this.deps.prompts.confirm({
        message: 'Last chance! Proceed with removing files from git history?',
        default: false
      });
      
      if (!finalConfirm) {
        this.deps.console.log(this.deps.chalk.yellow('Operation cancelled.'));
        return;
      }
      
      // Remove files from history
      await this.removeFilesFromHistory(selectedFiles);
      
      // Show next steps
      this.displayNextSteps();
      
    } catch (error) {
      this.deps.console.log(this.deps.chalk.red(`❌ Error: ${error.message}`));
      this.deps.process.exit(1);
    }
  }
}

// Create and run tool if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const tool = new GitCleanupTool();
  tool.run();
}

export default GitCleanupTool;