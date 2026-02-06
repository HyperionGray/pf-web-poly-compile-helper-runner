#!/usr/bin/env node

/**
 * Batch AI Review Tool
 * Runs AI reviews on multiple PRs concurrently
 */

import fs from 'fs';
import path from 'path';
import AIReviewer from './pr-ai-review.mjs';

import { ensureDir, loadPrContext, writeJson } from './pr-common.mjs';

class BatchAIReviewer {
    constructor() {
        this.ctx = loadPrContext();
        this.prDataPath = this.ctx.paths.discoveredPrsFile;
        this.prs = this.loadPRs();
        this.reviewer = new AIReviewer();
        this.results = [];
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

    filterPRsForReview() {
        return this.prs.filter(pr => {
            // Only review open PRs
            if (pr.state !== 'open') return false;
            
            // Skip if already AI reviewed recently (within 24 hours)
            if (pr.aiReviewed && pr.lastAiReview) {
                const lastReview = new Date(pr.lastAiReview);
                const now = new Date();
                const hoursSinceReview = (now - lastReview) / (1000 * 60 * 60);
                if (hoursSinceReview < 24) return false;
            }
            
            // Skip if has conflicts (should be resolved first)
            if (pr.conflicts) return false;
            
            return true;
        });
    }

    async reviewPRBatch(provider = 'openai', model = null, maxConcurrent = 3) {
        console.log('🤖 Starting batch AI review process...\n');
        
        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }
        
        const prsToReview = this.filterPRsForReview();
        
        console.log(`📊 Review Analysis:`);
        console.log(`   Total PRs: ${this.prs.length}`);
        console.log(`   Need review: ${prsToReview.length}`);
        console.log(`   AI Provider: ${provider}`);
        console.log(`   Model: ${model || 'default'}`);
        console.log(`   Max concurrent: ${maxConcurrent}`);
        console.log('');
        
        if (prsToReview.length === 0) {
            console.log('✅ All PRs are up to date with AI reviews.');
            return;
        }
        
        // Display PRs to be reviewed
        console.log('📋 PRs to be reviewed:');
        prsToReview.forEach((pr, index) => {
            const statusIcon = pr.aiReviewed ? '🔄' : '🆕';
            console.log(`${index + 1}. ${statusIcon} ${pr.platform} ${pr.repository}#${pr.id}: ${pr.title}`);
        });
        console.log('');
        
        // Process PRs in batches
        const batches = this.createBatches(prsToReview, maxConcurrent);
        
        for (let i = 0; i < batches.length; i++) {
            const batch = batches[i];
            console.log(`🔄 Processing batch ${i + 1}/${batches.length} (${batch.length} PRs)...`);
            
            // Process batch concurrently
            const batchPromises = batch.map(pr => this.reviewSinglePR(pr, provider, model));
            const batchResults = await Promise.allSettled(batchPromises);
            
            // Collect results
            batchResults.forEach((result, index) => {
                const pr = batch[index];
                if (result.status === 'fulfilled') {
                    this.results.push({
                        success: true,
                        pr: pr,
                        result: result.value,
                        timestamp: new Date().toISOString()
                    });
                    console.log(`   ✅ Completed review for PR #${pr.id}`);
                } else {
                    this.results.push({
                        success: false,
                        pr: pr,
                        error: result.reason?.message || 'Unknown error',
                        timestamp: new Date().toISOString()
                    });
                    console.log(`   ❌ Failed review for PR #${pr.id}: ${result.reason?.message}`);
                }
            });
            
            // Delay between batches to respect rate limits
            if (i < batches.length - 1) {
                console.log('   ⏳ Waiting before next batch...');
                await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second delay
            }
        }
        
        // Display summary
        this.displayBatchSummary();
        this.saveBatchResults();
    }

    createBatches(items, batchSize) {
        const batches = [];
        for (let i = 0; i < items.length; i += batchSize) {
            batches.push(items.slice(i, i + batchSize));
        }
        return batches;
    }

    async reviewSinglePR(pr, provider, model) {
        try {
            // Use the existing reviewer but capture the result
            await this.reviewer.reviewPR(pr.id, provider, model);
            return { success: true };
        } catch (error) {
            throw error;
        }
    }

    displayBatchSummary() {
        const successful = this.results.filter(r => r.success).length;
        const failed = this.results.filter(r => !r.success).length;
        
        console.log('\n' + '='.repeat(60));
        console.log('🤖 BATCH AI REVIEW SUMMARY');
        console.log('='.repeat(60));
        console.log(`✅ Successful reviews: ${successful}`);
        console.log(`❌ Failed reviews: ${failed}`);
        console.log(`📊 Total processed: ${this.results.length}`);
        
        if (failed > 0) {
            console.log('\n❌ Failed reviews:');
            this.results.filter(r => !r.success).forEach(result => {
                console.log(`   • PR #${result.pr.id} (${result.pr.repository}): ${result.error}`);
            });
        }
        
        if (successful > 0) {
            console.log('\n✅ Successfully reviewed:');
            this.results.filter(r => r.success).forEach(result => {
                console.log(`   • PR #${result.pr.id} (${result.pr.repository}): ${result.pr.title}`);
            });
        }
        
        console.log('\n💡 Next steps:');
        console.log('   pf pr-list                   # View updated PR list with AI reviews');
        console.log('   pf pr-merge-all              # Merge approved PRs');
        console.log('   pf pr-status-dashboard       # View comprehensive status');
    }

    saveBatchResults() {
        const resultsDir = this.ctx.paths.batchReviewsDir;
        ensureDir(resultsDir);
        
        const filename = `batch-review-${Date.now()}.json`;
        const filepath = path.join(resultsDir, filename);
        
        writeJson(filepath, this.results);
        console.log(`\n💾 Batch review results saved to ${filepath}`);
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const provider = args[0] || 'openai';
    const model = args[1] || null;
    const maxConcurrent = parseInt(args[2]) || 3;
    
    const batchReviewer = new BatchAIReviewer();
    await batchReviewer.reviewPRBatch(provider, model, maxConcurrent);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default BatchAIReviewer;
