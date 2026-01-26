#!/usr/bin/env node

/**
 * PR Webhook Setup Tool
 *
 * Stores webhook configuration for downstream automation.
 * Actual webhook registration is platform-dependent (GitHub/GitLab) and
 * requires credentials + repository access, so this script focuses on
 * configuration and safe guidance.
 */

import fs from 'fs';
import path from 'path';

class PRWebhookSetup {
    constructor() {
        this.configPath = path.join(process.env.HOME, '.config', 'pf', 'pr-config.json');
        this.config = this.loadConfig();
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
            },
            webhooks: []
        };
    }

    saveConfig() {
        const dir = path.dirname(this.configPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
    }

    setup(endpointUrl, secret) {
        if (!endpointUrl || !secret) {
            console.log('Usage: pr-webhook-setup.mjs <endpoint_url> <secret>');
            console.log('Example: pr-webhook-setup.mjs https://example.com/pf/webhook mysecret');
            return;
        }

        if (!Array.isArray(this.config.webhooks)) {
            this.config.webhooks = [];
        }

        const entry = {
            endpointUrl,
            secret,
            createdAt: new Date().toISOString()
        };

        this.config.webhooks.push(entry);
        this.saveConfig();

        console.log('✅ Webhook configuration saved.');
        console.log(`📄 Config: ${this.configPath}`);
        console.log('');
        console.log('Next steps (manual registration):');
        console.log('  - GitHub: Settings → Webhooks → Add webhook');
        console.log('  - GitLab: Settings → Webhooks → Add new webhook');
        console.log('');
        console.log('Tip: keep the secret private and rotate it regularly.');
    }
}

function main() {
    const args = process.argv.slice(2);
    const endpointUrl = args[0];
    const secret = args[1];

    const setup = new PRWebhookSetup();
    setup.setup(endpointUrl, secret);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default PRWebhookSetup;

