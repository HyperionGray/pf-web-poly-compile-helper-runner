#!/usr/bin/env node

/**
 * PR Conflict Detection Tool
 * Detects potential merge conflicts across pull requests
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

import { ensureDir, loadPrContext, writeJson } from './pr-common.mjs';

class ConflictDetector {
    constructor() {
        this.ctx = loadPrContext();
        this.prDataPath = this.ctx.paths.discoveredPrsFile;
        this.prs = this.loadPRs();
        this.conflicts = [];
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

    async detectConflicts(checkAll = true) {
        console.log('⚠️  Starting conflict detection analysis...\n');
        
        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }
        
        const openPRs = this.prs.filter(pr => pr.state === 'open');
        console.log(`📊 Analyzing ${openPRs.length} open PRs for conflicts...`);
        console.log('');
        
        // Check each PR for conflicts
        for (const pr of openPRs) {
            await this.checkPRConflicts(pr);
        }
        
        // Cross-PR conflict analysis
        if (checkAll) {
            await this.analyzeCrossPRConflicts(openPRs);
        }
        
        // Display results
        this.displayResults();
        this.saveResults();
        this.updatePRData();
    }

    async checkPRConflicts(pr) {
        console.log(`🔍 Checking ${pr.platform} PR #${pr.id}: ${pr.title.substring(0, 50)}...`);
        
        try {
            let conflictData = {
                pr: pr,
                hasConflicts: false,
                conflictFiles: [],
                mergeableStatus: 'unknown',
                statusChecks: pr.statusChecks,
                lastChecked: new Date().toISOString()
            };
            
            // Get latest PR status
            let cmd;
            if (pr.platform === 'github') {
                cmd = `gh pr view ${pr.id} --repo ${pr.repository} --json mergeable,statusCheckRollup,files`;
            } else if (pr.platform === 'gitlab') {
                cmd = `glab mr view ${pr.id} --repo ${pr.repository} --output json`;
            }
            
            if (cmd) {
                const output = execSync(cmd, { encoding: 'utf8' });
                const data = JSON.parse(output);
                
                if (pr.platform === 'github') {
                    conflictData.mergeableStatus = data.mergeable;
                    conflictData.hasConflicts = data.mergeable === 'CONFLICTING';
                    conflictData.statusChecks = data.statusCheckRollup?.state || 'unknown';
                    
                    // Try to get diff to identify conflict files
                    try {
                        const diffCmd = `gh pr diff ${pr.id} --repo ${pr.repository}`;
                        const diff = execSync(diffCmd, { encoding: 'utf8' });
                        conflictData.conflictFiles = this.extractConflictFiles(diff);
                    } catch (diffError) {
                        console.warn(`   ⚠️  Could not fetch diff: ${diffError.message}`);
                    }
                    
                } else if (pr.platform === 'gitlab') {
                    conflictData.mergeableStatus = data.merge_status;
                    conflictData.hasConflicts = data.has_conflicts || data.merge_status === 'cannot_be_merged';
                    
                    if (data.changes) {
                        conflictData.conflictFiles = data.changes.map(change => change.new_path);
                    }
                }
            }
            
            // Display status
            const statusIcon = conflictData.hasConflicts ? '❌' : 
                             conflictData.mergeableStatus === 'MERGEABLE' || conflictData.mergeableStatus === 'can_be_merged' ? '✅' : '🟡';
            console.log(`   ${statusIcon} Status: ${conflictData.mergeableStatus}`);
            
            if (conflictData.hasConflicts) {
                console.log(`   ⚠️  Conflicts detected!`);
                if (conflictData.conflictFiles.length > 0) {
                    console.log(`   📁 Affected files: ${conflictData.conflictFiles.slice(0, 3).join(', ')}${conflictData.conflictFiles.length > 3 ? '...' : ''}`);
                }
                this.conflicts.push(conflictData);
            }
            
        } catch (error) {
            console.log(`   ❌ Error checking PR: ${error.message}`);
            this.conflicts.push({
                pr: pr,
                hasConflicts: true,
                error: error.message,
                lastChecked: new Date().toISOString()
            });
        }
        
        console.log('');
    }

    extractConflictFiles(diff) {
        const files = [];
        const lines = diff.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('diff --git')) {
                const match = line.match(/diff --git a\/(.+) b\/(.+)/);
                if (match) {
                    files.push(match[2]);
                }
            } else if (line.includes('<<<<<<<') || line.includes('>>>>>>>') || line.includes('=======')) {
                // This indicates actual conflict markers in the diff
                return files; // Return files that have conflicts
            }
        }
        
        return files;
    }

    async analyzeCrossPRConflicts(prs) {
        console.log('🔄 Analyzing cross-PR conflicts...');
        
        // Group PRs by repository
        const prsByRepo = {};
        prs.forEach(pr => {
            if (!prsByRepo[pr.repository]) {
                prsByRepo[pr.repository] = [];
            }
            prsByRepo[pr.repository].push(pr);
        });
        
        // Analyze each repository
        for (const [repo, repoPRs] of Object.entries(prsByRepo)) {
            if (repoPRs.length > 1) {
                console.log(`   📁 Analyzing ${repo} (${repoPRs.length} PRs)...`);
                await this.analyzeRepositoryConflicts(repo, repoPRs);
            }
        }
        
        console.log('');
    }

    async analyzeRepositoryConflicts(repo, prs) {
        // Get file changes for each PR
        const prFiles = {};
        
        for (const pr of prs) {
            try {
                let cmd;
                if (pr.platform === 'github') {
                    cmd = `gh pr view ${pr.id} --repo ${repo} --json files`;
                } else if (pr.platform === 'gitlab') {
                    cmd = `glab mr view ${pr.id} --repo ${repo} --output json`;
                }
                
                if (cmd) {
                    const output = execSync(cmd, { encoding: 'utf8' });
                    const data = JSON.parse(output);
                    
                    if (pr.platform === 'github' && data.files) {
                        prFiles[pr.id] = data.files.map(f => f.path);
                    } else if (pr.platform === 'gitlab' && data.changes) {
                        prFiles[pr.id] = data.changes.map(c => c.new_path);
                    }
                }
            } catch (error) {
                console.warn(`     ⚠️  Could not get files for PR #${pr.id}: ${error.message}`);
                prFiles[pr.id] = [];
            }
        }
        
        // Find overlapping files
        const prIds = Object.keys(prFiles);
        for (let i = 0; i < prIds.length; i++) {
            for (let j = i + 1; j < prIds.length; j++) {
                const pr1Id = prIds[i];
                const pr2Id = prIds[j];
                const files1 = prFiles[pr1Id] || [];
                const files2 = prFiles[pr2Id] || [];
                
                const overlapping = files1.filter(file => files2.includes(file));
                
                if (overlapping.length > 0) {
                    const pr1 = prs.find(p => p.id.toString() === pr1Id);
                    const pr2 = prs.find(p => p.id.toString() === pr2Id);
                    
                    console.log(`     ⚠️  Potential conflict between PR #${pr1Id} and PR #${pr2Id}`);
                    console.log(`        Overlapping files: ${overlapping.slice(0, 3).join(', ')}${overlapping.length > 3 ? '...' : ''}`);
                    
                    this.conflicts.push({
                        type: 'cross-pr',
                        pr1: pr1,
                        pr2: pr2,
                        overlappingFiles: overlapping,
                        lastChecked: new Date().toISOString()
                    });
                }
            }
        }
    }

    displayResults() {
        console.log('📊 CONFLICT DETECTION RESULTS');
        console.log('='.repeat(60));
        
        const singlePRConflicts = this.conflicts.filter(c => c.pr && !c.type);
        const crossPRConflicts = this.conflicts.filter(c => c.type === 'cross-pr');
        
        console.log(`Total conflicts found: ${this.conflicts.length}`);
        console.log(`Single PR conflicts: ${singlePRConflicts.length}`);
        console.log(`Cross-PR conflicts: ${crossPRConflicts.length}`);
        console.log('');
        
        if (singlePRConflicts.length > 0) {
            console.log('❌ SINGLE PR CONFLICTS:');
            singlePRConflicts.forEach((conflict, index) => {
                console.log(`${index + 1}. ${conflict.pr.platform} ${conflict.pr.repository}#${conflict.pr.id}`);
                console.log(`   📝 ${conflict.pr.title}`);
                console.log(`   👤 ${conflict.pr.author}`);
                console.log(`   🔗 ${conflict.pr.url}`);
                
                if (conflict.conflictFiles && conflict.conflictFiles.length > 0) {
                    console.log(`   📁 Files: ${conflict.conflictFiles.join(', ')}`);
                }
                
                if (conflict.error) {
                    console.log(`   ❌ Error: ${conflict.error}`);
                }
                
                console.log('');
            });
        }
        
        if (crossPRConflicts.length > 0) {
            console.log('⚠️  CROSS-PR CONFLICTS:');
            crossPRConflicts.forEach((conflict, index) => {
                console.log(`${index + 1}. PR #${conflict.pr1.id} ↔ PR #${conflict.pr2.id} (${conflict.pr1.repository})`);
                console.log(`   📝 "${conflict.pr1.title}" vs "${conflict.pr2.title}"`);
                console.log(`   📁 Overlapping files (${conflict.overlappingFiles.length}): ${conflict.overlappingFiles.slice(0, 3).join(', ')}${conflict.overlappingFiles.length > 3 ? '...' : ''}`);
                console.log('');
            });
        }
        
        if (this.conflicts.length === 0) {
            console.log('✅ No conflicts detected! All PRs appear to be mergeable.');
        } else {
            console.log('💡 RECOMMENDED ACTIONS:');
            if (singlePRConflicts.length > 0) {
                console.log('   pf pr-conflict-resolve pr_id=<id>    # Resolve specific PR conflicts');
            }
            if (crossPRConflicts.length > 0) {
                console.log('   • Consider merging PRs in order of priority');
                console.log('   • Coordinate with PR authors to avoid conflicts');
                console.log('   • Use feature branches to isolate changes');
            }
        }
        
        console.log('');
    }

    saveResults() {
        const resultsDir = this.ctx.paths.conflictAnalysisDir;
        ensureDir(resultsDir);
        
        const filename = `conflict-analysis-${Date.now()}.json`;
        const filepath = path.join(resultsDir, filename);
        
        const results = {
            timestamp: new Date().toISOString(),
            totalPRs: this.prs.length,
            totalConflicts: this.conflicts.length,
            conflicts: this.conflicts
        };
        
        writeJson(filepath, results);
        console.log(`💾 Conflict analysis saved to ${filepath}`);
    }

    updatePRData() {
        // Update PR data with conflict information
        this.conflicts.forEach(conflict => {
            if (conflict.pr) {
                const prIndex = this.prs.findIndex(p => 
                    p.id === conflict.pr.id && p.repository === conflict.pr.repository
                );
                if (prIndex !== -1) {
                    this.prs[prIndex].conflicts = conflict.hasConflicts;
                    this.prs[prIndex].conflictFiles = conflict.conflictFiles || [];
                    this.prs[prIndex].lastConflictCheck = conflict.lastChecked;
                }
            }
        });
        
        // Save updated PR data
        writeJson(this.prDataPath, this.prs);
        console.log('✅ PR data updated with conflict information');
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const checkAll = args[0] !== 'false';
    
    const detector = new ConflictDetector();
    await detector.detectConflicts(checkAll);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default ConflictDetector;
