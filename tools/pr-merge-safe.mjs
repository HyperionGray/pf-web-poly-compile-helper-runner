#!/usr/bin/env node

/**
 * Safe PR Merge Tool
 * Safely merges a single PR with comprehensive pre-merge checks
 */

import { execSync } from 'child_process';
import fs from 'fs';
import { promises as fsPromises } from 'fs';
import path from 'path';

class SafeMerger {
    constructor() {
        this.prDataPath = path.join(process.env.HOME, '.config', 'pf', 'discovered-prs.json');
        this.prs = [];
    }
    
    async init() {
        this.prs = await this.loadPRs();
        return this;
    }

    async loadPRs() {
        try {
            const data = await fsPromises.readFile(this.prDataPath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code !== 'ENOENT') {
                console.error('❌ Failed to load PR data:', error.message);
            }
        }
        
        return [];
    }

    async findPR(prId) {
        const pr = this.prs.find(p => p.id.toString() === prId.toString());
        if (!pr) {
            console.error(`❌ PR #${prId} not found. Run "pf pr-discover" first.`);
            return null;
        }
        return pr;
    }

    async performPreMergeChecks(pr) {
        console.log(`🔍 Performing comprehensive pre-merge checks for PR #${pr.id}...`);
        console.log(`📋 ${pr.title} by ${pr.author}`);
        console.log('');
        
        const checks = {
            basic: {
                name: 'Basic Requirements',
                tests: {
                    'PR is open': pr.state === 'open',
                    'PR is mergeable': pr.mergeable,
                    'No merge conflicts': !pr.conflicts
                }
            },
            status: {
                name: 'Status Checks',
                tests: {
                    'Status checks pass': pr.statusChecks === 'SUCCESS' || pr.statusChecks === 'PENDING'
                }
            },
            approval: {
                name: 'Approval Requirements',
                tests: {
                    'Has human approval': pr.reviewDecision === 'APPROVED',
                    'Has AI approval': pr.aiRecommendation === 'APPROVE',
                    'No changes requested': pr.reviewDecision !== 'CHANGES_REQUESTED' && pr.aiRecommendation !== 'REQUEST_CHANGES'
                }
            },
            freshness: {
                name: 'Freshness Checks',
                tests: {}
            }
        };
        
        // Fetch latest PR status
        try {
            console.log('🔄 Fetching latest PR status...');
            let cmd;
            if (pr.platform === 'github') {
                cmd = `gh pr view ${pr.id} --repo ${pr.repository} --json mergeable,statusCheckRollup,reviewDecision,state`;
            } else if (pr.platform === 'gitlab') {
                cmd = `glab mr view ${pr.id} --repo ${pr.repository} --output json`;
            }
            
            if (cmd) {
                const output = execSync(cmd, { encoding: 'utf8' });
                const data = JSON.parse(output);
                
                if (pr.platform === 'github') {
                    checks.freshness.tests['Up-to-date mergeable status'] = data.mergeable === 'MERGEABLE';
                    checks.freshness.tests['Latest status checks'] = data.statusCheckRollup?.state === 'SUCCESS';
                    checks.freshness.tests['Current state is open'] = data.state === 'OPEN';
                } else if (pr.platform === 'gitlab') {
                    checks.freshness.tests['Up-to-date mergeable status'] = data.merge_status === 'can_be_merged';
                    checks.freshness.tests['No current conflicts'] = !data.has_conflicts;
                    checks.freshness.tests['Current state is open'] = data.state === 'opened';
                }
            }
        } catch (error) {
            console.warn(`⚠️  Could not fetch latest PR status: ${error.message}`);
            checks.freshness.tests['Status fetch failed'] = false;
        }
        
        // Display check results
        let allPassed = true;
        Object.entries(checks).forEach(([category, checkGroup]) => {
            console.log(`📋 ${checkGroup.name}:`);
            Object.entries(checkGroup.tests).forEach(([test, passed]) => {
                const icon = passed ? '✅' : '❌';
                console.log(`   ${icon} ${test}`);
                if (!passed) allPassed = false;
            });
            console.log('');
        });
        
        // Additional safety checks
        console.log('🛡️  Additional Safety Checks:');
        
        // Check for recent activity
        const lastUpdate = new Date(pr.updatedAt);
        const hoursSinceUpdate = (new Date() - lastUpdate) / (1000 * 60 * 60);
        const recentActivity = hoursSinceUpdate < 24;
        console.log(`   ${recentActivity ? '✅' : '⚠️'} Recent activity (${Math.round(hoursSinceUpdate)}h ago)`);
        
        // Check AI review recency
        if (pr.aiReviewed && pr.lastAiReview) {
            const lastAiReview = new Date(pr.lastAiReview);
            const hoursSinceAiReview = (new Date() - lastAiReview) / (1000 * 60 * 60);
            const recentAiReview = hoursSinceAiReview < 48;
            console.log(`   ${recentAiReview ? '✅' : '⚠️'} Recent AI review (${Math.round(hoursSinceAiReview)}h ago)`);
        }
        
        console.log('');
        
        return allPassed;
    }

