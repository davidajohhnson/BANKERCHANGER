# BANKERCHANGER - 125 Repository Issues & Action Items

Comprehensive task backlog covering every component of the repository: Smart Contracts, Backend API, Blockchain Indexer, Frontend UI/UX, Treasury & Governance, and DevOps / CI/CD.

A significant portion of these issues directly address critical bugs, compilation failures, security vulnerabilities, and stability fixes necessary to make the repository production-ready.

---

## Issue #1: [Contracts] Fix #[contracterror] macro LengthExceedsMax panic in shared/src/errors.rs

**Labels**: `blockchain, bug, security`

### Context & Problem
Soroban SDK's `#[contracterror]` macro panics with `called Result::unwrap() on an Err value: LengthExceedsMax` in `contracts/shared/src/errors.rs`. This completely breaks compilation of `boxmeout-shared` and dependent contracts.

### Proposed Solution
1. Inspect variant identifiers and string lengths in `contracts/shared/src/errors.rs`.
2. Consolidate error variants or group error domains (auth, market, treasury, math) to satisfy Soroban SDK macro constraints.
3. Ensure no discriminant exceeds `u32` limits and variant names are concise.

### Acceptance Criteria
- `cargo check --manifest-path contracts/Cargo.toml` compiles successfully without macro panics.
- Error codes remain uniquely mapped and documented.

---

## Issue #2: [Contracts] Fix reentrancy and Checks-Effects-Interactions violations in share redemption

**Labels**: `blockchain, security, bug`

### Context & Problem
In `contracts/market/src/lib.rs`, token transfer to the winning bettor occurs before deducting the user's winning outcome shares balance from contract storage, violating the Checks-Effects-Interactions (CEI) pattern.

### Proposed Solution
1. Update user state and pool reserves before executing `token::Client::transfer`.
2. Add reentrancy guard or ensure strict CEI ordering across `claim_winnings` and `redeem_shares`.

### Acceptance Criteria
- Storage mutations are finalized prior to external token transfers.
- Unit tests verify reentrancy revert behavior.

---

## Issue #3: [Contracts] Fix integer rounding down to zero in CPMM outcome token pricing

**Labels**: `blockchain, trading, bug`

### Context & Problem
During share pricing calculations in low-liquidity markets, integer division in `contracts/shared/src/math.rs` truncates remainders, resulting in 0 price output and allowing zero-cost share acquisition.

### Proposed Solution
1. Implement fixed-point scaling factor (e.g. 10^7 or 10^9 precision) before performing division in AMM price formula.
2. Ensure minimum price boundary is enforced (minimum 1 unit).

### Acceptance Criteria
- Price calculations return strictly positive values for any valid pool reserves.
- Property test verifies monotonicity of price with respect to supply.

---

## Issue #4: [Contracts] Fix missing storage TTL extensions across persistent market instances

**Labels**: `blockchain, markets, bug`

### Context & Problem
Soroban persistent storage entries for markets and user balance mappings expire if their TTL is not bumped, causing market state to become inaccessible on testnet and mainnet.

### Proposed Solution
1. Invoke `env.storage().persistent().extend_ttl(...)` on all state reads and writes.
2. Set threshold and extension ledger parameters based on network recommendations.

### Acceptance Criteria
- All state accessors bump TTL appropriately.
- Long-running simulation tests verify state remains valid past default TTL.

---

## Issue #5: [Contracts] Fix missing admin timelock enforcement during emergency market cancellation

**Labels**: `blockchain, security, treasury`

### Context & Problem
An admin key compromise allows instant emergency market cancellation without notice, potentially rugging active liquidity providers.

### Proposed Solution
1. Introduce a configurable timelock delay for emergency cancellations.
2. Require a two-phase commit: `schedule_emergency_cancellation` followed by `execute_emergency_cancellation` after delay.

### Acceptance Criteria
- Instant cancellation reverts with `AdminTimelockActive`.
- Executing cancellation is only permitted once timelock elapsed.

---

## Issue #6: [Contracts] Fix unverified oracle report signatures in multi-oracle consensus resolution

**Labels**: `blockchain, oracle, security`

### Context & Problem
When resolving markets using off-chain oracle reports, signature verification is bypassed if quorum threshold is met, allowing forged reports.

### Proposed Solution
1. Verify ed25519 signature of each participating oracle address against the registered oracle public key before counting its vote.
2. Reject duplicate signatures from the same oracle.

### Acceptance Criteria
- Invalid or mismatched signatures cause immediate transaction rejection.
- Test verifies consensus requires valid cryptographic signatures from quorum.

---

## Issue #7: [Contracts] Fix zero-shares liquidity trap when initial LP deposits minimal tokens

**Labels**: `blockchain, trading, bug`

### Context & Problem
If an initial liquidity provider deposits dust amounts, initial LP share minting can round down to 0 while tokens remain locked in the contract forever.

### Proposed Solution
1. Enforce `MINIMUM_INITIAL_LIQUIDITY` (e.g., 1,000,000 stroops / units) locked permanently (dead shares).
2. Validate both outcome reserves meet minimum balance threshold.

### Acceptance Criteria
- Liquidity initialization below threshold reverts.
- First LP receives valid non-zero share tokens.

---

## Issue #8: [Contracts] Fix dispute bond refund logic failing when dispute is upheld by governance

**Labels**: `blockchain, disputes, bug`

### Context & Problem
When a community dispute is voted valid, the bond refund function reverts due to an incorrect balance check against treasury reserves instead of the escrowed dispute balance.

### Proposed Solution
1. Track dispute bonds in a separate escrow mapping per dispute ID.
2. Release the escrowed bond plus reward back to the disputer upon resolution.

### Acceptance Criteria
- Disputer successfully receives initial bond + bonus when dispute passes.
- Escrow accounting balances exactly.

---

## Issue #9: [Contracts] Fix overflow in accumulated protocol fee calculations in treasury contract

**Labels**: `blockchain, treasury, bug`

### Context & Problem
In `contracts/treasury/src/lib.rs`, high-volume markets accumulating protocol fees in `i128` can overflow if fees are compounded without periodic settlement.

### Proposed Solution
1. Use checked arithmetic (`checked_add`, `checked_mul`) for all fee accumulations.
2. Emit an error `FeeOverflow` if limits are exceeded, and cap maximum fee per swap.

### Acceptance Criteria
- Checked math prevents panics in fee accumulation.
- Unit test covers extreme volume edge cases.

---

## Issue #10: [Contracts] Fix unauthorized market registration in market_factory

**Labels**: `blockchain, markets, security`

### Context & Problem
`create_market` in `market_factory` lacks an authorization check validating caller permissions against the factory registry whitelist.

### Proposed Solution
1. Add `caller.require_auth()` and ensure caller is an approved deployer or admin.
2. Prevent deploying duplicate market instances with identical parameters.

### Acceptance Criteria
- Non-authorized calls revert with `Unauthorized`.
- Successfully deployed markets are registered in factory list.

---

## Issue #11: [Contracts] Add storage bump for temporary authentication nonces in market factory

**Labels**: `blockchain, security, middleware`

### Context & Problem
Temporary storage entries used for replay protection nonces in factory deployment do not bump TTL, leading to potential premature eviction.

### Proposed Solution
1. Use `env.storage().temporary().extend_ttl()` on all nonce checks.
2. Standardize nonce validation across contract entry points.

### Acceptance Criteria
- Nonces remain available throughout active transaction life cycle.

---

## Issue #12: [Contracts] Implement strict slippage bounds check on swap_shares to prevent sandwich attacks

**Labels**: `blockchain, trading, feature`

### Context & Problem
Traders placing large market share swaps have no `min_shares_out` parameter, exposing them to MEV / frontrunning sandwich attacks.

### Proposed Solution
1. Add `min_shares_out: i128` parameter to `swap_shares`.
2. Revert with `SlippageExceeded` if received shares fall below the minimum.

### Acceptance Criteria
- Swaps revert if calculated output < `min_shares_out`.
- Integration tests simulate price movement causing expected revert.

---

## Issue #13: [Contracts] Implement minimum bet amount validation to prevent dust attack state bloat

**Labels**: `blockchain, predictions, feature`

### Context & Problem
Users can place 1-stroop bets repeatedly, bloating contract state and consuming storage without contributing liquidity.

### Proposed Solution
1. Define a global constant `MIN_BET_AMOUNT` in `shared/src/lib.rs`.
2. Validate bet amount >= `MIN_BET_AMOUNT` before processing.

### Acceptance Criteria
- Bets below threshold revert with `AmountTooLow`.
- Legitimate bets proceed without issues.

---

