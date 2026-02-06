#!/usr/bin/env node

/**
 * PR Status Dashboard
 * Interactive dashboard showing comprehensive PR status and metrics
 */

import fs from 'fs';
import path from 'path';

class PRDashboard {
    constructor() {
        this.prDataPath = path.join(process.env.HOME, '.config', 'pf', 'discovered-prs.json');
        this.prs = this.loadPRs();
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

    calculateMetrics() {
        const total = this.prs.length;
        
        if (total === 0) {
            return {
                total: 0,
                byPlatform: {},
                byStatus: {},
                byReview: {},
                readyToMerge: 0,
                needsAttention: 0,
                aiReviewed: 0,
                hasConflicts: 0
            };
        }
        
        const metrics = {
            total,
            byPlatform: {},
            byStatus: {},
            byReview: {},
            readyToMerge: 0,
            needsAttention: 0,
            aiReviewed: 0,
            hasConflicts: 0
        };
        
        this.prs.forEach(pr => {
            // Platform breakdown
            metrics.byPlatform[pr.platform] = (metrics.byPlatform[pr.platform] || 0) + 1;
            
            // Status breakdown
            metrics.byStatus[pr.state] = (metrics.byStatus[pr.state] || 0) + 1;
            
            // Review status
            const reviewStatus = pr.reviewDecision || 'pending';
            metrics.byReview[reviewStatus] = (metrics.byReview[reviewStatus] || 0) + 1;
            
            // Ready to merge
            if (pr.mergeable && 
                (pr.reviewDecision === 'APPROVED' || pr.aiRecommendation === 'APPROVE') &&
                !pr.conflicts &&
                pr.statusChecks === 'SUCCESS') {
                metrics.readyToMerge++;
            }
            
            // Needs attention
            if (pr.conflicts || 
                pr.statusChecks === 'FAILURE' ||
                pr.reviewDecision === 'CHANGES_REQUESTED' ||
                pr.aiRecommendation === 'REQUEST_CHANGES') {
                metrics.needsAttention++;
            }
            
            // AI reviewed
            if (pr.aiReviewed) {
                metrics.aiReviewed++;
            }
            
            // Has conflicts
            if (pr.conflicts) {
                metrics.hasConflicts++;
            }
        });
        
        return metrics;
    }

    displayHeader() {
        const now = new Date().toLocaleString();
        console.log('╔' + '═'.repeat(78) + '╗');
        console.log('║' + ' '.repeat(25) + '🚀 PR MANAGEMENT DASHBOARD' + ' '.repeat(25) + '║');
        console.log('║' + ' '.repeat(78) + '║');
        console.log('║' + ` Last Updated: ${now}`.padEnd(78) + '║');
        console.log('╚' + '═'.repeat(78) + '╝');
        console.log('');
    }

    displayMetrics(metrics) {
        console.log('📊 OVERVIEW METRICS');
        console.log('─'.repeat(50));
        
        // Main stats
        console.log(`Total Pull Requests: ${metrics.total}`);
        console.log(`Ready to Merge: ${metrics.readyToMerge} (${Math.round(metrics.readyToMerge/metrics.total*100)}%)`);
        console.log(`Needs Attention: ${metrics.needsAttention} (${Math.round(metrics.needsAttention/metrics.total*100)}%)`);
        console.log(`AI Reviewed: ${metrics.aiReviewed} (${Math.round(metrics.aiReviewed/metrics.total*100)}%)`);
        console.log(`Has Conflicts: ${metrics.hasConflicts} (${Math.round(metrics.hasConflicts/metrics.total*100)}%)`);
        console.log('');
        
        // Platform breakdown
        console.log('🌐 BY PLATFORM');
        console.log('─'.repeat(30));
        Object.entries(metrics.byPlatform).forEach(([platform, count]) => {
            const percentage = Math.round(count/metrics.total*100);
            const bar = '█'.repeat(Math.floor(percentage/5));
            console.log(`${platform.padEnd(10)} ${count.toString().padStart(3)} (${percentage}%) ${bar}`);
        });
        console.log('');
        
        // Status breakdown
        console.log('📋 BY STATUS');
        console.log('─'.repeat(30));
        Object.entries(metrics.byStatus).forEach(([status, count]) => {
            const percentage = Math.round(count/metrics.total*100);
            const bar = '█'.repeat(Math.floor(percentage/5));
            const icon = status === 'open' ? '🟢' : status === 'merged' ? '✅' : '🔴';
            console.log(`${icon} ${status.padEnd(8)} ${count.toString().padStart(3)} (${percentage}%) ${bar}`);
        });
        console.log('');
        
        // Review breakdown
        console.log('👥 BY REVIEW STATUS');
        console.log('─'.repeat(30));
        Object.entries(metrics.byReview).forEach(([review, count]) => {
            const percentage = Math.round(count/metrics.total*100);
            const bar = '█'.repeat(Math.floor(percentage/5));
            const icon = review === 'APPROVED' ? '✅' : 
                       review === 'CHANGES_REQUESTED' ? '🔄' : 
                       review === 'pending' ? '⏳' : '❓';
            console.log(`${icon} ${review.padEnd(18)} ${count.toString().padStart(3)} (${percentage}%) ${bar}`);
        });
        console.log('');
    }

    displayTopPRs() {
        console.log('🔥 TOP PRIORITY PRS');
        console.log('─'.repeat(80));
        
        // Ready to merge
        const readyToMerge = this.prs.filter(pr => 
            pr.mergeable && 
            (pr.reviewDecision === 'APPROVED' || pr.aiRecommendation === 'APPROVE') &&
            !pr.conflicts &&
            pr.statusChecks === 'SUCCESS'
        ).slice(0, 5);
        
        if (readyToMerge.length > 0) {
            console.log('✅ READY TO MERGE:');
            readyToMerge.forEach((pr, index) => {
                const approvalIcon = pr.reviewDecision === 'APPROVED' ? '👥' : '🤖';
                console.log(`   ${index + 1}. ${approvalIcon} ${pr.platform} ${pr.repository}#${pr.id}: ${pr.title.substring(0, 50)}...`);
            });
            console.log('');
        }
        
        // Needs attention
        const needsAttention = this.prs.filter(pr => 
            pr.conflicts || 
            pr.statusChecks === 'FAILURE' ||
            pr.reviewDecision === 'CHANGES_REQUESTED' ||
            pr.aiRecommendation === 'REQUEST_CHANGES'
        ).slice(0, 5);
        
        if (needsAttention.length > 0) {
            console.log('⚠️  NEEDS ATTENTION:');
            needsAttention.forEach((pr, index) => {
                const issueIcon = pr.conflicts ? '🔀' : 
                                pr.statusChecks === 'FAILURE' ? '❌' : '🔄';
                console.log(`   ${index + 1}. ${issueIcon} ${pr.platform} ${pr.repository}#${pr.id}: ${pr.title.substring(0, 50)}...`);
            });
            console.log('');
        }
        
        // Pending review
        const pendingReview = this.prs.filter(pr => 
            !pr.aiReviewed && 
            (!pr.reviewDecision || pr.reviewDecision === 'REVIEW_REQUIRED') &&
            pr.state === 'open' &&
            !pr.conflicts
        ).slice(0, 5);
        
        if (pendingReview.length > 0) {
            console.log('👀 PENDING REVIEW:');
            pendingReview.forEach((pr, index) => {
                console.log(`   ${index + 1}. 🆕 ${pr.platform} ${pr.repository}#${pr.id}: ${pr.title.substring(0, 50)}...`);
            });
            console.log('');
        }
    }

    displayQuickActions(metrics) {
        console.log('⚡ QUICK ACTIONS');
        console.log('─'.repeat(50));
        
        if (metrics.readyToMerge > 0) {
            console.log(`🔀 pf pr-merge-all                    # Merge ${metrics.readyToMerge} ready PRs`);
        }
        
        const pendingReview = metrics.total - metrics.aiReviewed;
        if (pendingReview > 0) {
            console.log(`🤖 pf pr-review-all-ai                # Review ${pendingReview} pending PRs`);
        }
        
        if (metrics.hasConflicts > 0) {
            console.log(`⚠️  pf pr-conflict-detect              # Analyze ${metrics.hasConflicts} conflicted PRs`);
        }
        
        console.log('📋 pf pr-list                        # View detailed PR list');
        console.log('🔍 pf pr-discover                    # Refresh PR data');
        console.log('📊 pf pr-analytics                   # Generate detailed reports');
        console.log('');
    }

    displayRecentActivity() {
        console.log('📅 RECENT ACTIVITY');
        console.log('─'.repeat(50));
        
        // Sort by most recently updated
        const recentPRs = [...this.prs]
            .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
            .slice(0, 10);
        
        recentPRs.forEach((pr, index) => {
            const timeAgo = this.getTimeAgo(new Date(pr.updatedAt));
            const statusIcon = pr.state === 'open' ? '🟢' : 
                             pr.state === 'merged' ? '✅' : '🔴';
            console.log(`${statusIcon} ${pr.platform} ${pr.repository}#${pr.id} - ${timeAgo}`);
        });
        console.log('');
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    async displayDashboard(refreshInterval = 0) {
        const showDashboard = () => {
            // Clear screen
            console.clear();
            
            this.displayHeader();
            
            if (this.prs.length === 0) {
                console.log('❌ No PR data found.');
                console.log('Run "pf pr-discover" to discover pull requests.');
                return;
            }
            
            const metrics = this.calculateMetrics();
            
            this.displayMetrics(metrics);
            this.displayTopPRs();
            this.displayQuickActions(metrics);
            this.displayRecentActivity();
            
            if (refreshInterval > 0) {
                console.log(`🔄 Auto-refreshing every ${refreshInterval} seconds. Press Ctrl+C to exit.`);
            }
        };
        
        // Initial display
        showDashboard();
        
        // Auto-refresh if interval specified
        if (refreshInterval > 0) {
            setInterval(() => {
                // Reload data
                this.prs = this.loadPRs();
                showDashboard();
            }, refreshInterval * 1000);
        }
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const refreshInterval = parseInt(args[0]) || 0;
    
    const dashboard = new PRDashboard();
    await dashboard.displayDashboard(refreshInterval);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default PRDashboard;