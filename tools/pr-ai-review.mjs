#!/usr/bin/env node

/**
 * AI-Powered PR Review Tool
 * Performs automated code review using AI providers (OpenAI, Anthropic, etc.)
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

class AIReviewer {
    constructor() {
        this.configPath = path.join(process.env.HOME, '.config', 'pf', 'ai-providers.json');
        this.prDataPath = path.join(process.env.HOME, '.config', 'pf', 'discovered-prs.json');
        this.config = this.loadConfig();
        this.prs = this.loadPRs();
    }

    loadConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                return JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
            }
        } catch (error) {
            console.warn('⚠️  Could not load AI config, using defaults');
        }
        
        return {
            providers: {
                openai: {
                    apiKey: process.env.OPENAI_API_KEY,
                    model: 'gpt-4',
                    enabled: !!process.env.OPENAI_API_KEY
                },
                anthropic: {
                    apiKey: process.env.ANTHROPIC_API_KEY,
                    model: 'claude-3-sonnet-20240229',
                    enabled: !!process.env.ANTHROPIC_API_KEY
                }
            },
            reviewCriteria: {
                security: true,
                performance: true,
                maintainability: true,
                testCoverage: true,
                documentation: true
            }
        };
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

    async getPRDiff(pr) {
        console.log(`📥 Fetching diff for ${pr.platform} PR #${pr.id}...`);
        
        try {
            let cmd;
            if (pr.platform === 'github') {
                cmd = `gh pr diff ${pr.id} --repo ${pr.repository}`;
            } else if (pr.platform === 'gitlab') {
                cmd = `glab mr diff ${pr.id} --repo ${pr.repository}`;
            } else {
                throw new Error(`Unsupported platform: ${pr.platform}`);
            }
            
            const diff = execSync(cmd, { encoding: 'utf8', maxBuffer: 1024 * 1024 * 10 }); // 10MB buffer
            return diff;
        } catch (error) {
            console.error(`❌ Failed to fetch diff: ${error.message}`);
            return null;
        }
    }

    async callOpenAI(prompt, model = 'gpt-4') {
        const apiKey = this.config.providers.openai.apiKey;
        if (!apiKey) {
            throw new Error('OpenAI API key not configured');
        }

        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                messages: [
                    {
                        role: 'system',
                        content: 'You are an expert code reviewer. Analyze the provided code diff and provide constructive feedback focusing on security, performance, maintainability, and best practices.'
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                max_tokens: 2000,
                temperature: 0.1
            })
        });

        if (!response.ok) {
            throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data.choices[0].message.content;
    }

    async callAnthropic(prompt, model = 'claude-3-sonnet-20240229') {
        const apiKey = this.config.providers.anthropic.apiKey;
        if (!apiKey) {
            throw new Error('Anthropic API key not configured');
        }

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'x-api-key': apiKey,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: model,
                max_tokens: 2000,
                messages: [
                    {
                        role: 'user',
                        content: `You are an expert code reviewer. Analyze this code diff and provide constructive feedback:\n\n${prompt}`
                    }
                ]
            })
        });

        if (!response.ok) {
            throw new Error(`Anthropic API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data.content[0].text;
    }

    generateReviewPrompt(pr, diff) {
        return `
Please review this pull request:

**PR Information:**
- Title: ${pr.title}
- Author: ${pr.author}
- Repository: ${pr.repository}
- Platform: ${pr.platform}

**Code Diff:**
\`\`\`diff
${diff}
\`\`\`

**Review Criteria:**
Please evaluate the following aspects:
1. **Security**: Look for potential security vulnerabilities, input validation issues, authentication/authorization problems
2. **Performance**: Identify potential performance bottlenecks, inefficient algorithms, resource usage issues
3. **Maintainability**: Check code readability, documentation, naming conventions, code structure
4. **Testing**: Assess test coverage, test quality, edge cases
5. **Best Practices**: Verify adherence to language-specific best practices and coding standards

**Output Format:**
Please provide your review in the following JSON format:
\`\`\`json
{
  "overall_score": 1-10,
  "recommendation": "APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION",
  "summary": "Brief overall assessment",
  "issues": [
    {
      "severity": "HIGH|MEDIUM|LOW",
      "category": "security|performance|maintainability|testing|style",
      "description": "Issue description",
      "suggestion": "Suggested fix or improvement",
      "line_numbers": [1, 2, 3]
    }
  ],
  "positive_aspects": ["List of good things about this PR"],
  "suggestions": ["General improvement suggestions"]
}
\`\`\`
`;
    }

    async reviewPR(prId, provider = 'openai', model = null) {
        console.log(`🤖 Starting AI review for PR #${prId}...`);
        
        // Find the PR
        const pr = this.prs.find(p => p.id.toString() === prId.toString());
        if (!pr) {
            console.error(`❌ PR #${prId} not found. Run "pf pr-discover" first.`);
            return;
        }
        
        console.log(`📋 Reviewing: ${pr.title} by ${pr.author}`);
        
        // Get the diff
        const diff = await this.getPRDiff(pr);
        if (!diff) {
            console.error('❌ Could not fetch PR diff');
            return;
        }
        
        if (diff.length > 50000) {
            console.warn('⚠️  Large diff detected, truncating for AI review...');
            diff = diff.substring(0, 50000) + '\n\n[... diff truncated for AI review ...]';
        }
        
        // Generate review prompt
        const prompt = this.generateReviewPrompt(pr, diff);
        
        // Call AI provider
        let review;
        try {
            console.log(`🧠 Calling ${provider} for code review...`);
            
            if (provider === 'openai') {
                const selectedModel = model || this.config.providers.openai.model;
                review = await this.callOpenAI(prompt, selectedModel);
            } else if (provider === 'anthropic') {
                const selectedModel = model || this.config.providers.anthropic.model;
                review = await this.callAnthropic(prompt, selectedModel);
            } else {
                throw new Error(`Unsupported AI provider: ${provider}`);
            }
        } catch (error) {
            console.error(`❌ AI review failed: ${error.message}`);
            return;
        }
        
        // Parse and save review
        const reviewData = this.parseReview(review, pr, provider);
        this.saveReview(pr, reviewData);
        
        // Display results
        this.displayReview(reviewData);
        
        // Update PR data
        this.updatePRData(pr, reviewData);
    }

    parseReview(review, pr, provider) {
        try {
            // Extract JSON from the review
            const jsonMatch = review.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[1]);
                return {
                    ...parsed,
                    pr_id: pr.id,
                    repository: pr.repository,
                    platform: pr.platform,
                    provider: provider,
                    timestamp: new Date().toISOString(),
                    raw_review: review
                };
            }
        } catch (error) {
            console.warn('⚠️  Could not parse structured review, using raw format');
        }
        
        // Fallback to raw review
        return {
            pr_id: pr.id,
            repository: pr.repository,
            platform: pr.platform,
            provider: provider,
            timestamp: new Date().toISOString(),
            raw_review: review,
            overall_score: null,
            recommendation: 'NEEDS_DISCUSSION',
            summary: 'Raw AI review (could not parse structured format)'
        };
    }

    saveReview(pr, reviewData) {
        const reviewsDir = path.join(process.env.HOME, '.config', 'pf', 'reviews');
        if (!fs.existsSync(reviewsDir)) {
            fs.mkdirSync(reviewsDir, { recursive: true });
        }
        
        const filename = `${pr.platform}-${pr.repository.replace('/', '-')}-${pr.id}-${Date.now()}.json`;
        const filepath = path.join(reviewsDir, filename);
        
        fs.writeFileSync(filepath, JSON.stringify(reviewData, null, 2));
        console.log(`💾 Review saved to ${filepath}`);
    }

    displayReview(reviewData) {
        console.log('\n' + '='.repeat(80));
        console.log('🤖 AI CODE REVIEW RESULTS');
        console.log('='.repeat(80));
        
        if (reviewData.overall_score) {
            console.log(`📊 Overall Score: ${reviewData.overall_score}/10`);
        }
        
        if (reviewData.recommendation) {
            const icon = reviewData.recommendation === 'APPROVE' ? '✅' : 
                        reviewData.recommendation === 'REQUEST_CHANGES' ? '🔄' : '💬';
            console.log(`${icon} Recommendation: ${reviewData.recommendation}`);
        }
        
        if (reviewData.summary) {
            console.log(`📝 Summary: ${reviewData.summary}`);
        }
        
        if (reviewData.issues && reviewData.issues.length > 0) {
            console.log('\n🚨 Issues Found:');
            reviewData.issues.forEach((issue, index) => {
                const severityIcon = issue.severity === 'HIGH' ? '🔴' : 
                                   issue.severity === 'MEDIUM' ? '🟡' : '🟢';
                console.log(`\n${index + 1}. ${severityIcon} ${issue.severity} - ${issue.category.toUpperCase()}`);
                console.log(`   Description: ${issue.description}`);
                if (issue.suggestion) {
                    console.log(`   Suggestion: ${issue.suggestion}`);
                }
                if (issue.line_numbers && issue.line_numbers.length > 0) {
                    console.log(`   Lines: ${issue.line_numbers.join(', ')}`);
                }
            });
        }
        
        if (reviewData.positive_aspects && reviewData.positive_aspects.length > 0) {
            console.log('\n✅ Positive Aspects:');
            reviewData.positive_aspects.forEach(aspect => {
                console.log(`   • ${aspect}`);
            });
        }
        
        if (reviewData.suggestions && reviewData.suggestions.length > 0) {
            console.log('\n💡 General Suggestions:');
            reviewData.suggestions.forEach(suggestion => {
                console.log(`   • ${suggestion}`);
            });
        }
        
        console.log('\n' + '='.repeat(80));
    }

    updatePRData(pr, reviewData) {
        // Update the PR in our local data
        const prIndex = this.prs.findIndex(p => p.id === pr.id && p.repository === pr.repository);
        if (prIndex !== -1) {
            this.prs[prIndex].aiReviewed = true;
            this.prs[prIndex].aiRecommendation = reviewData.recommendation;
            this.prs[prIndex].aiScore = reviewData.overall_score;
            this.prs[prIndex].lastAiReview = reviewData.timestamp;
            
            // Save updated PR data
            fs.writeFileSync(this.prDataPath, JSON.stringify(this.prs, null, 2));
            console.log('✅ PR data updated with AI review results');
        }
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const prId = args[0];
    const provider = args[1] || 'openai';
    const model = args[2] || null;
    
    if (!prId) {
        console.error('❌ Please specify a PR ID');
        console.log('Usage: pf pr-review-ai pr_id=123 [provider=openai|anthropic] [model=gpt-4]');
        return;
    }
    
    const reviewer = new AIReviewer();
    await reviewer.reviewPR(prId, provider, model);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default AIReviewer;