## Issue #14: [Contracts] Implement emergency pause circuit breaker across all market interactions

**Labels**: `blockchain, security, feature`

### Context & Problem
In the event of an exploit or oracle failure, administrators need an instant circuit breaker to pause swaps, bets, and dispute resolutions.

### Proposed Solution
1. Add `paused: bool` in market contract storage.
2. Add `set_paused(admin, bool)` with admin authentication.
3. Guard all mutation functions with `require(!paused)`.

### Acceptance Criteria
- When paused, all bets, swaps, and withdrawals revert with `ContractPaused`.
- Only admin can pause/unpause.

---

## Issue #15: [Contracts] Implement dispute resolution appeal cooldown window before final payout

**Labels**: `blockchain, disputes, feature`

### Context & Problem
Immediately after an initial dispute ruling, funds are distributed without allowing an appeal window, preventing community governance intervention.

### Proposed Solution
1. Introduce an `appeal_window_end` timestamp.
2. Require payout execution to happen only after `env.ledger().timestamp() >= appeal_window_end`.

### Acceptance Criteria
- Payout claims during appeal window revert.
- Payout claims after appeal window succeed.

---

## Issue #16: [Contracts] Implement dynamic fee split configuration in treasury with basis point bounds

**Labels**: `blockchain, treasury, feature`

### Context & Problem
Treasury contract has hardcoded fee distribution percentages, preventing governance from adjusting splits between treasury, LP rewards, and burns.

### Proposed Solution
1. Add `set_fee_split(admin, treasury_bps, lp_bps, burn_bps)` verifying sum equals 10,000 bps (100%).
2. Apply configured split on all fee allocations.

### Acceptance Criteria
- Invalid splits (sum != 10000) revert.
- Treasury correctly routes tokens per configured percentages.

---

## Issue #17: [Contracts] Implement partial order matching support for limit-style share orders

**Labels**: `blockchain, trading, feature`

### Context & Problem
Currently, users can only execute AMM market orders; there is no capability to place limit orders that execute when target odds are reached.

### Proposed Solution
1. Create an order storage structure with price limit, amount, and expiry.
2. Match incoming swaps against resting limit orders before routing to the CPMM curve.

### Acceptance Criteria
- Partial fills update remaining order size.
- Cancel order returns unspent balance to creator.

---

## Issue #18: [Contracts] Implement automated contract event emissions for all state transitions

**Labels**: `blockchain, markets, feature`

### Context & Problem
Some contract functions (such as dispute opening and fee updates) do not emit Soroban topics/events, forcing indexers to poll raw ledger entries.

### Proposed Solution
1. Define typed event structures for: `MarketCreated`, `BetPlaced`, `MarketResolved`, `DisputeOpened`, `FeesClaimed`.
2. Emit events with indexed topics for contract ID, user address, and action.

### Acceptance Criteria
- Every critical state change emits a corresponding Soroban event.
- Events follow unified schema matching indexer expectations.

---

## Issue #19: [Contracts] Implement daily withdrawal velocity limits per recipient in treasury contract

**Labels**: `blockchain, treasury, security`

### Context & Problem
A compromised admin or authorized recipient can drain entire treasury balances in a single transaction.

### Proposed Solution
1. Maintain rolling 24-hour withdrawal totals per address in treasury contract.
2. Reject withdrawals exceeding `daily_limit` unless a multi-day timelock is initiated.

### Acceptance Criteria
- Cumulative withdrawals within 24h exceeding limit revert.
- Daily counters reset correctly after 24h window.

---

## Issue #20: [Contracts] Implement multi-token collateral support with Soroban token client validation

**Labels**: `blockchain, markets, feature`

### Context & Problem
Markets currently only support native XLM / standard test token; market creators cannot use verified stablecoins (e.g. USDC).

### Proposed Solution
1. Support arbitrary Stellar Asset Contract (SAC) token addresses in `create_market`.
2. Validate token contract interface compatibility upon initialization.

### Acceptance Criteria
- Markets accept arbitrary Soroban-compatible token addresses.
- Balance and transfers correctly interact with specified token client.

---

## Issue #21: [Contracts] Implement formal property-based fuzz tests for CPMM invariant k = x * y

**Labels**: `blockchain, testing, security`

### Context & Problem
Numerical precision loss and potential invariant drain attacks have not been tested with arbitrary random inputs.

### Proposed Solution
1. Add property-based testing harness using `proptest` or `quickcheck`.
2. Assert that `k_after >= k_before` holds for all non-zero swaps and liquidity additions.

### Acceptance Criteria
- Fuzz tests execute 10,000+ random swap sequences without invariant violation.
- Edge case bounds (min/max integer limits) are covered.

---

## Issue #22: [Contracts] Implement unit test suite for dispute escalation and voting quorum

**Labels**: `blockchain, testing, disputes`

### Context & Problem
Test coverage for the multi-tiered dispute escalation mechanism in `contracts/market/src/dispute.rs` is incomplete.

### Proposed Solution
1. Add comprehensive test cases for: invalid disputes, quorum not met, quorum met with overturn, tie-breaker handling.
2. Verify token transfers and state transitions at every step.

### Acceptance Criteria
- Test coverage for dispute module reaches >= 90%.
- All dispute paths pass cleanly in CI.

---

## Issue #23: [Contracts] Implement gas and CPU instruction profiling benchmarks for market execution

**Labels**: `blockchain, testing, feature`

### Context & Problem
High compute and storage metering can cause Soroban transactions to hit ledger resource limits under high market activity.

### Proposed Solution
1. Write benchmark scripts using `soroban-sdk` budget inspection APIs.
2. Measure CPU cycles and memory footprint for `swap_shares`, `claim_winnings`, and `resolve_market`.

### Acceptance Criteria
- Benchmark reports generated and added to `contracts/benchmarks.md`.
- Optimizations reduce swap transaction budget by at least 15%.

---

## Issue #24: [Contracts] Implement contract upgradeability pattern via WASM hash migration in factory

**Labels**: `blockchain, security, feature`

### Context & Problem
Bug fixes in market contracts cannot be applied to existing deployed instances without manual migration paths.

### Proposed Solution
1. Implement `upgrade(new_wasm_hash)` in market contracts restricted to factory/admin.
2. Use Soroban `env.deployer().update_current_contract_wasm(new_wasm_hash)`.

### Acceptance Criteria
- Authorized upgrades update code while preserving storage.
- Unauthorized upgrade attempts revert.

---

## Issue #25: [Contracts] Implement automated contract size verification in build script

**Labels**: `blockchain, testing, middleware`

### Context & Problem
Soroban has a strict limit on compiled contract WASM bytecode size. Large contracts risk build failure in production.

### Proposed Solution
1. Add a build script that optimizes WASM via `soroban contract optimize`.
2. Fail CI if compiled binary exceeds 64KB threshold.

### Acceptance Criteria
- Build script logs WASM size.
- Pre-merge checks enforce budget limit.

---

## Issue #26: [Backend] Fix unhandled Promise rejections causing backend crash on Postgres pool timeout

**Labels**: `backend, bug, middleware`

### Context & Problem
When database connection pool runs out of available clients or encounters a network timeout, unhandled rejections crash the Node.js server process.

### Proposed Solution
1. Wrap pool acquisition and query executions in standard try/catch blocks with exponential retry.
2. Add global `process.on('unhandledRejection')` and `process.on('uncaughtException')` handlers with graceful shutdown.

### Acceptance Criteria
- DB timeouts return 503 Service Unavailable instead of process termination.
- Connection pool recovers automatically.

---

## Issue #27: [Backend] Fix missing transaction isolation level causing race condition in simultaneous bets

**Labels**: `backend, security, bug`

### Context & Problem
Concurrent bet placement requests from the same user can lead to double-spending off-chain cached balances because queries run in default Read Committed mode.

### Proposed Solution
1. Wrap balance checks and bet placement in a serializable transaction: `tx.transaction(async (trx) => { ... }, { isolationLevel: 'serializable' })`.
2. Use `FOR UPDATE` row-level locks on user balance records.

### Acceptance Criteria
- Simultaneous bet requests are executed atomically without balance drift.
- Stress test verifies zero double-spends.

---

## Issue #28: [Backend] Fix JWT session invalidation bypass on password reset and role changes

**Labels**: `backend, auth, security`

### Context & Problem
When a user resets their password or is banned by admin, previously issued JWT tokens remain valid until expiration (up to 7 days).

### Proposed Solution
1. Add `token_version` column to the `users` table.
2. Include `token_version` in the JWT payload and verify it against DB/Redis on every authenticated request.
3. Increment `token_version` on password reset or account status changes.

