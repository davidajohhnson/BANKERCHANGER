Run `npm run openapi:generate` from `backend/`, then `npm run openapi:validate`.
Commit the generated `backend/openapi.yaml` with annotation changes. CI regenerates,
validates, and checks that the committed output is current.

`openapi-base.yaml` preserves the curated API contracts and shared schemas.
`swagger-jsdoc` extracts annotations from every TypeScript file in `src/routes/`;
new paths and operations extend the curated contracts. For overlapping operations,
the curated contract takes precedence. Update that source when changing an existing
contract. Root operation annotations live in `operations.routes.ts`.

Legacy annotations without status documentation receive a descriptive default
response. Numeric exclusive minima are normalized to OpenAPI 3.0 boolean syntax;
path parameters omitted by legacy annotations are included as required strings.
These defaults do not replace endpoint-specific request/response schemas.

The real PostgreSQL rollback and 50-request betting test runs with
`BET_LOAD_DATABASE_URL=postgresql://... npm test -- --runInBand tests/integration/betPostgresConcurrency.test.ts`.
It creates and removes its own isolated schema. Backend CI supplies this variable
using its disposable PostgreSQL service; without it, only this database test skips.
