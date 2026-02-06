#!/usr/bin/env node

/**
 * Batch PR Merge Tool
 * Automatically merges approved pull requests with safety checks
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

import { ensureDir, loadPrContext, writeJson } from './pr-common.mjs';

class BatchMerger {
    constructor() {
        this.ctx = loadPrContext();
        this.prDataPath = this.ctx.paths.discoveredPrsFile;
        this.prs = this.loadPRs();
        this.mergeResults = [];
    }

    loadPRs() {
        try {
            if (fs.existsSync(this.prDataPath)) {
                return JSON.parse(fs.readFileSync(this.prDataPath, 'utf8'));
            }
        } catch (error) {
            console.error('❌ Failed to load PR data:', error.message);
        }
        
        return [];
    }

    filterReadyPRs(strategy = 'squash', requireReviews = true, requireAiApproval = true) {
        return this.prs.filter(pr => {
            // Basic requirements
            if (!pr.mergeable) return false;
            if (pr.conflicts) return false;
            if (pr.state !== 'open') return false;
            
            // Status checks
            if (pr.statusChecks === 'FAILURE') return false;
            
            // Review requirements
            if (requireReviews && !pr.reviewDecision) return false;
            if (requireReviews && pr.reviewDecision === 'CHANGES_REQUESTED') return false;
            
            // AI approval requirements
            if (requireAiApproval && !pr.aiReviewed) return false;
            if (requireAiApproval && pr.aiRecommendation === 'REQUEST_CHANGES') return false;
            
            // At least one approval source
            const hasHumanApproval = pr.reviewDecision === 'APPROVED';
            const hasAiApproval = pr.aiRecommendation === 'APPROVE';
            
            if (!hasHumanApproval && !hasAiApproval) return false;
            
            return true;
        });
    }

    async mergePR(pr, strategy = 'squash', autoDeleteBranch = true) {
        console.log(`🔀 Merging ${pr.platform} PR #${pr.id}: ${pr.title}`);
        
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
                        cmd += ' --squash'; // Default to squash
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
                    default:
                        // GitLab default merge
                        break;
                }
                
                if (autoDeleteBranch) {
                    cmd += ' --remove-source-branch';
                }
            } else {
                throw new Error(`Unsupported platform: ${pr.platform}`);
            }
            
            // Execute merge
            const output = execSync(cmd, { encoding: 'utf8' });
            
            return {
                success: true,
                pr: pr,
                output: output.trim(),
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            return {
                success: false,
                pr: pr,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async performPreMergeChecks(pr) {
        console.log(`🔍 Performing pre-merge checks for PR #${pr.id}...`);
        
        const checks = {
            mergeable: pr.mergeable,
            noConflicts: !pr.conflicts,
            statusChecks: pr.statusChecks === 'SUCCESS' || pr.statusChecks === 'PENDING',
            hasApproval: pr.reviewDecision === 'APPROVED' || pr.aiRecommendation === 'APPROVE',
            upToDate: true // We'll check this dynamically
        };
        
        // Check if PR is up to date (fetch latest status)
        try {
            let cmd;
            if (pr.platform === 'github') {
                cmd = `gh pr view ${pr.id} --repo ${pr.repository} --json mergeable,statusCheckRollup`;
            } else if (pr.platform === 'gitlab') {
                cmd = `glab mr view ${pr.id} --repo ${pr.repository} --output json`;
            }
            
            if (cmd) {
                const output = execSync(cmd, { encoding: 'utf8' });
                const data = JSON.parse(output);
                
                if (pr.platform === 'github') {
                    checks.mergeable = data.mergeable === 'MERGEABLE';
                    checks.statusChecks = data.statusCheckRollup?.state === 'SUCCESS';
                } else if (pr.platform === 'gitlab') {
                    checks.mergeable = data.merge_status === 'can_be_merged';
                    checks.noConflicts = !data.has_conflicts;
                }
            }
        } catch (error) {
            console.warn(`⚠️  Could not fetch latest PR status: ${error.message}`);
        }
        
        const allPassed = Object.values(checks).every(check => check);
        
        if (!allPassed) {
            console.log('❌ Pre-merge checks failed:');
            Object.entries(checks).forEach(([check, passed]) => {
                const icon = passed ? '✅' : '❌';
                console.log(`   ${icon} ${check}`);
            });
        }
        
        return allPassed;
    }

    async batchMerge(strategy = 'squash', requireReviews = true, requireAiApproval = true, dryRun = false) {
        console.log('🚀 Starting batch PR merge process...\n');
        
        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }
        
        // Filter ready PRs
        const readyPRs = this.filterReadyPRs(strategy, requireReviews, requireAiApproval);
        
        console.log(`📊 Merge Analysis:`);
        console.log(`   Total PRs: ${this.prs.length}`);
        console.log(`   Ready to merge: ${readyPRs.length}`);
        console.log(`   Strategy: ${strategy}`);
        console.log(`   Require reviews: ${requireReviews}`);
        console.log(`   Require AI approval: ${requireAiApproval}`);
        console.log(`   Dry run: ${dryRun}`);
        console.log('');
        
        if (readyPRs.length === 0) {
            console.log('✅ No PRs ready for merging at this time.');
            console.log('\n💡 Suggestions:');
            console.log('   pf pr-review-all-ai          # Review pending PRs');
            console.log('   pf pr-conflict-detect        # Check for conflicts');
            console.log('   pf pr-list needs-review      # See what needs attention');
            return;
        }
        
        // Display PRs to be merged
        console.log('📋 PRs ready for merging:');
        readyPRs.forEach((pr, index) => {
            const approvalIcon = pr.reviewDecision === 'APPROVED' ? '👥' : '🤖';
            console.log(`${index + 1}. ${approvalIcon} ${pr.platform} ${pr.repository}#${pr.id}: ${pr.title}`);
        });
        console.log('');
        
        if (dryRun) {
            console.log('🔍 DRY RUN - No actual merging will be performed');
            return;
        }
        
        // Confirm before proceeding
        if (readyPRs.length > 1) {
            console.log('⚠️  About to merge multiple PRs. This action cannot be undone.');
            // In a real implementation, you might want to add interactive confirmation
        }
        
        // Merge each PR
        for (const pr of readyPRs) {
            console.log(`\n${'='.repeat(60)}`);
            
            // Pre-merge checks
            const checksPass = await this.performPreMergeChecks(pr);
            if (!checksPass) {
                console.log(`❌ Skipping PR #${pr.id} due to failed pre-merge checks`);
                this.mergeResults.push({
                    success: false,
                    pr: pr,
                    error: 'Pre-merge checks failed',
                    timestamp: new Date().toISOString()
                });
                continue;
            }
            
            // Perform merge
            const result = await this.mergePR(pr, strategy, true);
            this.mergeResults.push(result);
            
            if (result.success) {
                console.log(`✅ Successfully merged PR #${pr.id}`);
            } else {
                console.log(`❌ Failed to merge PR #${pr.id}: ${result.error}`);
            }
            
            // Small delay between merges
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Save results and display summary
        this.saveMergeResults();
        this.displaySummary();
        this.updatePRData();
    }

    saveMergeResults() {
        const resultsDir = this.ctx.paths.mergeResultsDir;
        ensureDir(resultsDir);
        
        const filename = `batch-merge-${Date.now()}.json`;
        const filepath = path.join(resultsDir, filename);
        
        writeJson(filepath, this.mergeResults);
        console.log(`\n💾 Merge results saved to ${filepath}`);
    }

    displaySummary() {
        const successful = this.mergeResults.filter(r => r.success).length;
        const failed = this.mergeResults.filter(r => !r.success).length;
        
        console.log('\n' + '='.repeat(60));
        console.log('📊 BATCH MERGE SUMMARY');
        console.log('='.repeat(60));
        console.log(`✅ Successful merges: ${successful}`);
        console.log(`❌ Failed merges: ${failed}`);
        console.log(`📊 Total processed: ${this.mergeResults.length}`);
        
        if (failed > 0) {
            console.log('\n❌ Failed merges:');
            this.mergeResults.filter(r => !r.success).forEach(result => {
                console.log(`   • PR #${result.pr.id} (${result.pr.repository}): ${result.error}`);
            });
        }
        
        if (successful > 0) {
            console.log('\n✅ Successfully merged:');
            this.mergeResults.filter(r => r.success).forEach(result => {
                console.log(`   • PR #${result.pr.id} (${result.pr.repository}): ${result.pr.title}`);
            });
        }
        
        console.log('\n💡 Next steps:');
        console.log('   pf pr-cleanup                # Clean up merged branches');
        console.log('   pf pr-discover               # Refresh PR list');
        console.log('   pf pr-analytics              # Generate merge analytics');
    }

    updatePRData() {
        // Update PR data to reflect merged status
        this.mergeResults.forEach(result => {
            if (result.success) {
                const prIndex = this.prs.findIndex(p => 
                    p.id === result.pr.id && p.repository === result.pr.repository
                );
                if (prIndex !== -1) {
                    this.prs[prIndex].state = 'merged';
                    this.prs[prIndex].mergedAt = result.timestamp;
                }
            }
        });
        
        // Save updated PR data
        writeJson(this.prDataPath, this.prs);
        console.log('✅ PR data updated with merge results');
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const strategy = args[0] || 'squash';
    const requireReviews = args[1] !== 'false';
    const requireAiApproval = args[2] !== 'false';
    const dryRun = args[3] === 'true';
    
    const merger = new BatchMerger();
    await merger.batchMerge(strategy, requireReviews, requireAiApproval, dryRun);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default BatchMerger;