### Acceptance Criteria
- Password change immediately invalidates all existing JWT sessions.
- Invalid token returns 401 Unauthorized.

---

## Issue #29: [Backend] Fix SQL injection risk in dynamic order filtering within MarketRepository

**Labels**: `backend, security, repository`

### Context & Problem
In `backend/src/api/repositories/MarketRepository.ts`, raw SQL string concatenation is used for dynamic sort columns and direction, presenting SQL injection vectors.

### Proposed Solution
1. Whitelist acceptable sort columns (`created_at`, `volume`, `liquidity`, `end_time`).
2. Use parameterized Drizzle ORM column references instead of string interpolation.

### Acceptance Criteria
- Arbitrary SQL fragments in query params are rejected with 400 Bad Request.
- Valid sort options function as expected.

---

## Issue #30: [Backend] Fix unbounded pagination queries on /api/governance/proposals and /api/markets

**Labels**: `backend, markets, bug`

### Context & Problem
Querying `/api/markets` without a `limit` parameter loads all historical records into Node.js heap memory, resulting in high latency and OOM crashes.

### Proposed Solution
1. Enforce default limit = 20 and maximum limit = 100 in pagination middleware.
2. Add cursor-based pagination using `id` or `created_at` index for high-scale performance.

### Acceptance Criteria
- Requests with `limit > 100` are clamped or rejected with validation error.
- Memory usage remains bounded under large datasets.

---

## Issue #31: [Backend] Fix missing rate limiter on /api/auth/login and /api/auth/reset-password

**Labels**: `backend, auth, security`

### Context & Problem
Authentication endpoints lack IP and user-based rate limiting, allowing credential stuffing and brute force attacks.

### Proposed Solution
1. Implement `express-rate-limit` with Redis store on `/api/auth/login` (5 attempts per 15 min).
2. Add progressive delay backoff for failed attempts.

### Acceptance Criteria
- Exceeding 5 failed attempts returns 429 Too Many Requests with `Retry-After` header.
- Successful login resets failure counter.

---

## Issue #32: [Backend] Fix CORS configuration wildcard permitting unauthorized origins in production

**Labels**: `backend, security, middleware`

### Context & Problem
CORS middleware uses `origin: "*"` when `NODE_ENV=production`, exposing internal API endpoints to cross-site request forgery and data exfiltration.

### Proposed Solution
1. Restrict CORS origins to an explicit whitelist configured via `ALLOWED_ORIGINS` environment variable.
2. Reject requests with missing or unauthorized `Origin` headers in production.

### Acceptance Criteria
- Production requests from untrusted origins are blocked with CORS error.
- Trusted domains pass cleanly.

---

## Issue #33: [Backend] Fix inconsistent error response format between Express middlewares and controllers

**Labels**: `backend, middleware, bug`

### Context & Problem
Validation errors return `{ error: string }`, while controller errors return `{ success: false, message: string }`, complicating frontend error handling.

### Proposed Solution
1. Standardize error format: `{ success: false, error: { code: string, message: string, details?: any } }`.
2. Refactor centralized `errorHandler` middleware to format all standard and custom `AppError` instances.

### Acceptance Criteria
- All 4xx and 5xx responses adhere to the standard JSON error schema.
- Frontend error handler reliably parses all backend errors.

---

## Issue #34: [Backend] Fix date validation parsing in useCreateMarket backend counterpart endpoint

**Labels**: `backend, markets, bug`

### Context & Problem
The `/api/markets` creation endpoint accepts timestamp values that parse as NaN, failing to validate minimum market duration (e.g. at least 1 hour in the future).

### Proposed Solution
1. Add Joi/Zod validation asserting `scheduledAt` is a valid ISO date >= `Date.now() + 3600000`.
2. Return descriptive validation errors.

### Acceptance Criteria
- Past or malformed dates are rejected with 400 Bad Request.
- Markets must have a duration of at least 1 hour.

---

## Issue #35: [Backend] Fix memory leak in WebSocket connection manager when clients disconnect abruptly

**Labels**: `backend, websocket, bug`

### Context & Problem
When clients close WebSocket connections abruptly without TCP FIN handshake, socket references remain stored in `activeConnections` map, leading to memory leaks.

### Proposed Solution
1. Listen for socket `close` and `error` events and clean up channel subscription sets.
2. Implement 30-second ping/pong heartbeat to identify and prune dead connections.

### Acceptance Criteria
- Disconnected sockets are removed from memory within 60 seconds.
- Memory remains stable under continuous reconnect loops.

---

## Issue #36: [Backend] Fix missing database index on events.sequence_number causing full table scans

**Labels**: `backend, repository, blockchain`

### Context & Problem
Queries querying indexer events by ledger sequence perform full table scans across millions of rows, slowing down indexer synchronization.

### Proposed Solution
1. Add migration: `CREATE INDEX CONCURRENTLY events_sequence_number_idx ON events(sequence_number);`.
2. Add composite index on `(contract_id, sequence_number)` for filtered event queries.

### Acceptance Criteria
- Query execution plan shows Index Scan instead of Seq Scan.
- Synchronization query time drops below 5ms.

---

## Issue #37: [Backend] Fix transaction export endpoint failing with 500 when exporting >10,000 rows

**Labels**: `backend, wallet, bug`

### Context & Problem
`GET /api/transactions/export` buffers all matching rows into memory before generating CSV, crashing on large user account histories.

### Proposed Solution
1. Stream database query results directly to HTTP response using Postgres cursor and `csv-stringify/sync`.
2. Limit export date range to a maximum of 90 days.

### Acceptance Criteria
- Exports stream efficiently without buffering entire dataset in RAM.
- Queries over 90 days return 400 Bad Request with guidance.

---

## Issue #38: [Backend] Fix TOTP two-factor authentication single-use backup codes being reusable

**Labels**: `backend, auth, security`

### Context & Problem
Backup recovery codes generated during 2FA setup are not marked as used upon login, allowing replay attacks.

### Proposed Solution
1. Store backup codes as hashed values with a `used_at: timestamp` flag.
2. Invalidate code immediately upon first successful redemption in the same database transaction.

### Acceptance Criteria
- Reusing a redeemed backup code returns 401 Invalid Code.
- Remaining unused codes continue to function.

---

## Issue #39: [Backend] Fix health check endpoint /health coupling with external Soroban RPC status

**Labels**: `backend, middleware, bug`

### Context & Problem
When external Soroban RPC provider experiences transient latency, the entire backend `/health` endpoint returns 500, causing Kubernetes / Docker to restart healthy backend pods.

### Proposed Solution
1. Separate `/health/live` (checks process liveness) from `/health/ready` (checks DB and RPC dependencies).
2. Set graceful timeouts on external RPC checks so transient hiccups do not report pod failure.

### Acceptance Criteria
- Container liveness probe remains green during upstream RPC degradation.
- Readiness probe accurately reports dependency health.

---

## Issue #40: [Backend] Fix market analytics N+1 query when fetching market outcome odds history

**Labels**: `backend, markets, repository`

### Context & Problem
Fetching the list of markets triggers individual queries for each market's historical odds datapoints, resulting in 100+ DB queries per page request.

### Proposed Solution
1. Use SQL `JOIN` with `JSON_AGG` or window functions to fetch latest odds snapshots in a single query.
2. Cache historical odds in Redis with 30-second TTL.

### Acceptance Criteria
- Single DB query fulfills market list + odds endpoint.
- Endpoint response time reduced by >80%.

---

## Issue #41: [Backend] Implement request payload schema validation using Zod for all POST/PUT routes

**Labels**: `backend, middleware, feature`

### Context & Problem
Several controller endpoints parse `req.body` directly without schema validation, allowing unexpected fields and invalid types to reach business logic.

### Proposed Solution
1. Define Zod schemas for all route inputs (markets, predictions, profile, disputes).
2. Create reusable validation middleware `validateBody(schema)`.

### Acceptance Criteria
- Malformed payloads return detailed 422 Unprocessable Entity errors.
- Valid payloads are safely typed throughout controller code.

---

## Issue #42: [Backend] Implement structured JSON logging with correlation ID tracing via Pino

**Labels**: `backend, middleware, feature`

### Context & Problem
Backend logs use unstructured `console.log` statements, making distributed tracing and error diagnosis difficult in production.

### Proposed Solution
1. Replace `console.log` with `pino` logger.
2. Attach `x-correlation-id` to incoming requests and forward it across logs and external service calls.

### Acceptance Criteria
- All logs output standardized JSON with timestamps, log levels, and correlation IDs.
- Log aggregation tools can parse and trace requests seamlessly.

---