    async createBackup(pr) {
        console.log('💾 Creating backup before merge...');
        
        try {
            const backupDir = path.join(process.env.HOME, '.config', 'pf', 'merge-backups');
            
            // recursive: true handles existing directories gracefully
            await fsPromises.mkdir(backupDir, { recursive: true });
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupFile = path.join(backupDir, `${pr.platform}-${pr.repository.replace('/', '-')}-${pr.id}-${timestamp}.json`);
            
            // Save PR data and current git state
            const backupData = {
                pr: pr,
                timestamp: new Date().toISOString(),
                gitState: {
                    currentBranch: execSync('git branch --show-current', { encoding: 'utf8' }).trim(),
                    lastCommit: execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim(),
                    remoteUrl: execSync('git remote get-url origin', { encoding: 'utf8' }).trim()
                }
            };
            
            await fsPromises.writeFile(backupFile, JSON.stringify(backupData, null, 2));
            console.log(`✅ Backup saved to ${backupFile}`);
            
            return backupFile;
        } catch (error) {
            console.warn(`⚠️  Could not create backup: ${error.message}`);
            return null;
        }
    }

    async mergePR(pr, strategy = 'squash', autoDeleteBranch = true) {
        console.log(`🔀 Merging PR #${pr.id} with ${strategy} strategy...`);
        
        try {
            let cmd;
            
            if (pr.platform === 'github') {
                cmd = `gh pr merge ${pr.id} --repo ${pr.repository}`;
                
                switch (strategy) {
                    case 'squash':
                        cmd += ' --squash';
                        break;
                    case 'rebase':
                        cmd += ' --rebase';
                        break;
                    case 'merge':
                        cmd += ' --merge';
                        break;
                    default:
                        cmd += ' --squash';
                }
                
                if (autoDeleteBranch) {
                    cmd += ' --delete-branch';
                }
            } else if (pr.platform === 'gitlab') {
                cmd = `glab mr merge ${pr.id} --repo ${pr.repository}`;
                
                switch (strategy) {
                    case 'squash':
                        cmd += ' --squash';
                        break;
                    case 'rebase':
                        cmd += ' --rebase';
                        break;
                }
                
                if (autoDeleteBranch) {
                    cmd += ' --remove-source-branch';
                }
            } else {
                throw new Error(`Unsupported platform: ${pr.platform}`);
            }
            
            console.log(`🔧 Executing: ${cmd}`);
            const output = execSync(cmd, { encoding: 'utf8' });
            
            console.log('✅ Merge completed successfully!');
            console.log('📄 Output:');
            console.log(output);
            
            return {
                success: true,
                output: output.trim(),
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('❌ Merge failed!');
            console.error('Error:', error.message);
            
            return {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async safeMerge(prId, strategy = 'squash', autoDeleteBranch = true) {
        console.log('🛡️  Starting safe PR merge process...\n');
        
        // Find PR
        const pr = await this.findPR(prId);
        if (!pr) return;
        
        // Pre-merge checks
        const checksPass = await this.performPreMergeChecks(pr);
        if (!checksPass) {
            console.log('❌ Pre-merge checks failed. Merge aborted for safety.');
            console.log('\n💡 Suggestions:');
            console.log('   • Resolve any conflicts');
            console.log('   • Ensure status checks pass');
            console.log('   • Get required approvals');
            console.log('   • Run "pf pr-review-ai" for AI review');
            return;
        }
        
        console.log('✅ All pre-merge checks passed!');
        console.log('');
        
        // Create backup
        const backupFile = await this.createBackup(pr);
        
        // Perform merge
        const result = await this.mergePR(pr, strategy, autoDeleteBranch);
        
        // Save result
        await this.saveMergeResult(pr, result, backupFile);
        
        // Update PR data
        if (result.success) {
            await this.updatePRData(pr, result);
        }
        
        // Display final status
        console.log('\n' + '='.repeat(60));
        if (result.success) {
            console.log('🎉 MERGE COMPLETED SUCCESSFULLY');
            console.log('='.repeat(60));
            console.log(`✅ PR #${pr.id} has been merged`);
            console.log(`📋 Title: ${pr.title}`);
            console.log(`👤 Author: ${pr.author}`);
            console.log(`🔗 Repository: ${pr.repository}`);
            console.log(`⚡ Strategy: ${strategy}`);
            
            if (backupFile) {
                console.log(`💾 Backup: ${backupFile}`);
            }
            
            console.log('\n💡 Next steps:');
            console.log('   pf pr-discover               # Refresh PR list');
            console.log('   pf pr-cleanup                # Clean up merged branches');
        } else {
            console.log('❌ MERGE FAILED');
            console.log('='.repeat(60));
            console.log(`Error: ${result.error}`);
            
            if (backupFile) {
                console.log(`💾 Backup available: ${backupFile}`);
            }
        }
    }

    async saveMergeResult(pr, result, backupFile) {
        const resultsDir = path.join(process.env.HOME, '.config', 'pf', 'merge-results');
        
        // recursive: true handles existing directories gracefully
        await fsPromises.mkdir(resultsDir, { recursive: true });
        
        const resultData = {
            pr: pr,
            result: result,
            backupFile: backupFile,
            timestamp: new Date().toISOString()
        };
        
        const filename = `single-merge-${pr.platform}-${pr.repository.replace('/', '-')}-${pr.id}-${Date.now()}.json`;
        const filepath = path.join(resultsDir, filename);
        
        await fsPromises.writeFile(filepath, JSON.stringify(resultData, null, 2));
        console.log(`💾 Merge result saved to ${filepath}`);
    }

    async updatePRData(pr, result) {
        if (result.success) {
            const prIndex = this.prs.findIndex(p => p.id === pr.id && p.repository === pr.repository);
            if (prIndex !== -1) {
                this.prs[prIndex].state = 'merged';
                this.prs[prIndex].mergedAt = result.timestamp;
                
                await fsPromises.writeFile(this.prDataPath, JSON.stringify(this.prs, null, 2));
                console.log('✅ PR data updated');
            }
        }
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const prId = args[0];
    const strategy = args[1] || 'squash';
    const autoDeleteBranch = args[2] !== 'false';
    
    if (!prId) {
        console.error('❌ Please specify a PR ID');
        console.log('Usage: pf pr-merge-safe pr_id=123 [strategy=squash|merge|rebase] [auto_delete_branch=true]');
        return;
    }
    
    const merger = new SafeMerger();
    await merger.init();
    await merger.safeMerge(prId, strategy, autoDeleteBranch);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default SafeMerger;