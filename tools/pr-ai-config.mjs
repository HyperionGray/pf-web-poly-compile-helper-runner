#!/usr/bin/env node

/**
 * PR AI Config Tool
 *
 * Writes ~/.config/pf/ai-providers.json which is consumed by pr-ai-review.mjs.
 */

import fs from 'fs';
import path from 'path';

class PRAIConfig {
    constructor() {
        this.configPath = path.join(process.env.HOME, '.config', 'pf', 'ai-providers.json');
        this.config = this.loadConfig();
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

    saveConfig() {
        const dir = path.dirname(this.configPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
    }

    parseCriteria(value) {
        if (!value) return null;
        const v = String(value).trim();
        if (!v || v.startsWith('${')) return null;

        // JSON object support
        if (v.startsWith('{') && v.endsWith('}')) {
            try {
                const obj = JSON.parse(v);
                if (obj && typeof obj === 'object') return obj;
            } catch {
                // fall through
            }
        }

        // Comma-separated enable list, e.g. "security,performance"
        const enabled = v.split(',').map(s => s.trim()).filter(Boolean);
        if (!enabled.length) return null;

        const out = { ...this.config.reviewCriteria };
        Object.keys(out).forEach(k => { out[k] = false; });
        enabled.forEach(k => { out[k] = true; });
        return out;
    }

    configure(provider, apiKey, model, reviewCriteria) {
        if (!provider || String(provider).startsWith('${')) {
            console.log('Usage: pr-ai-config.mjs <provider> <api_key> <model> <review_criteria>');
            console.log('Examples:');
            console.log('  pr-ai-config.mjs openai sk-... gpt-4 \"security,performance\"');
            console.log('  pr-ai-config.mjs anthropic ... claude-3-sonnet-20240229 \"{\\\"security\\\":true}\"');
            return;
        }

        const p = String(provider).trim().toLowerCase();
        if (!this.config.providers) this.config.providers = {};
        if (!this.config.providers[p]) this.config.providers[p] = {};

        if (apiKey && !String(apiKey).startsWith('${')) {
            this.config.providers[p].apiKey = apiKey;
        }
        if (model && !String(model).startsWith('${')) {
            this.config.providers[p].model = model;
        }

        const resolvedKey = this.config.providers[p].apiKey;
        this.config.providers[p].enabled = !!resolvedKey;

        const criteriaObj = this.parseCriteria(reviewCriteria);
        if (criteriaObj) {
            this.config.reviewCriteria = criteriaObj;
        }

        this.saveConfig();

        console.log('✅ AI configuration saved.');
        console.log(`📄 Config: ${this.configPath}`);
        console.log(`🤖 Provider: ${p} (${this.config.providers[p].enabled ? 'enabled' : 'disabled'})`);
        if (this.config.providers[p].model) {
            console.log(`🧠 Model: ${this.config.providers[p].model}`);
        }
    }
}

function main() {
    const args = process.argv.slice(2);
    const provider = args[0];
    const apiKey = args[1];
    const model = args[2];
    const reviewCriteria = args[3];

    const tool = new PRAIConfig();
    tool.configure(provider, apiKey, model, reviewCriteria);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default PRAIConfig;