## Issue #43: [Backend] Implement Redis caching layer for high-throughput market odds and leaderboard endpoints

**Labels**: `backend, leaderboard, markets`

### Context & Problem
Leaderboard and active market endpoints receive heavy traffic, creating unnecessary database read load.

### Proposed Solution
1. Integrate Redis client with automatic fallback if Redis is unavailable.
2. Cache leaderboard results for 60 seconds and market odds for 5 seconds.
3. Invalidate cache on market resolution or large trades.

### Acceptance Criteria
- Cache hits serve in < 5ms without DB interaction.
- Invalidation maintains data freshness.

---

## Issue #44: [Backend] Implement idempotent webhook delivery mechanism with HMAC-SHA256 signatures

**Labels**: `backend, notifications, security`

### Context & Problem
Webhooks sent to external partners or consumers can fail on network errors and lack cryptographic verification.

### Proposed Solution
1. Add webhook event queue with exponential retry backoff.
2. Sign webhook payloads with HMAC-SHA256 using partner secret.
3. Include `X-Webhook-Signature` and `X-Event-ID` headers for idempotency.

### Acceptance Criteria
- Webhooks deliver with valid HMAC signatures.
- Failed deliveries retry up to 5 times before moving to DLQ.

---

## Issue #45: [Backend] Implement audit logging table capturing all administrative and dispute actions

**Labels**: `backend, security, repository`

### Context & Problem
Admin actions (market resolution, bans, config updates) are not recorded in an immutable audit trail, creating compliance and security risks.

