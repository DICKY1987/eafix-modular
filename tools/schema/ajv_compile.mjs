#!/usr/bin/env node
/**
 * AJV Schema Compilation and Validation Tools
 * Provides centralized schema validation for GDW specifications
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import fs from 'fs';
import path from 'path';

// Initialize AJV with strict mode and formats
const ajv = new Ajv({
  allErrors: true,
  verbose: true,
  strict: true,
  validateSchema: true
});

// Add format validation
addFormats(ajv);

// Schema paths (checking both local and project schema directories)
const SCHEMA_DIRS = ['.', '../../schema'];
const schemas = {
  gdw: 'gdw.spec.schema.json',
  chain: 'chain.spec.schema.json',
  lock: 'gdw.lock.schema.json',
  aiConfig: 'ai_workflow_config.schema.json'
};

/**
 * Find schema file in available directories
 */
function findSchema(schemaFile) {
  for (const dir of SCHEMA_DIRS) {
    const fullPath = path.join(dir, schemaFile);
    if (fs.existsSync(fullPath)) {
      return fullPath;
    }
  }
  return null;
}

/**
 * Load and compile a schema
 */
export function loadSchema(schemaPath) {
  try {
    const schemaContent = fs.readFileSync(schemaPath, 'utf8');
    const schema = JSON.parse(schemaContent);
    const validate = ajv.compile(schema);
    return { schema, validate };
  } catch (error) {
    console.error(`Failed to load schema ${schemaPath}:`, error.message);
    throw error;
  }
}

/**
 * Validate data against a schema
 */
export function validateData(data, validate, schemaName = 'unknown') {
  const valid = validate(data);

  return {
    valid,
    errors: valid ? [] : validate.errors.map(error => ({
      instancePath: error.instancePath || '',
      schemaPath: error.schemaPath || '',
      keyword: error.keyword,
      message: error.message,
      data: error.data,
      schema: error.schema
    })),
    schemaName
  };
}

/**
 * Format validation errors for display
 */
export function formatErrors(result) {
  if (result.valid) {
    return `✓ ${result.schemaName}: Valid`;
  }

  const lines = [`✗ ${result.schemaName}: Invalid`];
  result.errors.forEach((error, index) => {
    lines.push(`  ${index + 1}. Path: ${error.instancePath || '/'}`);
    lines.push(`     Rule: ${error.keyword}`);
    lines.push(`     Message: ${error.message}`);
    if (error.data !== undefined) {
      lines.push(`     Data: ${JSON.stringify(error.data)}`);
    }
    lines.push('');
  });

  return lines.join('\n');
}

// Compile all schemas when run directly
const isMainModule = process.argv[1] && import.meta.url.includes('ajv_compile.mjs');
if (isMainModule) {
  console.log('Compiling GDW schemas...');

  let successCount = 0;
  let totalCount = 0;

  for (const [name, schemaFile] of Object.entries(schemas)) {
    totalCount++;
    try {
      const schemaPath = findSchema(schemaFile);
      if (schemaPath) {
        const { schema } = loadSchema(schemaPath);
        console.log(`✓ ${name}: ${schema.title || 'Schema'} compiled successfully`);
        successCount++;
      } else {
        console.log(`⚠ ${name}: Schema file not found: ${schemaFile}`);
      }
    } catch (error) {
      console.error(`✗ ${name}: Compilation failed -`, error.message);
    }
  }

  console.log(`\nSummary: ${successCount}/${totalCount} schemas compiled successfully`);

  if (successCount === totalCount) {
    console.log('🎉 All schemas compiled successfully!');
  }
}