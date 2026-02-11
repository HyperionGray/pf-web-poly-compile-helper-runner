#!/usr/bin/env node

/**
 * Documentation Validator for CI/CD Review
 * CLI wrapper; implementation lives in scripts/ci-cd-review/lib/documentation-validator.mjs
 */

import path from 'path';
import { fileURLToPath } from 'url';
import DocumentationValidator from './lib/documentation-validator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

if (import.meta.url === `file://${process.argv[1]}`) {
  const validator = new DocumentationValidator(path.resolve(__dirname, '../..'));
  console.log('📚 Validating documentation structure...');

  try {
    const validation = await validator.validateDocumentationStructure();
    const additional = await validator.scanAdditionalDocs();

    if (process.argv.includes('--json')) {
      console.log(JSON.stringify(validator.generateReport(validation, additional), null, 2));
    } else if (process.argv.includes('--cicd')) {
      console.log(validator.formatForCICD(validation, additional));
    } else {
      const report = validator.generateReport(validation, additional);
      console.log('\n📊 Documentation Summary:');
      console.log(`Required completion: ${report.summary.requiredCompletionRate}%`);
      console.log(`README completeness: ${report.summary.readmeCompletenessRate}%`);
      console.log(`Additional docs: ${report.summary.additionalDocsCount}`);
    }
  } catch (error) {
    console.error('❌ Error during documentation validation:', error.message);
    process.exit(1);
  }
}

export default DocumentationValidator;

