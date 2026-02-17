#!/usr/bin/env node

/**
 * PR List Tool
 * Lists discovered pull requests with filtering and formatting options
 */

import fs from 'fs';
import path from 'path';

import { loadPrContext } from './pr-common.mjs';

class PRList {
    constructor() {
        this.ctx = loadPrContext();
        this.configPath = this.ctx.paths.discoveredPrsFile;
        this.prs = this.loadPRs();
    }

    loadPRs() {
        try {
            if (fs.existsSync(this.configPath)) {
                return JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
            }
        } catch (error) {
            console.error('❌ Failed to load PR data:', error.message);
        }
        
        return [];
    }

    filterPRs(filter) {
        switch (filter) {
            case 'mergeable':
                return this.prs.filter(pr => pr.mergeable);
            case 'needs-review':
                return this.prs.filter(pr => !pr.reviewDecision || pr.reviewDecision === 'REVIEW_REQUIRED');
            case 'approved':
                return this.prs.filter(pr => pr.reviewDecision === 'APPROVED');
            case 'conflicts':
                return this.prs.filter(pr => pr.conflicts);
            case 'ai-reviewed':
                return this.prs.filter(pr => pr.aiReviewed);
            case 'ready-to-merge':
                return this.prs.filter(pr => 
                    pr.mergeable && 
                    (pr.reviewDecision === 'APPROVED' || pr.aiReviewed) &&
                    !pr.conflicts &&
                    pr.statusChecks === 'SUCCESS'
                );
            case 'github':
                return this.prs.filter(pr => pr.platform === 'github');
            case 'gitlab':
                return this.prs.filter(pr => pr.platform === 'gitlab');
            default:
                return this.prs;
        }
    }

    formatTable(prs) {
        if (prs.length === 0) {
            console.log('📭 No pull requests found matching the filter criteria.');
            return;
        }

        console.log('\n📋 Pull Requests:\n');
        
        // Header
        const header = '| Platform | Repo | ID | Title | Author | Status | Mergeable | Review | Conflicts |';
        const separator = '|----------|------|----|----|--------|--------|-----------|--------|-----------|';
        
        console.log(header);
        console.log(separator);
        
        // Rows
        prs.forEach(pr => {
            const platform = pr.platform.padEnd(8);
            const repo = this.truncate(pr.repository, 12);
            const id = pr.id.toString().padEnd(4);
            const title = this.truncate(pr.title, 30);
            const author = this.truncate(pr.author, 12);
            const status = this.getStatusIcon(pr);
            const mergeable = pr.mergeable ? '✅' : '❌';
            const review = this.getReviewIcon(pr);
            const conflicts = pr.conflicts ? '⚠️' : '✅';
            
            console.log(`| ${platform} | ${repo} | ${id} | ${title} | ${author} | ${status} | ${mergeable} | ${review} | ${conflicts} |`);
        });
        
        console.log(`\nTotal: ${prs.length} PRs`);
    }

    formatJson(prs) {
        console.log(JSON.stringify(prs, null, 2));
    }

    formatCompact(prs) {
        if (prs.length === 0) {
            console.log('📭 No pull requests found.');
            return;
        }

        console.log('\n📋 Pull Requests (Compact View):\n');
        
        prs.forEach((pr, index) => {
            const status = this.getStatusIcon(pr);
            const review = this.getReviewIcon(pr);
            const mergeable = pr.mergeable ? '✅' : '❌';
            const conflicts = pr.conflicts ? '⚠️' : '';
            
            console.log(`${index + 1}. [${pr.platform.toUpperCase()}] ${pr.repository}#${pr.id}`);
            console.log(`   📝 ${pr.title}`);
            console.log(`   👤 ${pr.author} | ${status} ${mergeable} ${review} ${conflicts}`);
            console.log(`   🔗 ${pr.url}`);
            console.log('');
        });
    }

    formatDetailed(prs) {
        if (prs.length === 0) {
            console.log('📭 No pull requests found.');
            return;
        }

        console.log('\n📋 Pull Requests (Detailed View):\n');
        
        prs.forEach((pr, index) => {
            console.log(`${'='.repeat(80)}`);
            console.log(`PR #${index + 1}: ${pr.platform.toUpperCase()} ${pr.repository}#${pr.id}`);
            console.log(`${'='.repeat(80)}`);
            console.log(`📝 Title: ${pr.title}`);
            console.log(`👤 Author: ${pr.author}`);
            console.log(`🔗 URL: ${pr.url}`);
            console.log(`📅 Created: ${new Date(pr.createdAt).toLocaleDateString()}`);
            console.log(`📅 Updated: ${new Date(pr.updatedAt).toLocaleDateString()}`);
            console.log(`📊 State: ${pr.state}`);
            console.log(`🔀 Mergeable: ${pr.mergeable ? '✅ Yes' : '❌ No'}`);
            console.log(`👥 Review Decision: ${pr.reviewDecision || 'Pending'}`);
            console.log(`✅ Status Checks: ${pr.statusChecks}`);
            console.log(`⚠️  Conflicts: ${pr.conflicts ? '❌ Yes' : '✅ No'}`);
            console.log(`🤖 AI Reviewed: ${pr.aiReviewed ? '✅ Yes' : '❌ No'}`);
            console.log('');
        });
    }

