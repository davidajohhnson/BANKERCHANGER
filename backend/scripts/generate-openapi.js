const fs = require('fs');
const path = require('path');
const swaggerJsdoc = require('swagger-jsdoc');
const YAML = require('yaml');

// Preserve the curated schemas and deployed route contracts while extracting
// newer route annotations. The committed output is reproducible in CI.
const root = path.resolve(__dirname, '..');
const document = YAML.parseDocument(fs.readFileSync(path.join(__dirname, 'openapi-base.yaml'), 'utf8'));
const definition = document.toJS();
const originalPaths = JSON.parse(JSON.stringify(definition.paths));
const extracted = swaggerJsdoc({
  definition: { openapi: definition.openapi, info: definition.info },
  apis: [path.join(root, 'src/routes/*.ts')],
  failOnErrors: true,
});
for (const [route, operations] of Object.entries(extracted.paths || {})) {
  definition.paths[route] = { ...operations, ...definition.paths[route] };
}
// Normalize legacy annotations to the OpenAPI 3.0 schema dialect.
function normalize(value) {
  if (!value || typeof value !== 'object') return;
  if (typeof value.exclusiveMinimum === 'number') {
    value.minimum = value.exclusiveMinimum;
    value.exclusiveMinimum = true;
  }
  for (const child of Object.values(value)) normalize(child);
}
for (const [route, item] of Object.entries(definition.paths)) {
  for (const method of ['get', 'post', 'put', 'patch', 'delete']) {
    const operation = item[method];
    if (!operation) continue;
    operation.responses ||= {
      default: {
        description:
          'Endpoint response; see the route implementation for status-specific behavior.',
      },
    };
    if (!route.includes('{')) continue;
    operation.parameters ||= [];
    for (const match of route.matchAll(/\{([^}]+)\}/g)) {
      if (
        !operation.parameters.some(
          (parameter) => parameter.in === 'path' && parameter.name === match[1]
        )
      ) {
        operation.parameters.push({
          in: 'path',
          name: match[1],
          required: true,
          schema: { type: 'string' },
        });
      }
    }
  }
}
normalize(definition);
definition.paths['/wallet/withdraw'] = definition.paths['/api/v1/wallets/withdraw'];
const tags = new Map((definition.tags || []).map((tag) => [tag.name, tag]));
for (const tag of extracted.tags || []) tags.set(tag.name, tag);
definition.tags = [...tags.values()];
for (const [route, item] of Object.entries(definition.paths)) {
  if (JSON.stringify(item) !== JSON.stringify(originalPaths[route])) document.setIn(['paths', route], item);
}
document.set('tags', definition.tags);
fs.writeFileSync(path.join(root, 'openapi.yaml'), document.toString({ lineWidth: 0 }));
