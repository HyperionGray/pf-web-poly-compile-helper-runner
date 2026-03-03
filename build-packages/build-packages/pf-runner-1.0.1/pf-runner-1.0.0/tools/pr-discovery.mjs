#!/usr/bin/env node

/**
 * PR Discovery Tool
 * Discovers open pull requests across GitHub and GitLab repositories
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

class PRDiscovery {
    constructor() {
        this.configPath = path.join(process.env.HOME, '.config', 'pf', 'pr-config.json');
        this.config = this.loadConfig();
        this.results = [];
    }

    loadConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                return JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
            }
        } catch (error) {
            console.warn('⚠️  Could not load PR config, using defaults');
        }
        
        return {
            repositories: [],
            platforms: {
                github: { enabled: true },
                gitlab: { enabled: true }
            },
            filters: {
                states: ['open'],
                labels: [],
                authors: []
            }
        };
    }

    async discoverGitHubPRs(repo) {
        console.log(`🔍 Discovering GitHub PRs for ${repo}...`);
        
        try {
            // Check if gh CLI is authenticated
            execSync('gh auth status', { stdio: 'pipe' });
            
            const cmd = `gh pr list --repo ${repo} --json number,title,author,createdAt,updatedAt,url,state,mergeable,reviewDecision,statusCheckRollup`;
            const output = execSync(cmd, { encoding: 'utf8' });
            const prs = JSON.parse(output);
            
            return prs.map(pr => ({
                platform: 'github',
                repository: repo,
                id: pr.number,
                title: pr.title,
                author: pr.author.login,
                url: pr.url,
                state: pr.state,
                mergeable: pr.mergeable,
                reviewDecision: pr.reviewDecision,
                statusChecks: pr.statusCheckRollup?.state || 'unknown',
                createdAt: pr.createdAt,
                updatedAt: pr.updatedAt,
                aiReviewed: false,
                conflicts: false
            }));
        } catch (error) {
            console.error(`❌ Failed to discover GitHub PRs for ${repo}: ${error.message}`);
            return [];
        }
    }

    async discoverGitLabPRs(repo) {
        console.log(`🔍 Discovering GitLab MRs for ${repo}...`);
        
        try {
            // Check if glab CLI is configured
            execSync('glab auth status', { stdio: 'pipe' });
            
            const cmd = `glab mr list --repo ${repo} --output json`;
            const output = execSync(cmd, { encoding: 'utf8' });
            const mrs = JSON.parse(output);
            
            return mrs.map(mr => ({
                platform: 'gitlab',
                repository: repo,
                id: mr.iid,
                title: mr.title,
                author: mr.author.username,
                url: mr.web_url,
                state: mr.state,
                mergeable: mr.merge_status === 'can_be_merged',
                reviewDecision: mr.merge_status,
                statusChecks: mr.detailed_merge_status || 'unknown',
                createdAt: mr.created_at,
                updatedAt: mr.updated_at,
                aiReviewed: false,
                conflicts: mr.has_conflicts || false
            }));
        } catch (error) {
            console.error(`❌ Failed to discover GitLab MRs for ${repo}: ${error.message}`);
            return [];
        }
    }

    async discoverCurrentRepo() {
        try {
            // Get current repository info
            const remoteUrl = execSync('git remote get-url origin', { encoding: 'utf8' }).trim();
            
            let repo, platform;
            // Use strict regex patterns to match only legitimate domain URLs
            // Matches: git@github.com:, https://github.com/, ssh://git@github.com/
            const githubMatch = remoteUrl.match(/^(?:git@|https?:\/\/|ssh:\/\/(?:git@)?)github\.com[:/]([^/]+\/[^/]+?)(?:\.git)?$/);
            const gitlabMatch = remoteUrl.match(/^(?:git@|https?:\/\/|ssh:\/\/(?:git@)?)gitlab\.com[:/]([^/]+\/[^/]+?)(?:\.git)?$/);
            
            if (githubMatch) {
                platform = 'github';
                repo = githubMatch[1];
            } else if (gitlabMatch) {
                platform = 'gitlab';
                repo = gitlabMatch[1];
            }
            
            if (repo && platform) {
                console.log(`📍 Detected current repository: ${repo} (${platform})`);
                return { repo, platform };
            }
        } catch (error) {
            console.log('ℹ️  Not in a git repository or no remote configured');
        }
        
        return null;
    }

    async discover(targetRepo = null, targetPlatform = 'auto') {
        console.log('🚀 Starting PR discovery...\n');
        
        let repositories = [];
        
        if (targetRepo) {
            // Specific repository provided
            repositories.push({ repo: targetRepo, platform: targetPlatform });
        } else {
            // Use current repo if available
            const currentRepo = await this.discoverCurrentRepo();
            if (currentRepo) {
                repositories.push(currentRepo);
            }
            
            // Add configured repositories
            repositories.push(...this.config.repositories);
        }
        
        if (repositories.length === 0) {
            console.log('❌ No repositories configured. Please specify a repository or configure defaults.');
            console.log('Example: pf pr-discover repo=owner/repository');
            return;
        }
        
        // Discover PRs from all repositories
        for (const { repo, platform } of repositories) {
            let prs = [];
            
            if (platform === 'github' || platform === 'auto') {
                prs.push(...await this.discoverGitHubPRs(repo));
            }
            
            if (platform === 'gitlab' || platform === 'auto') {
                prs.push(...await this.discoverGitLabPRs(repo));
            }
            
            this.results.push(...prs);
        }
        
        // Save results
        this.saveResults();
        
        // Display summary
        this.displaySummary();
    }

    saveResults() {
        const outputDir = path.join(process.env.HOME, '.config', 'pf');
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        const outputFile = path.join(outputDir, 'discovered-prs.json');
        fs.writeFileSync(outputFile, JSON.stringify(this.results, null, 2));
        console.log(`💾 Results saved to ${outputFile}`);
    }

    displaySummary() {
        console.log('\n📊 Discovery Summary:');
        console.log(`Total PRs found: ${this.results.length}`);
        
        const byPlatform = this.results.reduce((acc, pr) => {
            acc[pr.platform] = (acc[pr.platform] || 0) + 1;
            return acc;
        }, {});
        
        Object.entries(byPlatform).forEach(([platform, count]) => {
            console.log(`  ${platform}: ${count} PRs`);
        });
        
        const mergeable = this.results.filter(pr => pr.mergeable).length;
        const needsReview = this.results.filter(pr => !pr.reviewDecision || pr.reviewDecision === 'REVIEW_REQUIRED').length;
        const hasConflicts = this.results.filter(pr => pr.conflicts).length;
        
        console.log(`\n📈 Status Breakdown:`);
        console.log(`  Mergeable: ${mergeable}`);
        console.log(`  Needs Review: ${needsReview}`);
        console.log(`  Has Conflicts: ${hasConflicts}`);
        
        if (this.results.length > 0) {
            console.log('\n💡 Next steps:');
            console.log('  pf pr-list                    # View detailed PR list');
            console.log('  pf pr-review-all-ai          # Run AI review on all PRs');
            console.log('  pf pr-status-dashboard       # Open interactive dashboard');
        }
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const repo = args[0] || null;
    const platform = args[1] || 'auto';
    
    const discovery = new PRDiscovery();
    await discovery.discover(repo, platform);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default PRDiscovery;