    getStatusIcon(pr) {
        if (pr.statusChecks === 'SUCCESS') return '✅';
        if (pr.statusChecks === 'FAILURE') return '❌';
        if (pr.statusChecks === 'PENDING') return '🟡';
        return '❓';
    }

    getReviewIcon(pr) {
        if (pr.aiReviewed) return '🤖';
        if (pr.reviewDecision === 'APPROVED') return '✅';
        if (pr.reviewDecision === 'CHANGES_REQUESTED') return '🔄';
        if (pr.reviewDecision === 'REVIEW_REQUIRED') return '👀';
        return '❓';
    }

    truncate(str, maxLength) {
        if (str.length <= maxLength) {
            return str.padEnd(maxLength);
        }
        return str.substring(0, maxLength - 3) + '...';
    }

    displayStats(prs) {
        console.log('\n📊 Statistics:');
        
        const stats = {
            total: prs.length,
            mergeable: prs.filter(pr => pr.mergeable).length,
            needsReview: prs.filter(pr => !pr.reviewDecision || pr.reviewDecision === 'REVIEW_REQUIRED').length,
            approved: prs.filter(pr => pr.reviewDecision === 'APPROVED').length,
            conflicts: prs.filter(pr => pr.conflicts).length,
            aiReviewed: prs.filter(pr => pr.aiReviewed).length,
            readyToMerge: prs.filter(pr => 
                pr.mergeable && 
                (pr.reviewDecision === 'APPROVED' || pr.aiReviewed) &&
                !pr.conflicts &&
                pr.statusChecks === 'SUCCESS'
            ).length
        };
        
        console.log(`Total PRs: ${stats.total}`);
        console.log(`Mergeable: ${stats.mergeable} (${Math.round(stats.mergeable/stats.total*100)}%)`);
        console.log(`Needs Review: ${stats.needsReview} (${Math.round(stats.needsReview/stats.total*100)}%)`);
        console.log(`Approved: ${stats.approved} (${Math.round(stats.approved/stats.total*100)}%)`);
        console.log(`Has Conflicts: ${stats.conflicts} (${Math.round(stats.conflicts/stats.total*100)}%)`);
        console.log(`AI Reviewed: ${stats.aiReviewed} (${Math.round(stats.aiReviewed/stats.total*100)}%)`);
        console.log(`Ready to Merge: ${stats.readyToMerge} (${Math.round(stats.readyToMerge/stats.total*100)}%)`);
        
        if (stats.readyToMerge > 0) {
            console.log('\n💡 Suggested actions:');
            console.log(`  pf pr-merge-all                # Merge ${stats.readyToMerge} ready PRs`);
        }
        
        if (stats.needsReview > 0) {
            console.log(`  pf pr-review-all-ai            # AI review ${stats.needsReview} pending PRs`);
        }
        
        if (stats.conflicts > 0) {
            console.log(`  pf pr-conflict-detect          # Analyze ${stats.conflicts} conflicted PRs`);
        }
    }

    list(filter = 'all', format = 'table') {
        console.log('📋 Loading pull request data...\n');
        
        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first to discover pull requests.');
            return;
        }
        
        const filteredPRs = this.filterPRs(filter);
        
        console.log(`Filter: ${filter} | Format: ${format}`);
        
        switch (format) {
            case 'json':
                this.formatJson(filteredPRs);
                break;
            case 'compact':
                this.formatCompact(filteredPRs);
                break;
            case 'detailed':
                this.formatDetailed(filteredPRs);
                break;
            case 'table':
            default:
                this.formatTable(filteredPRs);
                break;
        }
        
        if (format !== 'json') {
            this.displayStats(filteredPRs);
        }
    }
}

// Main execution
function main() {
    const args = process.argv.slice(2);
    const filter = args[0] || 'all';
    const format = args[1] || 'table';
    
    const prList = new PRList();
    prList.list(filter, format);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default PRList;