### Proposed Solution
1. Create `audit_logs` table: `id`, `actor_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `before_state`, `after_state`, `timestamp`.
2. Add middleware logging all admin actions automatically.

### Acceptance Criteria
- Every privileged action creates an immutable audit record.
- Audit records can be queried by security admins.

---

## Issue #46: [Backend] Implement automated database backup and point-in-time recovery strategy

**Labels**: `backend, repository, feature`

### Context & Problem
There is no automated script or verification process for database backups, exposing the platform to data loss in case of hardware failure.

### Proposed Solution
1. Create automated pg_dump backup script with S3 / cloud storage upload.
2. Implement weekly automated restore verification test in staging.

### Acceptance Criteria
- Backup script executes cleanly via cron.
- Documented recovery time objective (RTO) < 1 hour.

---

## Issue #47: [Backend] Implement WebSocket heartbeat ping/pong mechanism to prune dead client sockets

**Labels**: `backend, websocket, feature`

### Context & Problem
Zombie WebSocket connections consume system file descriptors and memory.

### Proposed Solution
1. Server sends ping frame every 30 seconds to all connected clients.
2. Terminate socket if pong is not received within 10 seconds.

### Acceptance Criteria
- Stale connections are pruned automatically.
- Total connection count accurately reflects active clients.

---

## Issue #48: [Backend] Implement user referral tree depth capping and commission calculation bounds

**Labels**: `backend, referrals, feature`

### Context & Problem
Referral payouts lack depth bounds, creating risk of unbounded recursion during payout calculation.

### Proposed Solution
1. Limit referral tree traversal to 2 tiers (direct and tier-2).
2. Validate total referral commission cap (maximum 5% of trading fee).

### Acceptance Criteria
- Referral calculations execute in O(1) time complexity.
- Total commission payout never exceeds allotted fee percentage.

---

## Issue #49: [Backend] Implement OpenAPI/Swagger schema synchronization validation in CI pipeline

**Labels**: `backend, testing, feature`

### Context & Problem
`backend/openapi.yaml` frequently falls out of sync with actual controller routes and payload structures.

### Proposed Solution
1. Add a CI check comparing OpenAPI spec endpoints against registered Express routes.
2. Use `swagger-parser` to validate YAML syntax and schema correctness.

### Acceptance Criteria
- CI fails if routes exist without OpenAPI documentation or if spec contains syntax errors.

---

## Issue #50: [Backend] Implement social feature profanity and spam filter for market comments

**Labels**: `backend, users, feature`

### Context & Problem
Market comments lack content moderation, allowing spam, phishing URLs, and profanity to be posted freely.

### Proposed Solution
1. Implement text filtering middleware checking comments against profanity blocklist.
2. Restrict URL posting to verified domains or block URLs for unverified users.

### Acceptance Criteria
- Prohibited words and suspicious links are blocked with 400 Bad Request.
- Rate limiting prevents comment spamming.

---

## Issue #51: [Backend] Implement activity privacy filter for user betting history

**Labels**: `backend, users, feature`

### Context & Problem
User profile betting history is publicly exposed without option for privacy controls.

### Proposed Solution
1. Add `is_profile_private: boolean` to user settings.
2. Obfuscate or hide prediction history from public view if privacy is enabled.

### Acceptance Criteria
- Private profiles hide bet amounts and market specifics from other users.
- User can always view their own history.

---

## Issue #52: [Backend] Implement automated database migration rollback scripts and smoke tests

**Labels**: `backend, repository, testing`

### Context & Problem
Database migrations only have `up` scripts; failed deployments cannot be automatically rolled back.

### Proposed Solution
1. Write corresponding `down` migration scripts for all schema changes in `backend/migrations`.
2. Add CI test that runs `migrate up` followed by `migrate down` and verifies clean schema state.

### Acceptance Criteria
- Both up and down migrations execute cleanly in test environment.
- Documentation added for rollback procedures.

---

## Issue #53: [Backend] Implement end-to-end integration tests for user authentication and session lifecycle

**Labels**: `backend, auth, testing`

### Context & Problem
Authentication flow (register, verify, login, refresh token, 2FA, logout) lacks comprehensive automated integration tests.

### Proposed Solution
1. Build test suite using Jest and Supertest exercising full auth lifecycle.
2. Test token expiration, refresh rotation, and revocation scenarios.

### Acceptance Criteria
- Auth integration test suite achieves >95% statement coverage.
- All tests execute in CI without flakes.

---

## Issue #54: [Backend] Implement test suite for market resolution payout calculation service

**Labels**: `backend, testing, predictions`

### Context & Problem
Edge cases in outcome payout distribution (e.g., ties, cancelled markets, zero winning bets) lack dedicated unit tests.

### Proposed Solution
1. Create unit tests covering binary, categorical, and cancelled resolution states.
2. Verify precision and rounding behavior under fractional shares.

### Acceptance Criteria
- 100% of calculation branches covered with assertions.
- Verified zero token leakage across all scenarios.

---

## Issue #55: [Backend] Implement Prometheus metrics endpoint /metrics for API latency and error rates

**Labels**: `backend, middleware, feature`

### Context & Problem
Production monitoring lacks visibility into endpoint latency percentiles (p50, p95, p99) and HTTP error code distributions.

### Proposed Solution
1. Use `prom-client` to collect HTTP request durations, active socket counts, and database query durations.
2. Expose `/metrics` endpoint protected by basic auth or internal network restriction.

### Acceptance Criteria
- Prometheus successfully scrapes metrics.
- Standard metrics (requests total, duration histogram, memory usage) are published.

---

## Issue #56: [Indexer] Fix indexer crash on unexpected event topic formatting from unverified contracts

**Labels**: `blockchain, bug, cron`

### Context & Problem
If an unverified contract or malicious actor emits events targeting the indexer address with malformed topics, `indexer/src/poller.ts` crashes on JSON/XDR decode.

### Proposed Solution
1. Wrap event decoding in `safeDecodeXdr` try/catch block.
2. Log malformed events to a dead-letter queue and continue processing remaining ledger events.

### Acceptance Criteria
- Malformed XDR events are safely bypassed without terminating the indexer thread.
- Metrics counter `indexer_malformed_events_total` increments.

---

## Issue #57: [Indexer] Fix ledger gap recovery skipping event batches when Soroban RPC lags behind

**Labels**: `blockchain, bug, cron`

### Context & Problem
When the Soroban RPC node temporarily desyncs and skips ledgers, the indexer advances its cursor without detecting missed event sequences.

### Proposed Solution
1. Track expected `last_processed_ledger`.
2. If `new_ledger > last_processed_ledger + 1`, enter gap recovery mode to backfill missed ledgers sequentially.

### Acceptance Criteria
- No ledgers are skipped during network disruptions.
- Gap recovery logs clear progress and resumes normal polling once caught up.

---

## Issue #58: [Indexer] Fix cursor non-atomic persistence causing duplicate event processing on restart

**Labels**: `blockchain, repository, bug`

### Context & Problem
Event records are inserted into the database, but cursor state is saved in a separate non-transactional step. A crash in between results in re-processing already ingested events.

### Proposed Solution
1. Save event batch insertions and cursor updates inside a single database transaction: `BEGIN ... INSERT events ... UPDATE cursor ... COMMIT`.

### Acceptance Criteria
- Cursor updates atomically with event records.
- Zero duplicate processing after abrupt process kill.

---

## Issue #59: [Indexer] Fix unhandled RPC 429 rate limit errors crashing the indexer poller thread

**Labels**: `blockchain, cron, bug`

### Context & Problem
Public and private Soroban RPC nodes return HTTP 429 when rate limits are exceeded, which causes uncaught errors in the polling loop.

### Proposed Solution
1. Catch 429 errors and extract `Retry-After` header if present.
2. Apply exponential backoff with randomized jitter (e.g. 1s, 2s, 4s, up to 30s) before retrying.

### Acceptance Criteria
- 429 errors trigger backoff rather than crash.
- Poller gracefully resumes once rate limit resets.

---

## Issue #60: [Indexer] Fix memory leak in indexer event queue under sustained high transaction volume

**Labels**: `blockchain, cron, bug`

### Context & Problem
Events fetched from RPC are pushed to an in-memory array that grows unbounded if database ingestion throughput falls behind.

### Proposed Solution
1. Introduce a bounded queue (e.g. max 5,000 items) with backpressure.
2. Pause RPC polling when queue reaches 80% capacity until DB writer catches up.

### Acceptance Criteria
- Heap memory usage remains flat under extreme event ingestion load.
- Backpressure pauses and resumes polling cleanly.

---

## Issue #61: [Indexer] Fix duplicate event ingestion on network reorgs using database unique constraints

**Labels**: `blockchain, repository, bug`

### Context & Problem
When a short ledger reorganization occurs, re-emitted events with the same transaction hash create duplicate records in the database.

### Proposed Solution
1. Add unique constraint: `UNIQUE (transaction_hash, event_index)`.
2. Use `ON CONFLICT (transaction_hash, event_index) DO NOTHING` on event inserts.

### Acceptance Criteria
- Duplicate events are silently skipped without error.
- Event table integrity is preserved.

---

## Issue #62: [Indexer] Fix missing indexer heartbeat metric causing silent failure in monitoring

**Labels**: `blockchain, cron, bug`

### Context & Problem
If the polling loop hangs due to an unhandled socket promise, no process exit occurs, making it appear healthy to health checks while no new events are indexed.

### Proposed Solution
1. Update `last_polled_timestamp` in memory every polling cycle.
2. Expose health check that returns 500 if `Date.now() - last_polled_timestamp > 60000`.

### Acceptance Criteria
- Stalled pollers fail health check and trigger container restart.
- Metric `indexer_last_polled_timestamp_seconds` published to Prometheus.

---

## Issue #63: [Indexer] Fix race condition in concurrent block processing corrupting outcome token balances

**Labels**: `blockchain, markets, bug`

### Context & Problem
Running multiple worker threads to index blocks concurrently causes race conditions when two blocks update the same market's pool reserves out of order.

### Proposed Solution
1. Ensure events for a given `market_id` are processed strictly in ledger sequence order.
2. Use partition-based worker routing or sequential processing per contract ID.

### Acceptance Criteria
- Market pool balances match contract state exactly at every ledger height.
- Out-of-order execution is prevented.

---

## Issue #64: [Indexer] Fix unhandled JSON-RPC socket connection drops without automatic reconnect

**Labels**: `blockchain, websocket, bug`

### Context & Problem
WebSocket / persistent HTTP connections to the Stellar RPC node close after network idle timeouts, leaving the indexer idle permanently.

### Proposed Solution
1. Implement keep-alive ping and reconnect listener on the RPC provider client.
2. Reset and re-establish connection if no message is received within 45 seconds.

### Acceptance Criteria
- Dropped socket connections reconnect automatically within 5 seconds.
- Poller resumes without manual intervention.

---

## Issue #65: [Indexer] Fix timestamp desynchronization between ledger close time and ingestion timestamp

**Labels**: `blockchain, markets, bug`

### Context & Problem
Events currently store `ingested_at = NOW()` instead of the actual Stellar ledger close timestamp, distorting historical chart timeframes.

### Proposed Solution
1. Extract `ledger_closed_at` from block header and persist it as `event_timestamp`.
2. Use `event_timestamp` for all frontend candle and analytics calculations.

### Acceptance Criteria
- Event records store true on-chain ledger timestamp.
- Chart time series data matches blockchain history.

---

## Issue #66: [Indexer] Implement exponential backoff with jitter on Soroban RPC connection failures

**Labels**: `blockchain, cron, feature`

### Context & Problem
Immediate retry on connection failures hammers struggling RPC servers and risks getting IP blacklisted.

### Proposed Solution
1. Implement full jitter algorithm: `sleep = min(MAX_SLEEP, rand(0, BASE * 2^attempt))`.
2. Log connection attempts and retry status clearly.

### Acceptance Criteria
- Reconnect attempts back off smoothly without thundering herd problems.

---

## Issue #67: [Indexer] Implement configurable batch size and polling interval via environment variables

**Labels**: `blockchain, cron, feature`

### Context & Problem
Batch size (100) and polling interval (2000ms) are hardcoded, preventing tuning for testnet vs mainnet environments.

### Proposed Solution
1. Read `INDEXER_BATCH_SIZE` and `INDEXER_POLL_INTERVAL_MS` from environment with sensible defaults.
2. Validate values on startup.

### Acceptance Criteria
- Operators can tune polling speed via environment variables without code modification.

---

## Issue #68: [Indexer] Implement WebSocket event dispatcher decoupling indexing from socket broadcasting

**Labels**: `blockchain, websocket, feature`

### Context & Problem
Broadcasting events to thousands of connected frontend WebSocket clients directly within the polling loop slows down blockchain ingestion.

### Proposed Solution
1. Publish indexed events to a Redis Pub/Sub channel (`events:market:<id>`).
2. Have API server WebSocket workers consume Redis channels independently.

### Acceptance Criteria
- Indexer loop processing time is independent of connected client count.
- Broadcast latency remains under 50ms.

---

## Issue #69: [Indexer] Implement dead-letter queue (DLQ) for failed event ingestion records

**Labels**: `blockchain, repository, feature`

### Context & Problem
When an event fails to process due to a business logic error, it either halts the entire indexer or is dropped without trace.

### Proposed Solution
1. Create `failed_events` table storing payload, error message, stack trace, and retry count.
2. Provide admin CLI command `npm run indexer:retry-dlq` to re-process failed items.

### Acceptance Criteria
- Poison pill events are quarantined to DLQ while indexer continues.
- Admins can inspect and re-drive failed events.

---

## Issue #70: [Indexer] Implement ledger sequence lag reporting and alerting threshold

**Labels**: `blockchain, cron, feature`

### Context & Problem
There is no metric tracking how many ledgers the indexer is behind the Stellar network tip.

### Proposed Solution
1. Query network latest ledger height periodically.
2. Calculate and export `indexer_ledger_lag = network_latest - last_processed_ledger`.
3. Alert if lag > 50 ledgers for > 5 minutes.

### Acceptance Criteria
- Lag metric is exposed and visible in Grafana.
- Threshold violations trigger alerts.

---

## Issue #71: [Indexer] Implement indexer data pruning routine for historical low-priority events

**Labels**: `blockchain, cron, feature`

### Context & Problem
Raw event logs accumulate gigabytes of data over time, increasing database hosting costs and backup times.

### Proposed Solution
1. Implement scheduled monthly cron job archiving events older than 180 days to cold storage (e.g. Parquet / S3).
2. Retain aggregated market summaries in active database.

### Acceptance Criteria
- Pruning runs without locking active tables.
- Historical queries fall back to archive gracefully.

---

## Issue #72: [Indexer] Implement event schema validation before persisting to Postgres tables

**Labels**: `blockchain, repository, feature`

### Context & Problem
Unvalidated event payloads can insert unexpected nulls or malformed JSON into the database.

### Proposed Solution
1. Validate event payloads against Zod schemas matching contract event definitions.
2. Reject non-conforming events to DLQ.

### Acceptance Criteria
- Database contains only strictly typed, valid event structures.

---

## Issue #73: [Indexer] Implement snapshot replay mechanism for re-indexing from specific ledger heights

**Labels**: `blockchain, cron, feature`

### Context & Problem
When bugs are fixed in event parsing, developers must wipe the entire database to re-index from scratch.

### Proposed Solution
1. Add CLI flag `--from-ledger <number>` and `--to-ledger <number>`.
2. Allow selective re-indexing of specific contracts or block ranges with upsert semantics.

### Acceptance Criteria
- CLI allows re-indexing targeted ledger intervals without wiping unaffected data.

---

## Issue #74: [Indexer] Implement integration tests with mock Soroban RPC server simulating reorgs

**Labels**: `blockchain, testing, feature`

### Context & Problem
Indexer resilience during network forks and reorgs is untested in automated CI.

### Proposed Solution
1. Build mock RPC test server that simulates ledger forks, skipped sequences, and 429 rate limits.
2. Verify indexer handles all fault conditions cleanly.

### Acceptance Criteria
- Comprehensive test suite validates recovery scenarios in CI.

---

## Issue #75: [Indexer] Implement Docker healthcheck verifying indexer ledger processing freshness

**Labels**: `blockchain, testing, middleware`

### Context & Problem
The indexer container in `docker-compose.yml` lacks a healthcheck, preventing orchestrators from restarting hung containers.

### Proposed Solution
1. Add healthcheck script checking timestamp of last processed event in DB.
2. Configure `healthcheck` in `docker-compose.yml`.

### Acceptance Criteria
- Unhealthy indexer container status triggers restart automatically.

---

## Issue #76: [Frontend] Fix Next.js hydration error caused by server-rendered locale-specific dates

**Labels**: `markets, bug, good first issue`

### Context & Problem
Rendering market expiration dates with `toLocaleDateString()` produces different outputs on the Node.js server vs browser, triggering React hydration mismatch warnings.

### Proposed Solution
1. Create a `<FormattedDate date={...} />` component that renders a placeholder during SSR and updates on client mount.
2. Alternatively, standardize on UTC format until hydration completes.

### Acceptance Criteria
- Zero hydration mismatch warnings in browser console on market pages.

---

## Issue #77: [Frontend] Fix Freighter wallet unhandled rejection when user denies signature request

**Labels**: `wallet, bug, good first issue`

### Context & Problem
When a user rejects a transaction signing prompt in the Freighter extension, the promise rejects without a catch block, displaying an uncaught error modal to the user.

### Proposed Solution
1. Wrap Freighter signing calls in try/catch.
2. Display a user-friendly toast: 'Transaction was cancelled in wallet.'

### Acceptance Criteria
- Rejecting signature in wallet handles gracefully without application error.

---

## Issue #78: [Frontend] Fix NaN displaying in betting slip odds when market liquidity is zero

**Labels**: `markets, predictions, bug`

### Context & Problem
When viewing a newly created market before initial liquidity is deposited, the odds calculation divides by zero, displaying `NaN%` and breaking the betting slip input.

### Proposed Solution
1. Guard division: if total liquidity is 0, display default odds (e.g. 50% / 50%) or disabled state 'Awaiting Liquidity'.
2. Disable bet placement buttons until liquidity exists.

### Acceptance Criteria
- Zero-liquidity markets display clear status message without NaN.

---

## Issue #79: [Frontend] Fix missing React Error Boundary on market trading widget causing entire page whiteout

**Labels**: `trading, bug, good first issue`

### Context & Problem
An unhandled exception in the order book or chart component crashes the entire page tree to a white screen.

### Proposed Solution
1. Wrap `TradingWidget`, `OrderBook`, and `PriceChart` in dedicated React Error Boundaries.
2. Render fallback UI with a 'Reload Widget' button.

### Acceptance Criteria
- Widget errors are isolated without crashing navigation or adjacent components.

---

## Issue #80: [Frontend] Fix memory leak in WebSocket hook failing to unsubscribe on component unmount

**Labels**: `websocket, bug, markets`

### Context & Problem
`useMarketWebSocket` hook registers event listeners on global socket manager but does not clean them up in the `useEffect` return function.

### Proposed Solution
1. Return cleanup function calling `socket.off(...)` and unsubscribe from market channel on unmount.

### Acceptance Criteria
- Listener count returns to baseline when navigating between market pages.

---

## Issue #81: [Frontend] Fix stale market prices displayed after WebSocket reconnection

**Labels**: `websocket, markets, bug`

### Context & Problem
When WebSocket reconnects after a temporary network drop, client retains stale market prices until a new trade event occurs.

### Proposed Solution
1. On WebSocket reconnect event, immediately trigger a background REST refetch of active market data.

### Acceptance Criteria
- Reconnecting socket synchronizes prices with server immediately.

---

## Issue #82: [Frontend] Fix form submission double-click triggering duplicate Soroban transactions

**Labels**: `predictions, wallet, bug`

### Context & Problem
Rapidly clicking 'Place Bet' or 'Create Market' triggers two concurrent Freighter signature prompts, leading to accidental duplicate transactions.

### Proposed Solution
1. Set button loading state immediately on first click and disable the button until transaction settles or fails.
2. Use idempotency keys on client-side requests.

### Acceptance Criteria
- Double-clicking is prevented; only one transaction is built and submitted.

---

## Issue #83: [Frontend] Fix dark mode color contrast ratios failing WCAG 2.1 AA accessibility guidelines

**Labels**: `feature, bug, good first issue`

### Context & Problem
Certain text labels (muted timestamps, odds pills) have insufficient contrast in dark mode (< 4.5:1 ratio), failing accessibility audits.

### Proposed Solution
1. Adjust Tailwind color tokens in `tailwind.config.ts` for dark mode variants to guarantee >= 4.5:1 contrast.
2. Run automated axe-core accessibility checks.

### Acceptance Criteria
- All text elements pass WCAG 2.1 AA contrast requirements.

---

## Issue #84: [Frontend] Fix mobile viewport layout breaking on market detail order book tabs

**Labels**: `trading, markets, bug`

### Context & Problem
On mobile screens (< 375px), the order book table overflows horizontally, breaking the viewport and hiding action buttons.

### Proposed Solution
1. Implement responsive horizontal scroll or compact view for mobile viewports.
2. Ensure betting slip docks neatly to bottom of screen on mobile.

### Acceptance Criteria
- Zero horizontal overflow on screen widths down to 320px.

---

## Issue #85: [Frontend] Fix token balance not refreshing automatically after transaction confirmation

**Labels**: `wallet, bug, good first issue`

### Context & Problem
After completing a bet or liquidity deposit, the displayed wallet token balance remains unchanged until full page refresh.

### Proposed Solution
1. Trigger global balance invalidation via React Query / SWR upon transaction confirmation receipt.

### Acceptance Criteria
- Wallet token balance updates within 2 seconds of transaction confirmation.

---

## Issue #86: [Frontend] Fix user notification dropdown failing to mark notifications as read

**Labels**: `notifications, bug, good first issue`

### Context & Problem
Clicking 'Mark all as read' in the notification dropdown updates local state but does not send the mutation to the backend API.

### Proposed Solution
1. Wire mutation to `POST /api/notifications/mark-read`.
2. Sync unread badge count with server response.

### Acceptance Criteria
- Notifications remain marked as read across page refreshes.

---

## Issue #87: [Frontend] Fix XSS vulnerability in user profile bio and display name rendering

**Labels**: `security, users, bug`

### Context & Problem
User profile bio renders raw HTML in user card without sanitization, allowing stored XSS attacks.

### Proposed Solution
1. Use `DOMPurify` to sanitize user bio text or render as plain text only.
2. Set strict Content Security Policy (CSP) headers in Next.js configuration.

### Acceptance Criteria
- Malicious `<script>` and `onerror` payloads in bios are neutralized.

---

## Issue #88: [Frontend] Fix infinite re-render loop in useMarketData hook dependencies

**Labels**: `markets, bug, good first issue`

### Context & Problem
`useMarketData` defines an object literal inside `useEffect` dependency array, triggering infinite re-renders on market detail page.

### Proposed Solution
1. Memoize query options using `useMemo` and extract primitive dependencies (`marketId`).

### Acceptance Criteria
- Hook re-executes only when `marketId` actually changes.

---

## Issue #89: [Frontend] Fix transaction toast notification persisting indefinitely on network timeout

**Labels**: `notifications, bug, wallet`

### Context & Problem
If transaction polling times out, the 'Transaction in progress' toast never dismisses or transitions to error state.

### Proposed Solution
1. Add a 60-second timeout to transaction status watchers.
2. Transition toast to 'Transaction taking longer than expected. Check Stellar Expert' with link.

### Acceptance Criteria
- Toast automatically dismisses or displays error after timeout.

---

## Issue #90: [Frontend] Fix dispute evidence upload failing without user-visible error on oversized files

**Labels**: `disputes, bug, good first issue`

### Context & Problem
Uploading evidence files > 5MB fails silently without alerting the user.

### Proposed Solution
1. Add client-side file size check before initiating upload.
2. Display clear error: 'File exceeds 5MB limit. Please upload a smaller screenshot/PDF.'

### Acceptance Criteria
- Oversized uploads are rejected immediately with user-facing message.

---

## Issue #91: [Frontend] Implement optimistic UI state updates with automatic rollback on transaction failure

**Labels**: `predictions, trading, feature`

### Context & Problem
Users wait several seconds for Soroban transaction confirmation before seeing their bet appear in the active positions table.

### Proposed Solution
1. Immediately append pending position to local state.
2. Revert to previous state with an error toast if transaction fails on-chain.

### Acceptance Criteria
- Bet appears instantly in UI with 'Pending confirmation' status indicator.

---

## Issue #92: [Frontend] Implement skeleton loading states across market lists, portfolios, and leaderboards

**Labels**: `markets, leaderboard, feature`

### Context & Problem
Pages display blank screens or jarring layout shifts while data is loading from the API.

### Proposed Solution
1. Create reusable SVG skeleton loader components matching market card, table row, and chart dimensions.
2. Display skeletons during loading states.

### Acceptance Criteria
- Smooth visual transition from skeleton to populated content without layout shifts.

---

## Issue #93: [Frontend] Implement responsive sticky betting slip for mobile screens

**Labels**: `trading, feature, good first issue`

### Context & Problem
Mobile users have to scroll back and forth between market chart and betting slip.

### Proposed Solution
1. Create bottom-sheet drawer for betting slip on viewports < 768px.
2. Allow swipe down to minimize and tap to expand.

### Acceptance Criteria
- Mobile users can interact with betting slip seamlessly from anywhere on page.

---

## Issue #94: [Frontend] Implement comprehensive form validation with clear inline error messages

**Labels**: `markets, feature, good first issue`

### Context & Problem
Market creation form errors are only shown in a top banner, making it hard to see which input was invalid.

### Proposed Solution
1. Integrate React Hook Form with Zod resolver.
2. Highlight invalid fields with red borders and inline explanation text.

### Acceptance Criteria
- Form fields validate on blur with clear error feedback.

---

## Issue #95: [Frontend] Implement localized currency and timezone formatters across all financial tables

**Labels**: `wallet, feature, good first issue`

### Context & Problem
Timestamps and currency amounts use unformatted numbers, causing confusion for global users.

### Proposed Solution
1. Create formatting utilities using `Intl.NumberFormat` and `Intl.DateTimeFormat`.
2. Display user's local timezone alongside UTC indicator.

### Acceptance Criteria
- All numbers format with thousands separators and accurate decimal places.

---

## Issue #96: [Frontend] Implement market search and multi-facet filtering (category, status, liquidity, volume)

**Labels**: `markets, feature, good first issue`

### Context & Problem
Users cannot easily filter markets by status (Open, Resolved, Disputed) or category (Crypto, Sports, Politics).

### Proposed Solution
1. Add interactive filter sidebar and debounce search bar.
2. Synchronize filters with URL search params for shareable links.

### Acceptance Criteria
- Filtering updates market list instantly; URL reflects active filter state.

---

## Issue #97: [Frontend] Implement user activity feed with real-time bet placement toasts

**Labels**: `notifications, websocket, feature`

### Context & Problem
The platform lacks social proof and real-time excitement of ongoing market activity.

### Proposed Solution
1. Subscribe to global trade WebSocket channel.
2. Display unobtrusive toast for recent bets over threshold ($50+).

### Acceptance Criteria
- Activity feed updates in real-time with toggle to mute in user settings.

---

## Issue #98: [Frontend] Implement Playwright E2E tests for wallet connection and market creation flow

**Labels**: `testing, markets, wallet`

### Context & Problem
End-to-end user journeys are not tested automatically, leading to regressions in releases.

### Proposed Solution
1. Create Playwright test suite using mock wallet extension.
2. Test end-to-end market creation and form validation.

### Acceptance Criteria
- E2E test runs headlessly in CI pipeline and passes reliably.

---

## Issue #99: [Frontend] Implement Playwright E2E tests for placing predictions and claiming payouts

**Labels**: `testing, predictions, trading`

### Context & Problem
Prediction placement, share redemption, and payout claiming lack automated E2E test coverage.

### Proposed Solution
1. Write Playwright test simulating full user bet lifecycle from purchase to payout claim.

### Acceptance Criteria
- Automated test verifies balance updates and success confirmation modal.

---

## Issue #100: [Frontend] Implement client-side error telemetry reporting to Sentry

**Labels**: `testing, feature, middleware`

### Context & Problem
Frontend JavaScript exceptions in user browsers go unnoticed unless reported manually.

### Proposed Solution
1. Configure `@sentry/nextjs` with environment-specific DSN.
2. Capture unhandled errors and React Error Boundary events with user consent.

### Acceptance Criteria
- Errors report to Sentry dashboard with sourcemaps and breadcrumbs.

---

## Issue #101: [Treasury] Fix quorum percentage rounding allowing proposals to pass with insufficient votes

**Labels**: `treasury, bug, security`

### Context & Problem
Integer division when calculating 66% supermajority quorum rounds down, allowing proposals to pass with fewer votes than legally required.

### Proposed Solution
1. Implement ceiling division for quorum: `(total_votes * required_bps + 9999) / 10000`.
2. Ensure strict `>` or `>=` threshold enforcement.

### Acceptance Criteria
- Quorum math requires strict qualifying vote count before passing.

---

## Issue #102: [Treasury] Fix proposal vote double-counting when user transfers governance tokens mid-vote

**Labels**: `treasury, security, bug`

### Context & Problem
A user can vote on a proposal, transfer governance tokens to another address, and vote again on the same proposal.

### Proposed Solution
1. Implement voting snapshot mechanism based on token balance at proposal creation ledger height.
2. Reject votes from tokens acquired after proposal start.

### Acceptance Criteria
- Tokens can only vote once per proposal based on snapshot balance.

---

## Issue #103: [Treasury] Fix oracle resolution timeout window mismatch between contract and backend cron

**Labels**: `treasury, oracle, bug`

### Context & Problem
The backend cron attempts to trigger default resolution at 24 hours, while the smart contract requires 48 hours, causing repeated transaction failures.

### Proposed Solution
1. Align timeout constants across `contracts/shared/src/lib.rs` and `backend/src/config.ts`.
2. Document dispute and resolution timing parameters clearly.

### Acceptance Criteria
- Automated resolution executes cleanly once contract window opens.

---

## Issue #104: [Treasury] Fix dispute bond confiscation failing when dispute resolves as inconclusive

**Labels**: `treasury, disputes, bug`

### Context & Problem
If a market resolves as 'Inconclusive / Cancelled', the dispute bond is locked in the contract rather than returned to the disputer.

### Proposed Solution
1. Add logic to return 100% of dispute bond to disputer when outcome is deemed inconclusive through no fault of their own.

### Acceptance Criteria
- Bonds refund properly upon inconclusive market cancellation.

---

## Issue #105: [Treasury] Fix multi-sig execution authorization bypass in treasury withdrawal proposals

**Labels**: `treasury, security, bug`

### Context & Problem
A logic flaw in signature counting allows multiple signatures from the same authorized signer to count toward the threshold.

### Proposed Solution
1. Enforce unique signer addresses using a bitmask or set verification.
2. Assert `unique_signers.len() >= required_signatures`.

### Acceptance Criteria
- Replay signatures from the same key are rejected with `DuplicateSigner`.

---

## Issue #106: [Treasury] Fix staking reward distribution integer truncation favoring early claimants

**Labels**: `treasury, bug, wallet`

### Context & Problem
Reward rate truncation in early blocks over-allocates rewards to early stakers, leaving insufficient reward pool for subsequent stakers.

### Proposed Solution
1. Implement standard Synthetix-style `rewardPerTokenStored` accumulator with high-precision scaling (1e18).

### Acceptance Criteria
- Reward distribution remains mathematically fair across all staker deposit times.

---

## Issue #107: [Treasury] Fix emergency freeze failing to pause withdrawal queues in treasury

**Labels**: `treasury, security, bug`

### Context & Problem
Triggering `freeze()` halts new withdrawal requests but fails to pause queued withdrawals already scheduled for release.

### Proposed Solution
1. Check `!frozen` flag inside `execute_withdrawal` as well as `request_withdrawal`.

### Acceptance Criteria
- All withdrawal executions are halted while freeze is active.

---

## Issue #108: [Treasury] Fix oracle reputation score not decrementing after submitting refuted outcome

**Labels**: `oracle, disputes, bug`

### Context & Problem
When an oracle's reported outcome is overturned by governance dispute, the oracle's on-chain reputation score remains unchanged.

### Proposed Solution
1. Deduct reputation points upon upheld dispute and slash a portion of the oracle's staked bond.
2. Auto-delist oracle if score drops below minimum threshold.

### Acceptance Criteria
- Erroneous oracle reports result in automatic penalty and slashing.

---

## Issue #109: [Treasury] Implement 2-of-3 oracle consensus validation with signature verification

**Labels**: `oracle, security, feature`

### Context & Problem
Single-oracle market resolution creates centralization risk and single points of failure.

### Proposed Solution
1. Require outcome reports from at least 2 independent registered oracles.
2. Resolve market only when reports match; trigger dispute automatically if reports conflict.

### Acceptance Criteria
- Markets resolve automatically when 2 of 3 oracles submit matching reports.

---

## Issue #110: [Treasury] Implement dispute escalation tier requiring increasing bond deposits per appeal

**Labels**: `disputes, feature, treasury`

### Context & Problem
Trivially low dispute bond amounts allow bad actors to repeatedly stall market settlements with frivolous appeals.

### Proposed Solution
1. Double the required bond deposit on each subsequent appeal tier (100 -> 200 -> 400 XLM).
2. Cap appeals at 3 tiers before ultimate community referendum.

### Acceptance Criteria
- Escalated disputes require exponentially higher bond amounts.

---

## Issue #111: [Treasury] Implement quadratic voting mechanism for governance grant allocations

**Labels**: `treasury, feature, good first issue`

### Context & Problem
Large token holders completely dominate governance treasury funding decisions.

### Proposed Solution
1. Calculate voting weight as `sqrt(token_balance)` for ecosystem grant proposals.

### Acceptance Criteria
- Quadratic vote weighting verified in unit tests.

---

## Issue #112: [Treasury] Implement automated treasury balance reconciliation cron job with Slack alerting

**Labels**: `treasury, cron, feature`

### Context & Problem
No automated system verifies that on-chain treasury token balances match internal ledger records.

### Proposed Solution
1. Create hourly cron comparing on-chain contract balances against database aggregates.
2. Trigger high-priority alert if delta exceeds tolerance threshold.

### Acceptance Criteria
- Hourly reconciliation logs balance parity; alerts on discrepancies.

---

## Issue #113: [Treasury] Implement governance proposal cancellation by author before voting starts

**Labels**: `treasury, feature, good first issue`

### Context & Problem
Proposers who discover a typo or flaw in their proposal cannot cancel it once submitted.

### Proposed Solution
1. Add `cancel_proposal` allowing proposer to withdraw proposal before voting opens.
2. Return submission deposit.

### Acceptance Criteria
- Authors can cancel pending proposals and reclaim deposit.

---

## Issue #114: [Treasury] Implement time-locked delay on critical parameter changes (fees, oracle whitelist)

**Labels**: `treasury, security, feature`

### Context & Problem
Immediate parameter changes give users no time to exit positions if fees or governance rules change unfavorably.

### Proposed Solution
1. Enforce 48-hour timelock between proposing a fee change and executing it.

### Acceptance Criteria
- Parameter modifications enforce 48-hour delay with event notification.

---

## Issue #115: [Treasury] Implement unit tests for multi-sig threshold changes and timelock expiration

**Labels**: `treasury, testing, security`

### Context & Problem
Threshold change edge cases (e.g. reducing threshold below signer count, removing active signers) need thorough test coverage.

### Proposed Solution
1. Write test suite in `contracts/treasury/src/test.rs` covering all governance mutation scenarios.

### Acceptance Criteria
- 100% test coverage of multi-sig admin operations.

---

## Issue #116: [DevOps] Fix Docker Compose staging container startup race condition between DB and backend

**Labels**: `security, middleware, bug`

### Context & Problem
In `docker-compose.staging.yml`, the backend service starts before PostgreSQL is ready to accept connections, causing boot crash loops.

### Proposed Solution
1. Add `pg_isready` healthcheck to the `db` service.
2. Use `depends_on: db: condition: service_healthy` on backend and indexer containers.

### Acceptance Criteria
- `docker compose -f docker-compose.staging.yml up` boots cleanly without container restarts.

---

## Issue #117: [DevOps] Fix Dependabot alerts and update vulnerable dependencies in backend and frontend

**Labels**: `security, backend, bug`

### Context & Problem
Multiple high and moderate severity Dependabot alerts exist across npm dependencies (`cross-spawn`, `cookie`, `micromatch`).

### Proposed Solution
1. Audit and upgrade vulnerable dependencies in `backend/package.json` and `frontend/package.json`.
2. Run automated test suites to ensure zero breaking regressions.

### Acceptance Criteria
- `npm audit` reports 0 high or critical vulnerabilities.

---

## Issue #118: [DevOps] Fix Gitleaks false positives and enforce secret scanning in pre-commit hooks

**Labels**: `security, testing, bug`

### Context & Problem
Test keys and mock tokens in test files trigger false positive failures in Gitleaks.

### Proposed Solution
1. Update `.gitleaks.toml` with explicit path allowlists for mock fixtures.
2. Add pre-commit hook script blocking commits with actual credentials.

### Acceptance Criteria
- Gitleaks scans pass cleanly in CI while protecting against real leaks.

---

## Issue #119: [DevOps] Fix missing non-root user in Dockerfiles posing container escape risks

**Labels**: `security, middleware, bug`

### Context & Problem
`backend/Dockerfile` and `indexer/Dockerfile` run applications as `root`, violating container security best practices.

### Proposed Solution
1. Create a dedicated non-root user: `RUN addgroup -S app && adduser -S app -G app`.
2. Add `USER app` before `CMD` instruction.

### Acceptance Criteria
- Containers execute under unprivileged user permissions.

---

## Issue #120: [DevOps] Implement GitHub Actions workflow for automated Soroban contract compilation and test

**Labels**: `testing, blockchain, feature`

### Context & Problem
Pull requests can merge with broken Soroban contract code because CI only tests backend TypeScript.

### Proposed Solution
1. Add `.github/workflows/contracts.yml` running `cargo clippy`, `cargo test`, and `cargo check`.

### Acceptance Criteria
- Every PR automatically tests Rust contracts in CI.

---

## Issue #121: [DevOps] Implement automated testnet deployment pipeline triggered on main branch merge

**Labels**: `blockchain, feature, cron`

### Context & Problem
Deploying contracts and backend to Stellar Testnet requires manual developer intervention.

### Proposed Solution
1. Create CD workflow deploying updated contracts to Stellar testnet and updating contract ID configs.

### Acceptance Criteria
- Merges to `main` trigger automated deployment and smoke tests.

---

## Issue #122: [DevOps] Implement database connection pooling tuning for high-concurrency production load

**Labels**: `backend, repository, feature`

### Context & Problem
Default connection pool limit of 10 clients exhausts quickly under concurrent traffic spikes.

### Proposed Solution
1. Tune pool settings in `backend/src/db/index.ts`: `max: 50, idleTimeoutMillis: 30000, connectionTimeoutMillis: 5000`.
2. Configure PgBouncer in staging docker compose.

### Acceptance Criteria
- System handles 500 concurrent requests without connection acquisition errors.

---

## Issue #123: [DevOps] Implement automated contract bytecode size and optimization verification in CI

**Labels**: `blockchain, testing, feature`

### Context & Problem
Unchecked WASM sizes can exceed Soroban limits silently.

### Proposed Solution
1. Integrate `soroban contract optimize` in CI workflow.
2. Assert optimized WASM <= 64KB with artifact upload.

### Acceptance Criteria
- PRs report compiled WASM sizes; fail if over limit.

---

## Issue #124: [DevOps] Implement comprehensive seed script for local development and testnet simulation

**Labels**: `backend, feature, good first issue`

### Context & Problem
New developers starting locally have an empty database with no markets, categories, or test users.

### Proposed Solution
1. Create `npm run db:seed` script generating realistic categories, active markets, orders, and mock oracles.

### Acceptance Criteria
- Single command seeds a fully functional local development environment.

---

## Issue #125: [DevOps] Implement centralized logging and metric dashboard configuration with Grafana and Prometheus

**Labels**: `middleware, feature, testing`

### Context & Problem
No consolidated dashboard exists to monitor system health across backend, indexer, and contract interactions.

### Proposed Solution
1. Add Prometheus and Grafana service definitions to `docker-compose.staging.yml`.
2. Pre-configure dashboard JSON tracking API RPS, error rates, indexer lag, and contract volume.

### Acceptance Criteria
- Grafana dashboard visualizes full-stack metrics out-of-the-box.

---

