const fs = require('fs');
const path = require('path');

const MIGRATIONS_DIR = path.join(__dirname, '..', 'migrations');

// List of destructive operations to check for (case-insensitive, regexes)
const DESTRUCTIVE_PATTERNS = [
  /\bDROP\s+(?:COLUMN|TABLE|INDEX|VIEW|FUNCTION|SCHEMA|TYPE|SEQUENCE)\b/i,
  /\bTRUNCATE\b/i,
  /\bALTER\s+TABLE\s+\S+\s+DROP\s+(?:COLUMN|CONSTRAINT)\b/i,
  /\bALTER\s+(?:COLUMN|TABLE)\s+\S+\s+(?:DROP|RENAME|SET\s+NOT\s+NULL|DROP\s+NOT\s+NULL|SET\s+DATA\s+TYPE)\b/i,
];

const MIGRATION_FILES = fs.readdirSync(MIGRATIONS_DIR)
  .filter(f => f.endsWith('.js'))
  .sort();

const timestamps = new Map();
for (const file of MIGRATION_FILES) {
  const match = /^(\d+)_/.exec(file);
  if (!match) {
    console.error(`❌ Migration filename must start with a numeric timestamp: ${file}`);
    process.exitCode = 1;
    continue;
  }
  const previousFile = timestamps.get(match[1]);
  if (previousFile) {
    console.error(`❌ Duplicate migration timestamp ${match[1]}: ${previousFile}, ${file}`);
    process.exitCode = 1;
  } else {
    timestamps.set(match[1], file);
  }
}

console.log('🔍 Checking migrations for destructive operations...');

const destructiveMigrations = [];
const destructiveOperations = [];

for (const file of MIGRATION_FILES) {
  const filePath = path.join(MIGRATIONS_DIR, file);
  const content = fs.readFileSync(filePath, 'utf8');

  const matches = [];
  for (const pattern of DESTRUCTIVE_PATTERNS) {
    const regex = new RegExp(pattern.source, 'gi');
    let match;
    while ((match = regex.exec(content)) !== null) {
      matches.push(match[0]);
    }
  }

  if (matches.length > 0) {
    destructiveMigrations.push(file);
    destructiveOperations.push({ file, matches });
  }
}

if (destructiveMigrations.length > 0) {
  console.error('\n❌ Found potentially destructive operations in:');
  for (const op of destructiveOperations) {
    console.error(`\n📄 ${op.file}`);
    for (const match of op.matches) {
      console.error(`   ⚠️ ${match}`);
    }
  }
} else {
  console.log('\n✅ No destructive operations detected!');
}

// Dry run support: if --dry-run flag is passed, show what migrations would run
if (process.argv.includes('--dry-run')) {
  console.log('\n📋 Migration dry run plan:');
  for (const file of MIGRATION_FILES) {
    console.log(`  → ${file}`);
  }
}

// Fail if destructive operations found and we're in strict mode
const isStrict = process.env.MIGRATION_CHECK_STRICT === 'true';
if (destructiveMigrations.length > 0 && isStrict) {
  console.error('\n❌ Strict mode enabled. Destructive operations not allowed.');
  process.exit(1);
}
