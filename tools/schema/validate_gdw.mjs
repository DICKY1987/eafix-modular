#!/usr/bin/env node
/**
 * GDW Specification Validator
 * Validates GDW spec.json files against the schema
 */

import { loadSchema, validateData, formatErrors } from './ajv_compile.mjs';
import fs from 'fs';
import path from 'path';

const SCHEMA_PATH = './gdw.spec.schema.json';

function validateGDWFile(filePath) {
  try {
    // Load schema
    const { validate } = loadSchema(SCHEMA_PATH);

    // Load GDW spec
    const specContent = fs.readFileSync(filePath, 'utf8');
    const spec = JSON.parse(specContent);

    // Validate
    const result = validateData(spec, validate, `GDW Spec (${path.basename(filePath)})`);

    return result;
  } catch (error) {
    return {
      valid: false,
      errors: [{
        instancePath: '',
        schemaPath: '',
        keyword: 'file',
        message: `Failed to process file: ${error.message}`,
        data: filePath
      }],
      schemaName: `GDW Spec (${path.basename(filePath)})`
    };
  }
}

// Command line usage
const isMainModule = process.argv[1] && import.meta.url.includes('validate_gdw.mjs');
if (isMainModule) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node validate_gdw.mjs <spec.json> [spec2.json ...]');
    console.log('       node validate_gdw.mjs --all    # Validate all GDW specs');
    process.exit(1);
  }

  let filesToValidate = [];

  if (args[0] === '--all') {
    // Find all GDW spec files
    const gdwDir = '../../gdw';
    if (fs.existsSync(gdwDir)) {
      const domains = fs.readdirSync(gdwDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);

      for (const domain of domains) {
        const domainPath = path.join(gdwDir, domain);
        const versions = fs.readdirSync(domainPath, { withFileTypes: true })
          .filter(dirent => dirent.isDirectory())
          .map(dirent => dirent.name);

        for (const version of versions) {
          const specPath = path.join(domainPath, version, 'spec.json');
          if (fs.existsSync(specPath)) {
            filesToValidate.push(specPath);
          }
        }
      }
    }
  } else {
    filesToValidate = args;
  }

  console.log(`Validating ${filesToValidate.length} GDW specifications...\\n`);

  let allValid = true;
  const results = [];

  for (const filePath of filesToValidate) {
    const result = validateGDWFile(filePath);
    results.push(result);

    console.log(formatErrors(result));

    if (!result.valid) {
      allValid = false;
    }
  }

  // Summary
  const validCount = results.filter(r => r.valid).length;
  const invalidCount = results.length - validCount;

  console.log('\\n' + '='.repeat(50));
  console.log(`Summary: ${validCount} valid, ${invalidCount} invalid`);

  if (!allValid) {
    process.exit(1);
  }
}

export { validateGDWFile };