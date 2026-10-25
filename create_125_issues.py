#!/usr/bin/env python3
"""
Script to create labels and push 125 comprehensive, high-quality issues to
doradenise-jpg/BANKERCHANGER GitHub repository.
Supports execution via `gh` CLI or directly using a GitHub Personal Access Token (GH_TOKEN).
Also exports issues to ISSUES_125.md and issues_125.json.
"""

import os
import sys
import json
import subprocess
import time

REPO = "doradenise-jpg/BANKERCHANGER"

# Comprehensive labels required for the 125 issues
LABELS = [
    {
        "name": "backend",
        "color": "0075ca",
        "description": "Backend / API work"
    },
    {
        "name": "auth",
        "color": "ee0701",
        "description": "Authentication & authorisation"
    },
    {
        "name": "markets",
        "color": "e4e669",
        "description": "Market management"
    },
    {
        "name": "trading",
        "color": "f9d0c4",
        "description": "Trading & share operations"
    },
    {
        "name": "predictions",
        "color": "a2eeef",
        "description": "Prediction placement & settlement"
    },
    {
        "name": "disputes",
        "color": "b60205",
        "description": "Dispute resolution"
    },
    {
        "name": "oracle",
        "color": "5319e7",
        "description": "Oracle integration"
    },
    {
        "name": "wallet",
        "color": "006b75",
        "description": "Wallet & balance management"
    },
    {
        "name": "treasury",
        "color": "0e8a16",
        "description": "Treasury operations"
    },
    {
        "name": "notifications",
        "color": "fbca04",
        "description": "Notification system"
    },
    {
        "name": "leaderboard",
        "color": "1d76db",
        "description": "Leaderboard & rankings"
    },
    {
        "name": "users",
        "color": "bfd4f2",
        "description": "User profile & management"
    },
    {
        "name": "referrals",
        "color": "d93f0b",
        "description": "Referral system"
    },
    {
        "name": "achievements",
        "color": "0075ca",
        "description": "Achievement & reward system"
    },
    {
        "name": "websocket",
        "color": "5319e7",
        "description": "Real-time WebSocket layer"
    },
    {
        "name": "middleware",
        "color": "e4e669",
        "description": "Express middleware"
    },
    {
        "name": "blockchain",
        "color": "0e8a16",
        "description": "Stellar / Soroban blockchain layer"
    },
    {
        "name": "cron",
        "color": "fbca04",
        "description": "Scheduled / background jobs"
    },
    {
        "name": "repository",
        "color": "bfd4f2",
        "description": "Data access layer"
    },
    {
        "name": "feature",
        "color": "a2eeef",
        "description": "New functionality"
    },
    {
        "name": "bug",
        "color": "ee0701",
        "description": "Bug fix"
    },
    {
        "name": "security",
        "color": "ee0701",
        "description": "Security-critical"
    },
    {
        "name": "testing",
        "color": "0075ca",
        "description": "Test coverage"
    },
    {
        "name": "good first issue",
        "color": "7057ff",
        "description": "Suitable for newcomers"
    }
]

ISSUES = [
    {
        "title": "[Contracts] Fix #[contracterror] macro LengthExceedsMax panic in shared/src/errors.rs",
        "body": "### Context & Problem\nSoroban SDK's `#[contracterror]` macro panics with `called Result::unwrap() on an Err value: LengthExceedsMax` in `contracts/shared/src/errors.rs`. This completely breaks compilation of `boxmeout-shared` and dependent contracts.\n\n### Proposed Solution\n1. Inspect variant identifiers and string lengths in `contracts/shared/src/errors.rs`.\n2. Consolidate error variants or group error domains (auth, market, treasury, math) to satisfy Soroban SDK macro constraints.\n3. Ensure no discriminant exceeds `u32` limits and variant names are concise.\n\n### Acceptance Criteria\n- `cargo check --manifest-path contracts/Cargo.toml` compiles successfully without macro panics.\n- Error codes remain uniquely mapped and documented.",
        "labels": [
            "blockchain",
            "bug",
            "security"
        ]
    },
    {
        "title": "[Contracts] Fix reentrancy and Checks-Effects-Interactions violations in share redemption",
        "body": "### Context & Problem\nIn `contracts/market/src/lib.rs`, token transfer to the winning bettor occurs before deducting the user's winning outcome shares balance from contract storage, violating the Checks-Effects-Interactions (CEI) pattern.\n\n### Proposed Solution\n1. Update user state and pool reserves before executing `token::Client::transfer`.\n2. Add reentrancy guard or ensure strict CEI ordering across `claim_winnings` and `redeem_shares`.\n\n### Acceptance Criteria\n- Storage mutations are finalized prior to external token transfers.\n- Unit tests verify reentrancy revert behavior.",
        "labels": [
            "blockchain",
            "security",
            "bug"
        ]
    },
    {
        "title": "[Contracts] Fix integer rounding down to zero in CPMM outcome token pricing",
        "body": "### Context & Problem\nDuring share pricing calculations in low-liquidity markets, integer division in `contracts/shared/src/math.rs` truncates remainders, resulting in 0 price output and allowing zero-cost share acquisition.\n\n### Proposed Solution\n1. Implement fixed-point scaling factor (e.g. 10^7 or 10^9 precision) before performing division in AMM price formula.\n2. Ensure minimum price boundary is enforced (minimum 1 unit).\n\n### Acceptance Criteria\n- Price calculations return strictly positive values for any valid pool reserves.\n- Property test verifies monotonicity of price with respect to supply.",
        "labels": [
            "blockchain",
            "trading",
            "bug"
        ]
    },
    {
        "title": "[Contracts] Fix missing storage TTL extensions across persistent market instances",
        "body": "### Context & Problem\nSoroban persistent storage entries for markets and user balance mappings expire if their TTL is not bumped, causing market state to become inaccessible on testnet and mainnet.\n\n### Proposed Solution\n1. Invoke `env.storage().persistent().extend_ttl(...)` on all state reads and writes.\n2. Set threshold and extension ledger parameters based on network recommendations.\n\n### Acceptance Criteria\n- All state accessors bump TTL appropriately.\n- Long-running simulation tests verify state remains valid past default TTL.",
        "labels": [
            "blockchain",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Contracts] Fix missing admin timelock enforcement during emergency market cancellation",
        "body": "### Context & Problem\nAn admin key compromise allows instant emergency market cancellation without notice, potentially rugging active liquidity providers.\n\n### Proposed Solution\n1. Introduce a configurable timelock delay for emergency cancellations.\n2. Require a two-phase commit: `schedule_emergency_cancellation` followed by `execute_emergency_cancellation` after delay.\n\n### Acceptance Criteria\n- Instant cancellation reverts with `AdminTimelockActive`.\n- Executing cancellation is only permitted once timelock elapsed.",
        "labels": [
            "blockchain",
            "security",
            "treasury"
        ]
    },
    {
        "title": "[Contracts] Fix unverified oracle report signatures in multi-oracle consensus resolution",
        "body": "### Context & Problem\nWhen resolving markets using off-chain oracle reports, signature verification is bypassed if quorum threshold is met, allowing forged reports.\n\n### Proposed Solution\n1. Verify ed25519 signature of each participating oracle address against the registered oracle public key before counting its vote.\n2. Reject duplicate signatures from the same oracle.\n\n### Acceptance Criteria\n- Invalid or mismatched signatures cause immediate transaction rejection.\n- Test verifies consensus requires valid cryptographic signatures from quorum.",
        "labels": [
            "blockchain",
            "oracle",
            "security"
        ]
    },
    {
        "title": "[Contracts] Fix zero-shares liquidity trap when initial LP deposits minimal tokens",
        "body": "### Context & Problem\nIf an initial liquidity provider deposits dust amounts, initial LP share minting can round down to 0 while tokens remain locked in the contract forever.\n\n### Proposed Solution\n1. Enforce `MINIMUM_INITIAL_LIQUIDITY` (e.g., 1,000,000 stroops / units) locked permanently (dead shares).\n2. Validate both outcome reserves meet minimum balance threshold.\n\n### Acceptance Criteria\n- Liquidity initialization below threshold reverts.\n- First LP receives valid non-zero share tokens.",
        "labels": [
            "blockchain",
            "trading",
            "bug"
        ]
    },
    {
        "title": "[Contracts] Fix dispute bond refund logic failing when dispute is upheld by governance",
        "body": "### Context & Problem\nWhen a community dispute is voted valid, the bond refund function reverts due to an incorrect balance check against treasury reserves instead of the escrowed dispute balance.\n\n### Proposed Solution\n1. Track dispute bonds in a separate escrow mapping per dispute ID.\n2. Release the escrowed bond plus reward back to the disputer upon resolution.\n\n### Acceptance Criteria\n- Disputer successfully receives initial bond + bonus when dispute passes.\n- Escrow accounting balances exactly.",
        "labels": [
            "blockchain",
            "disputes",
            "bug"
        ]
    },
    {
        "title": "[Contracts] Fix overflow in accumulated protocol fee calculations in treasury contract",
        "body": "### Context & Problem\nIn `contracts/treasury/src/lib.rs`, high-volume markets accumulating protocol fees in `i128` can overflow if fees are compounded without periodic settlement.\n\n### Proposed Solution\n1. Use checked arithmetic (`checked_add`, `checked_mul`) for all fee accumulations.\n2. Emit an error `FeeOverflow` if limits are exceeded, and cap maximum fee per swap.\n\n### Acceptance Criteria\n- Checked math prevents panics in fee accumulation.\n- Unit test covers extreme volume edge cases.",
        "labels": [
            "blockchain",
            "treasury",
            "bug"
        ]
    },
    {
        "title": "[Contracts] Fix unauthorized market registration in market_factory",
        "body": "### Context & Problem\n`create_market` in `market_factory` lacks an authorization check validating caller permissions against the factory registry whitelist.\n\n### Proposed Solution\n1. Add `caller.require_auth()` and ensure caller is an approved deployer or admin.\n2. Prevent deploying duplicate market instances with identical parameters.\n\n### Acceptance Criteria\n- Non-authorized calls revert with `Unauthorized`.\n- Successfully deployed markets are registered in factory list.",
        "labels": [
            "blockchain",
            "markets",
            "security"
        ]
    },
    {
        "title": "[Contracts] Add storage bump for temporary authentication nonces in market factory",
        "body": "### Context & Problem\nTemporary storage entries used for replay protection nonces in factory deployment do not bump TTL, leading to potential premature eviction.\n\n### Proposed Solution\n1. Use `env.storage().temporary().extend_ttl()` on all nonce checks.\n2. Standardize nonce validation across contract entry points.\n\n### Acceptance Criteria\n- Nonces remain available throughout active transaction life cycle.",
        "labels": [
            "blockchain",
            "security",
            "middleware"
        ]
    },
    {
        "title": "[Contracts] Implement strict slippage bounds check on swap_shares to prevent sandwich attacks",
        "body": "### Context & Problem\nTraders placing large market share swaps have no `min_shares_out` parameter, exposing them to MEV / frontrunning sandwich attacks.\n\n### Proposed Solution\n1. Add `min_shares_out: i128` parameter to `swap_shares`.\n2. Revert with `SlippageExceeded` if received shares fall below the minimum.\n\n### Acceptance Criteria\n- Swaps revert if calculated output < `min_shares_out`.\n- Integration tests simulate price movement causing expected revert.",
        "labels": [
            "blockchain",
            "trading",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement minimum bet amount validation to prevent dust attack state bloat",
        "body": "### Context & Problem\nUsers can place 1-stroop bets repeatedly, bloating contract state and consuming storage without contributing liquidity.\n\n### Proposed Solution\n1. Define a global constant `MIN_BET_AMOUNT` in `shared/src/lib.rs`.\n2. Validate bet amount >= `MIN_BET_AMOUNT` before processing.\n\n### Acceptance Criteria\n- Bets below threshold revert with `AmountTooLow`.\n- Legitimate bets proceed without issues.",
        "labels": [
            "blockchain",
            "predictions",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement emergency pause circuit breaker across all market interactions",
        "body": "### Context & Problem\nIn the event of an exploit or oracle failure, administrators need an instant circuit breaker to pause swaps, bets, and dispute resolutions.\n\n### Proposed Solution\n1. Add `paused: bool` in market contract storage.\n2. Add `set_paused(admin, bool)` with admin authentication.\n3. Guard all mutation functions with `require(!paused)`.\n\n### Acceptance Criteria\n- When paused, all bets, swaps, and withdrawals revert with `ContractPaused`.\n- Only admin can pause/unpause.",
        "labels": [
            "blockchain",
            "security",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement dispute resolution appeal cooldown window before final payout",
        "body": "### Context & Problem\nImmediately after an initial dispute ruling, funds are distributed without allowing an appeal window, preventing community governance intervention.\n\n### Proposed Solution\n1. Introduce an `appeal_window_end` timestamp.\n2. Require payout execution to happen only after `env.ledger().timestamp() >= appeal_window_end`.\n\n### Acceptance Criteria\n- Payout claims during appeal window revert.\n- Payout claims after appeal window succeed.",
        "labels": [
            "blockchain",
            "disputes",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement dynamic fee split configuration in treasury with basis point bounds",
        "body": "### Context & Problem\nTreasury contract has hardcoded fee distribution percentages, preventing governance from adjusting splits between treasury, LP rewards, and burns.\n\n### Proposed Solution\n1. Add `set_fee_split(admin, treasury_bps, lp_bps, burn_bps)` verifying sum equals 10,000 bps (100%).\n2. Apply configured split on all fee allocations.\n\n### Acceptance Criteria\n- Invalid splits (sum != 10000) revert.\n- Treasury correctly routes tokens per configured percentages.",
        "labels": [
            "blockchain",
            "treasury",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement partial order matching support for limit-style share orders",
        "body": "### Context & Problem\nCurrently, users can only execute AMM market orders; there is no capability to place limit orders that execute when target odds are reached.\n\n### Proposed Solution\n1. Create an order storage structure with price limit, amount, and expiry.\n2. Match incoming swaps against resting limit orders before routing to the CPMM curve.\n\n### Acceptance Criteria\n- Partial fills update remaining order size.\n- Cancel order returns unspent balance to creator.",
        "labels": [
            "blockchain",
            "trading",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement automated contract event emissions for all state transitions",
        "body": "### Context & Problem\nSome contract functions (such as dispute opening and fee updates) do not emit Soroban topics/events, forcing indexers to poll raw ledger entries.\n\n### Proposed Solution\n1. Define typed event structures for: `MarketCreated`, `BetPlaced`, `MarketResolved`, `DisputeOpened`, `FeesClaimed`.\n2. Emit events with indexed topics for contract ID, user address, and action.\n\n### Acceptance Criteria\n- Every critical state change emits a corresponding Soroban event.\n- Events follow unified schema matching indexer expectations.",
        "labels": [
            "blockchain",
            "markets",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement daily withdrawal velocity limits per recipient in treasury contract",
        "body": "### Context & Problem\nA compromised admin or authorized recipient can drain entire treasury balances in a single transaction.\n\n### Proposed Solution\n1. Maintain rolling 24-hour withdrawal totals per address in treasury contract.\n2. Reject withdrawals exceeding `daily_limit` unless a multi-day timelock is initiated.\n\n### Acceptance Criteria\n- Cumulative withdrawals within 24h exceeding limit revert.\n- Daily counters reset correctly after 24h window.",
        "labels": [
            "blockchain",
            "treasury",
            "security"
        ]
    },
    {
        "title": "[Contracts] Implement multi-token collateral support with Soroban token client validation",
        "body": "### Context & Problem\nMarkets currently only support native XLM / standard test token; market creators cannot use verified stablecoins (e.g. USDC).\n\n### Proposed Solution\n1. Support arbitrary Stellar Asset Contract (SAC) token addresses in `create_market`.\n2. Validate token contract interface compatibility upon initialization.\n\n### Acceptance Criteria\n- Markets accept arbitrary Soroban-compatible token addresses.\n- Balance and transfers correctly interact with specified token client.",
        "labels": [
            "blockchain",
            "markets",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement formal property-based fuzz tests for CPMM invariant k = x * y",
        "body": "### Context & Problem\nNumerical precision loss and potential invariant drain attacks have not been tested with arbitrary random inputs.\n\n### Proposed Solution\n1. Add property-based testing harness using `proptest` or `quickcheck`.\n2. Assert that `k_after >= k_before` holds for all non-zero swaps and liquidity additions.\n\n### Acceptance Criteria\n- Fuzz tests execute 10,000+ random swap sequences without invariant violation.\n- Edge case bounds (min/max integer limits) are covered.",
        "labels": [
            "blockchain",
            "testing",
            "security"
        ]
    },
    {
        "title": "[Contracts] Implement unit test suite for dispute escalation and voting quorum",
        "body": "### Context & Problem\nTest coverage for the multi-tiered dispute escalation mechanism in `contracts/market/src/dispute.rs` is incomplete.\n\n### Proposed Solution\n1. Add comprehensive test cases for: invalid disputes, quorum not met, quorum met with overturn, tie-breaker handling.\n2. Verify token transfers and state transitions at every step.\n\n### Acceptance Criteria\n- Test coverage for dispute module reaches >= 90%.\n- All dispute paths pass cleanly in CI.",
        "labels": [
            "blockchain",
            "testing",
            "disputes"
        ]
    },
    {
        "title": "[Contracts] Implement gas and CPU instruction profiling benchmarks for market execution",
        "body": "### Context & Problem\nHigh compute and storage metering can cause Soroban transactions to hit ledger resource limits under high market activity.\n\n### Proposed Solution\n1. Write benchmark scripts using `soroban-sdk` budget inspection APIs.\n2. Measure CPU cycles and memory footprint for `swap_shares`, `claim_winnings`, and `resolve_market`.\n\n### Acceptance Criteria\n- Benchmark reports generated and added to `contracts/benchmarks.md`.\n- Optimizations reduce swap transaction budget by at least 15%.",
        "labels": [
            "blockchain",
            "testing",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement contract upgradeability pattern via WASM hash migration in factory",
        "body": "### Context & Problem\nBug fixes in market contracts cannot be applied to existing deployed instances without manual migration paths.\n\n### Proposed Solution\n1. Implement `upgrade(new_wasm_hash)` in market contracts restricted to factory/admin.\n2. Use Soroban `env.deployer().update_current_contract_wasm(new_wasm_hash)`.\n\n### Acceptance Criteria\n- Authorized upgrades update code while preserving storage.\n- Unauthorized upgrade attempts revert.",
        "labels": [
            "blockchain",
            "security",
            "feature"
        ]
    },
    {
        "title": "[Contracts] Implement automated contract size verification in build script",
        "body": "### Context & Problem\nSoroban has a strict limit on compiled contract WASM bytecode size. Large contracts risk build failure in production.\n\n### Proposed Solution\n1. Add a build script that optimizes WASM via `soroban contract optimize`.\n2. Fail CI if compiled binary exceeds 64KB threshold.\n\n### Acceptance Criteria\n- Build script logs WASM size.\n- Pre-merge checks enforce budget limit.",
        "labels": [
            "blockchain",
            "testing",
            "middleware"
        ]
    },
    {
        "title": "[Backend] Fix unhandled Promise rejections causing backend crash on Postgres pool timeout",
        "body": "### Context & Problem\nWhen database connection pool runs out of available clients or encounters a network timeout, unhandled rejections crash the Node.js server process.\n\n### Proposed Solution\n1. Wrap pool acquisition and query executions in standard try/catch blocks with exponential retry.\n2. Add global `process.on('unhandledRejection')` and `process.on('uncaughtException')` handlers with graceful shutdown.\n\n### Acceptance Criteria\n- DB timeouts return 503 Service Unavailable instead of process termination.\n- Connection pool recovers automatically.",
        "labels": [
            "backend",
            "bug",
            "middleware"
        ]
    },
    {
        "title": "[Backend] Fix missing transaction isolation level causing race condition in simultaneous bets",
        "body": "### Context & Problem\nConcurrent bet placement requests from the same user can lead to double-spending off-chain cached balances because queries run in default Read Committed mode.\n\n### Proposed Solution\n1. Wrap balance checks and bet placement in a serializable transaction: `tx.transaction(async (trx) => { ... }, { isolationLevel: 'serializable' })`.\n2. Use `FOR UPDATE` row-level locks on user balance records.\n\n### Acceptance Criteria\n- Simultaneous bet requests are executed atomically without balance drift.\n- Stress test verifies zero double-spends.",
        "labels": [
            "backend",
            "security",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix JWT session invalidation bypass on password reset and role changes",
        "body": "### Context & Problem\nWhen a user resets their password or is banned by admin, previously issued JWT tokens remain valid until expiration (up to 7 days).\n\n### Proposed Solution\n1. Add `token_version` column to the `users` table.\n2. Include `token_version` in the JWT payload and verify it against DB/Redis on every authenticated request.\n3. Increment `token_version` on password reset or account status changes.\n\n### Acceptance Criteria\n- Password change immediately invalidates all existing JWT sessions.\n- Invalid token returns 401 Unauthorized.",
        "labels": [
            "backend",
            "auth",
            "security"
        ]
    },
    {
        "title": "[Backend] Fix SQL injection risk in dynamic order filtering within MarketRepository",
        "body": "### Context & Problem\nIn `backend/src/api/repositories/MarketRepository.ts`, raw SQL string concatenation is used for dynamic sort columns and direction, presenting SQL injection vectors.\n\n### Proposed Solution\n1. Whitelist acceptable sort columns (`created_at`, `volume`, `liquidity`, `end_time`).\n2. Use parameterized Drizzle ORM column references instead of string interpolation.\n\n### Acceptance Criteria\n- Arbitrary SQL fragments in query params are rejected with 400 Bad Request.\n- Valid sort options function as expected.",
        "labels": [
            "backend",
            "security",
            "repository"
        ]
    },
    {
        "title": "[Backend] Fix unbounded pagination queries on /api/governance/proposals and /api/markets",
        "body": "### Context & Problem\nQuerying `/api/markets` without a `limit` parameter loads all historical records into Node.js heap memory, resulting in high latency and OOM crashes.\n\n### Proposed Solution\n1. Enforce default limit = 20 and maximum limit = 100 in pagination middleware.\n2. Add cursor-based pagination using `id` or `created_at` index for high-scale performance.\n\n### Acceptance Criteria\n- Requests with `limit > 100` are clamped or rejected with validation error.\n- Memory usage remains bounded under large datasets.",
        "labels": [
            "backend",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix missing rate limiter on /api/auth/login and /api/auth/reset-password",
        "body": "### Context & Problem\nAuthentication endpoints lack IP and user-based rate limiting, allowing credential stuffing and brute force attacks.\n\n### Proposed Solution\n1. Implement `express-rate-limit` with Redis store on `/api/auth/login` (5 attempts per 15 min).\n2. Add progressive delay backoff for failed attempts.\n\n### Acceptance Criteria\n- Exceeding 5 failed attempts returns 429 Too Many Requests with `Retry-After` header.\n- Successful login resets failure counter.",
        "labels": [
            "backend",
            "auth",
            "security"
        ]
    },
    {
        "title": "[Backend] Fix CORS configuration wildcard permitting unauthorized origins in production",
        "body": "### Context & Problem\nCORS middleware uses `origin: \"*\"` when `NODE_ENV=production`, exposing internal API endpoints to cross-site request forgery and data exfiltration.\n\n### Proposed Solution\n1. Restrict CORS origins to an explicit whitelist configured via `ALLOWED_ORIGINS` environment variable.\n2. Reject requests with missing or unauthorized `Origin` headers in production.\n\n### Acceptance Criteria\n- Production requests from untrusted origins are blocked with CORS error.\n- Trusted domains pass cleanly.",
        "labels": [
            "backend",
            "security",
            "middleware"
        ]
    },
    {
        "title": "[Backend] Fix inconsistent error response format between Express middlewares and controllers",
        "body": "### Context & Problem\nValidation errors return `{ error: string }`, while controller errors return `{ success: false, message: string }`, complicating frontend error handling.\n\n### Proposed Solution\n1. Standardize error format: `{ success: false, error: { code: string, message: string, details?: any } }`.\n2. Refactor centralized `errorHandler` middleware to format all standard and custom `AppError` instances.\n\n### Acceptance Criteria\n- All 4xx and 5xx responses adhere to the standard JSON error schema.\n- Frontend error handler reliably parses all backend errors.",
        "labels": [
            "backend",
            "middleware",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix date validation parsing in useCreateMarket backend counterpart endpoint",
        "body": "### Context & Problem\nThe `/api/markets` creation endpoint accepts timestamp values that parse as NaN, failing to validate minimum market duration (e.g. at least 1 hour in the future).\n\n### Proposed Solution\n1. Add Joi/Zod validation asserting `scheduledAt` is a valid ISO date >= `Date.now() + 3600000`.\n2. Return descriptive validation errors.\n\n### Acceptance Criteria\n- Past or malformed dates are rejected with 400 Bad Request.\n- Markets must have a duration of at least 1 hour.",
        "labels": [
            "backend",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix memory leak in WebSocket connection manager when clients disconnect abruptly",
        "body": "### Context & Problem\nWhen clients close WebSocket connections abruptly without TCP FIN handshake, socket references remain stored in `activeConnections` map, leading to memory leaks.\n\n### Proposed Solution\n1. Listen for socket `close` and `error` events and clean up channel subscription sets.\n2. Implement 30-second ping/pong heartbeat to identify and prune dead connections.\n\n### Acceptance Criteria\n- Disconnected sockets are removed from memory within 60 seconds.\n- Memory remains stable under continuous reconnect loops.",
        "labels": [
            "backend",
            "websocket",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix missing database index on events.sequence_number causing full table scans",
        "body": "### Context & Problem\nQueries querying indexer events by ledger sequence perform full table scans across millions of rows, slowing down indexer synchronization.\n\n### Proposed Solution\n1. Add migration: `CREATE INDEX CONCURRENTLY events_sequence_number_idx ON events(sequence_number);`.\n2. Add composite index on `(contract_id, sequence_number)` for filtered event queries.\n\n### Acceptance Criteria\n- Query execution plan shows Index Scan instead of Seq Scan.\n- Synchronization query time drops below 5ms.",
        "labels": [
            "backend",
            "repository",
            "blockchain"
        ]
    },
    {
        "title": "[Backend] Fix transaction export endpoint failing with 500 when exporting >10,000 rows",
        "body": "### Context & Problem\n`GET /api/transactions/export` buffers all matching rows into memory before generating CSV, crashing on large user account histories.\n\n### Proposed Solution\n1. Stream database query results directly to HTTP response using Postgres cursor and `csv-stringify/sync`.\n2. Limit export date range to a maximum of 90 days.\n\n### Acceptance Criteria\n- Exports stream efficiently without buffering entire dataset in RAM.\n- Queries over 90 days return 400 Bad Request with guidance.",
        "labels": [
            "backend",
            "wallet",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix TOTP two-factor authentication single-use backup codes being reusable",
        "body": "### Context & Problem\nBackup recovery codes generated during 2FA setup are not marked as used upon login, allowing replay attacks.\n\n### Proposed Solution\n1. Store backup codes as hashed values with a `used_at: timestamp` flag.\n2. Invalidate code immediately upon first successful redemption in the same database transaction.\n\n### Acceptance Criteria\n- Reusing a redeemed backup code returns 401 Invalid Code.\n- Remaining unused codes continue to function.",
        "labels": [
            "backend",
            "auth",
            "security"
        ]
    },
    {
        "title": "[Backend] Fix health check endpoint /health coupling with external Soroban RPC status",
        "body": "### Context & Problem\nWhen external Soroban RPC provider experiences transient latency, the entire backend `/health` endpoint returns 500, causing Kubernetes / Docker to restart healthy backend pods.\n\n### Proposed Solution\n1. Separate `/health/live` (checks process liveness) from `/health/ready` (checks DB and RPC dependencies).\n2. Set graceful timeouts on external RPC checks so transient hiccups do not report pod failure.\n\n### Acceptance Criteria\n- Container liveness probe remains green during upstream RPC degradation.\n- Readiness probe accurately reports dependency health.",
        "labels": [
            "backend",
            "middleware",
            "bug"
        ]
    },
    {
        "title": "[Backend] Fix market analytics N+1 query when fetching market outcome odds history",
        "body": "### Context & Problem\nFetching the list of markets triggers individual queries for each market's historical odds datapoints, resulting in 100+ DB queries per page request.\n\n### Proposed Solution\n1. Use SQL `JOIN` with `JSON_AGG` or window functions to fetch latest odds snapshots in a single query.\n2. Cache historical odds in Redis with 30-second TTL.\n\n### Acceptance Criteria\n- Single DB query fulfills market list + odds endpoint.\n- Endpoint response time reduced by >80%.",
        "labels": [
            "backend",
            "markets",
            "repository"
        ]
    },
    {
        "title": "[Backend] Implement request payload schema validation using Zod for all POST/PUT routes",
        "body": "### Context & Problem\nSeveral controller endpoints parse `req.body` directly without schema validation, allowing unexpected fields and invalid types to reach business logic.\n\n### Proposed Solution\n1. Define Zod schemas for all route inputs (markets, predictions, profile, disputes).\n2. Create reusable validation middleware `validateBody(schema)`.\n\n### Acceptance Criteria\n- Malformed payloads return detailed 422 Unprocessable Entity errors.\n- Valid payloads are safely typed throughout controller code.",
        "labels": [
            "backend",
            "middleware",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement structured JSON logging with correlation ID tracing via Pino",
        "body": "### Context & Problem\nBackend logs use unstructured `console.log` statements, making distributed tracing and error diagnosis difficult in production.\n\n### Proposed Solution\n1. Replace `console.log` with `pino` logger.\n2. Attach `x-correlation-id` to incoming requests and forward it across logs and external service calls.\n\n### Acceptance Criteria\n- All logs output standardized JSON with timestamps, log levels, and correlation IDs.\n- Log aggregation tools can parse and trace requests seamlessly.",
        "labels": [
            "backend",
            "middleware",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement Redis caching layer for high-throughput market odds and leaderboard endpoints",
        "body": "### Context & Problem\nLeaderboard and active market endpoints receive heavy traffic, creating unnecessary database read load.\n\n### Proposed Solution\n1. Integrate Redis client with automatic fallback if Redis is unavailable.\n2. Cache leaderboard results for 60 seconds and market odds for 5 seconds.\n3. Invalidate cache on market resolution or large trades.\n\n### Acceptance Criteria\n- Cache hits serve in < 5ms without DB interaction.\n- Invalidation maintains data freshness.",
        "labels": [
            "backend",
            "leaderboard",
            "markets"
        ]
    },
    {
        "title": "[Backend] Implement idempotent webhook delivery mechanism with HMAC-SHA256 signatures",
        "body": "### Context & Problem\nWebhooks sent to external partners or consumers can fail on network errors and lack cryptographic verification.\n\n### Proposed Solution\n1. Add webhook event queue with exponential retry backoff.\n2. Sign webhook payloads with HMAC-SHA256 using partner secret.\n3. Include `X-Webhook-Signature` and `X-Event-ID` headers for idempotency.\n\n### Acceptance Criteria\n- Webhooks deliver with valid HMAC signatures.\n- Failed deliveries retry up to 5 times before moving to DLQ.",
        "labels": [
            "backend",
            "notifications",
            "security"
        ]
    },
    {
        "title": "[Backend] Implement audit logging table capturing all administrative and dispute actions",
        "body": "### Context & Problem\nAdmin actions (market resolution, bans, config updates) are not recorded in an immutable audit trail, creating compliance and security risks.\n\n### Proposed Solution\n1. Create `audit_logs` table: `id`, `actor_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `before_state`, `after_state`, `timestamp`.\n2. Add middleware logging all admin actions automatically.\n\n### Acceptance Criteria\n- Every privileged action creates an immutable audit record.\n- Audit records can be queried by security admins.",
        "labels": [
            "backend",
            "security",
            "repository"
        ]
    },
    {
        "title": "[Backend] Implement automated database backup and point-in-time recovery strategy",
        "body": "### Context & Problem\nThere is no automated script or verification process for database backups, exposing the platform to data loss in case of hardware failure.\n\n### Proposed Solution\n1. Create automated pg_dump backup script with S3 / cloud storage upload.\n2. Implement weekly automated restore verification test in staging.\n\n### Acceptance Criteria\n- Backup script executes cleanly via cron.\n- Documented recovery time objective (RTO) < 1 hour.",
        "labels": [
            "backend",
            "repository",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement WebSocket heartbeat ping/pong mechanism to prune dead client sockets",
        "body": "### Context & Problem\nZombie WebSocket connections consume system file descriptors and memory.\n\n### Proposed Solution\n1. Server sends ping frame every 30 seconds to all connected clients.\n2. Terminate socket if pong is not received within 10 seconds.\n\n### Acceptance Criteria\n- Stale connections are pruned automatically.\n- Total connection count accurately reflects active clients.",
        "labels": [
            "backend",
            "websocket",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement user referral tree depth capping and commission calculation bounds",
        "body": "### Context & Problem\nReferral payouts lack depth bounds, creating risk of unbounded recursion during payout calculation.\n\n### Proposed Solution\n1. Limit referral tree traversal to 2 tiers (direct and tier-2).\n2. Validate total referral commission cap (maximum 5% of trading fee).\n\n### Acceptance Criteria\n- Referral calculations execute in O(1) time complexity.\n- Total commission payout never exceeds allotted fee percentage.",
        "labels": [
            "backend",
            "referrals",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement OpenAPI/Swagger schema synchronization validation in CI pipeline",
        "body": "### Context & Problem\n`backend/openapi.yaml` frequently falls out of sync with actual controller routes and payload structures.\n\n### Proposed Solution\n1. Add a CI check comparing OpenAPI spec endpoints against registered Express routes.\n2. Use `swagger-parser` to validate YAML syntax and schema correctness.\n\n### Acceptance Criteria\n- CI fails if routes exist without OpenAPI documentation or if spec contains syntax errors.",
        "labels": [
            "backend",
            "testing",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement social feature profanity and spam filter for market comments",
        "body": "### Context & Problem\nMarket comments lack content moderation, allowing spam, phishing URLs, and profanity to be posted freely.\n\n### Proposed Solution\n1. Implement text filtering middleware checking comments against profanity blocklist.\n2. Restrict URL posting to verified domains or block URLs for unverified users.\n\n### Acceptance Criteria\n- Prohibited words and suspicious links are blocked with 400 Bad Request.\n- Rate limiting prevents comment spamming.",
        "labels": [
            "backend",
            "users",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement activity privacy filter for user betting history",
        "body": "### Context & Problem\nUser profile betting history is publicly exposed without option for privacy controls.\n\n### Proposed Solution\n1. Add `is_profile_private: boolean` to user settings.\n2. Obfuscate or hide prediction history from public view if privacy is enabled.\n\n### Acceptance Criteria\n- Private profiles hide bet amounts and market specifics from other users.\n- User can always view their own history.",
        "labels": [
            "backend",
            "users",
            "feature"
        ]
    },
    {
        "title": "[Backend] Implement automated database migration rollback scripts and smoke tests",
        "body": "### Context & Problem\nDatabase migrations only have `up` scripts; failed deployments cannot be automatically rolled back.\n\n### Proposed Solution\n1. Write corresponding `down` migration scripts for all schema changes in `backend/migrations`.\n2. Add CI test that runs `migrate up` followed by `migrate down` and verifies clean schema state.\n\n### Acceptance Criteria\n- Both up and down migrations execute cleanly in test environment.\n- Documentation added for rollback procedures.",
        "labels": [
            "backend",
            "repository",
            "testing"
        ]
    },
    {
        "title": "[Backend] Implement end-to-end integration tests for user authentication and session lifecycle",
        "body": "### Context & Problem\nAuthentication flow (register, verify, login, refresh token, 2FA, logout) lacks comprehensive automated integration tests.\n\n### Proposed Solution\n1. Build test suite using Jest and Supertest exercising full auth lifecycle.\n2. Test token expiration, refresh rotation, and revocation scenarios.\n\n### Acceptance Criteria\n- Auth integration test suite achieves >95% statement coverage.\n- All tests execute in CI without flakes.",
        "labels": [
            "backend",
            "auth",
            "testing"
        ]
    },
    {
        "title": "[Backend] Implement test suite for market resolution payout calculation service",
        "body": "### Context & Problem\nEdge cases in outcome payout distribution (e.g., ties, cancelled markets, zero winning bets) lack dedicated unit tests.\n\n### Proposed Solution\n1. Create unit tests covering binary, categorical, and cancelled resolution states.\n2. Verify precision and rounding behavior under fractional shares.\n\n### Acceptance Criteria\n- 100% of calculation branches covered with assertions.\n- Verified zero token leakage across all scenarios.",
        "labels": [
            "backend",
            "testing",
            "predictions"
        ]
    },
    {
        "title": "[Backend] Implement Prometheus metrics endpoint /metrics for API latency and error rates",
        "body": "### Context & Problem\nProduction monitoring lacks visibility into endpoint latency percentiles (p50, p95, p99) and HTTP error code distributions.\n\n### Proposed Solution\n1. Use `prom-client` to collect HTTP request durations, active socket counts, and database query durations.\n2. Expose `/metrics` endpoint protected by basic auth or internal network restriction.\n\n### Acceptance Criteria\n- Prometheus successfully scrapes metrics.\n- Standard metrics (requests total, duration histogram, memory usage) are published.",
        "labels": [
            "backend",
            "middleware",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Fix indexer crash on unexpected event topic formatting from unverified contracts",
        "body": "### Context & Problem\nIf an unverified contract or malicious actor emits events targeting the indexer address with malformed topics, `indexer/src/poller.ts` crashes on JSON/XDR decode.\n\n### Proposed Solution\n1. Wrap event decoding in `safeDecodeXdr` try/catch block.\n2. Log malformed events to a dead-letter queue and continue processing remaining ledger events.\n\n### Acceptance Criteria\n- Malformed XDR events are safely bypassed without terminating the indexer thread.\n- Metrics counter `indexer_malformed_events_total` increments.",
        "labels": [
            "blockchain",
            "bug",
            "cron"
        ]
    },
    {
        "title": "[Indexer] Fix ledger gap recovery skipping event batches when Soroban RPC lags behind",
        "body": "### Context & Problem\nWhen the Soroban RPC node temporarily desyncs and skips ledgers, the indexer advances its cursor without detecting missed event sequences.\n\n### Proposed Solution\n1. Track expected `last_processed_ledger`.\n2. If `new_ledger > last_processed_ledger + 1`, enter gap recovery mode to backfill missed ledgers sequentially.\n\n### Acceptance Criteria\n- No ledgers are skipped during network disruptions.\n- Gap recovery logs clear progress and resumes normal polling once caught up.",
        "labels": [
            "blockchain",
            "bug",
            "cron"
        ]
    },
    {
        "title": "[Indexer] Fix cursor non-atomic persistence causing duplicate event processing on restart",
        "body": "### Context & Problem\nEvent records are inserted into the database, but cursor state is saved in a separate non-transactional step. A crash in between results in re-processing already ingested events.\n\n### Proposed Solution\n1. Save event batch insertions and cursor updates inside a single database transaction: `BEGIN ... INSERT events ... UPDATE cursor ... COMMIT`.\n\n### Acceptance Criteria\n- Cursor updates atomically with event records.\n- Zero duplicate processing after abrupt process kill.",
        "labels": [
            "blockchain",
            "repository",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix unhandled RPC 429 rate limit errors crashing the indexer poller thread",
        "body": "### Context & Problem\nPublic and private Soroban RPC nodes return HTTP 429 when rate limits are exceeded, which causes uncaught errors in the polling loop.\n\n### Proposed Solution\n1. Catch 429 errors and extract `Retry-After` header if present.\n2. Apply exponential backoff with randomized jitter (e.g. 1s, 2s, 4s, up to 30s) before retrying.\n\n### Acceptance Criteria\n- 429 errors trigger backoff rather than crash.\n- Poller gracefully resumes once rate limit resets.",
        "labels": [
            "blockchain",
            "cron",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix memory leak in indexer event queue under sustained high transaction volume",
        "body": "### Context & Problem\nEvents fetched from RPC are pushed to an in-memory array that grows unbounded if database ingestion throughput falls behind.\n\n### Proposed Solution\n1. Introduce a bounded queue (e.g. max 5,000 items) with backpressure.\n2. Pause RPC polling when queue reaches 80% capacity until DB writer catches up.\n\n### Acceptance Criteria\n- Heap memory usage remains flat under extreme event ingestion load.\n- Backpressure pauses and resumes polling cleanly.",
        "labels": [
            "blockchain",
            "cron",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix duplicate event ingestion on network reorgs using database unique constraints",
        "body": "### Context & Problem\nWhen a short ledger reorganization occurs, re-emitted events with the same transaction hash create duplicate records in the database.\n\n### Proposed Solution\n1. Add unique constraint: `UNIQUE (transaction_hash, event_index)`.\n2. Use `ON CONFLICT (transaction_hash, event_index) DO NOTHING` on event inserts.\n\n### Acceptance Criteria\n- Duplicate events are silently skipped without error.\n- Event table integrity is preserved.",
        "labels": [
            "blockchain",
            "repository",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix missing indexer heartbeat metric causing silent failure in monitoring",
        "body": "### Context & Problem\nIf the polling loop hangs due to an unhandled socket promise, no process exit occurs, making it appear healthy to health checks while no new events are indexed.\n\n### Proposed Solution\n1. Update `last_polled_timestamp` in memory every polling cycle.\n2. Expose health check that returns 500 if `Date.now() - last_polled_timestamp > 60000`.\n\n### Acceptance Criteria\n- Stalled pollers fail health check and trigger container restart.\n- Metric `indexer_last_polled_timestamp_seconds` published to Prometheus.",
        "labels": [
            "blockchain",
            "cron",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix race condition in concurrent block processing corrupting outcome token balances",
        "body": "### Context & Problem\nRunning multiple worker threads to index blocks concurrently causes race conditions when two blocks update the same market's pool reserves out of order.\n\n### Proposed Solution\n1. Ensure events for a given `market_id` are processed strictly in ledger sequence order.\n2. Use partition-based worker routing or sequential processing per contract ID.\n\n### Acceptance Criteria\n- Market pool balances match contract state exactly at every ledger height.\n- Out-of-order execution is prevented.",
        "labels": [
            "blockchain",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix unhandled JSON-RPC socket connection drops without automatic reconnect",
        "body": "### Context & Problem\nWebSocket / persistent HTTP connections to the Stellar RPC node close after network idle timeouts, leaving the indexer idle permanently.\n\n### Proposed Solution\n1. Implement keep-alive ping and reconnect listener on the RPC provider client.\n2. Reset and re-establish connection if no message is received within 45 seconds.\n\n### Acceptance Criteria\n- Dropped socket connections reconnect automatically within 5 seconds.\n- Poller resumes without manual intervention.",
        "labels": [
            "blockchain",
            "websocket",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Fix timestamp desynchronization between ledger close time and ingestion timestamp",
        "body": "### Context & Problem\nEvents currently store `ingested_at = NOW()` instead of the actual Stellar ledger close timestamp, distorting historical chart timeframes.\n\n### Proposed Solution\n1. Extract `ledger_closed_at` from block header and persist it as `event_timestamp`.\n2. Use `event_timestamp` for all frontend candle and analytics calculations.\n\n### Acceptance Criteria\n- Event records store true on-chain ledger timestamp.\n- Chart time series data matches blockchain history.",
        "labels": [
            "blockchain",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Indexer] Implement exponential backoff with jitter on Soroban RPC connection failures",
        "body": "### Context & Problem\nImmediate retry on connection failures hammers struggling RPC servers and risks getting IP blacklisted.\n\n### Proposed Solution\n1. Implement full jitter algorithm: `sleep = min(MAX_SLEEP, rand(0, BASE * 2^attempt))`.\n2. Log connection attempts and retry status clearly.\n\n### Acceptance Criteria\n- Reconnect attempts back off smoothly without thundering herd problems.",
        "labels": [
            "blockchain",
            "cron",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement configurable batch size and polling interval via environment variables",
        "body": "### Context & Problem\nBatch size (100) and polling interval (2000ms) are hardcoded, preventing tuning for testnet vs mainnet environments.\n\n### Proposed Solution\n1. Read `INDEXER_BATCH_SIZE` and `INDEXER_POLL_INTERVAL_MS` from environment with sensible defaults.\n2. Validate values on startup.\n\n### Acceptance Criteria\n- Operators can tune polling speed via environment variables without code modification.",
        "labels": [
            "blockchain",
            "cron",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement WebSocket event dispatcher decoupling indexing from socket broadcasting",
        "body": "### Context & Problem\nBroadcasting events to thousands of connected frontend WebSocket clients directly within the polling loop slows down blockchain ingestion.\n\n### Proposed Solution\n1. Publish indexed events to a Redis Pub/Sub channel (`events:market:<id>`).\n2. Have API server WebSocket workers consume Redis channels independently.\n\n### Acceptance Criteria\n- Indexer loop processing time is independent of connected client count.\n- Broadcast latency remains under 50ms.",
        "labels": [
            "blockchain",
            "websocket",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement dead-letter queue (DLQ) for failed event ingestion records",
        "body": "### Context & Problem\nWhen an event fails to process due to a business logic error, it either halts the entire indexer or is dropped without trace.\n\n### Proposed Solution\n1. Create `failed_events` table storing payload, error message, stack trace, and retry count.\n2. Provide admin CLI command `npm run indexer:retry-dlq` to re-process failed items.\n\n### Acceptance Criteria\n- Poison pill events are quarantined to DLQ while indexer continues.\n- Admins can inspect and re-drive failed events.",
        "labels": [
            "blockchain",
            "repository",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement ledger sequence lag reporting and alerting threshold",
        "body": "### Context & Problem\nThere is no metric tracking how many ledgers the indexer is behind the Stellar network tip.\n\n### Proposed Solution\n1. Query network latest ledger height periodically.\n2. Calculate and export `indexer_ledger_lag = network_latest - last_processed_ledger`.\n3. Alert if lag > 50 ledgers for > 5 minutes.\n\n### Acceptance Criteria\n- Lag metric is exposed and visible in Grafana.\n- Threshold violations trigger alerts.",
        "labels": [
            "blockchain",
            "cron",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement indexer data pruning routine for historical low-priority events",
        "body": "### Context & Problem\nRaw event logs accumulate gigabytes of data over time, increasing database hosting costs and backup times.\n\n### Proposed Solution\n1. Implement scheduled monthly cron job archiving events older than 180 days to cold storage (e.g. Parquet / S3).\n2. Retain aggregated market summaries in active database.\n\n### Acceptance Criteria\n- Pruning runs without locking active tables.\n- Historical queries fall back to archive gracefully.",
        "labels": [
            "blockchain",
            "cron",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement event schema validation before persisting to Postgres tables",
        "body": "### Context & Problem\nUnvalidated event payloads can insert unexpected nulls or malformed JSON into the database.\n\n### Proposed Solution\n1. Validate event payloads against Zod schemas matching contract event definitions.\n2. Reject non-conforming events to DLQ.\n\n### Acceptance Criteria\n- Database contains only strictly typed, valid event structures.",
        "labels": [
            "blockchain",
            "repository",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement snapshot replay mechanism for re-indexing from specific ledger heights",
        "body": "### Context & Problem\nWhen bugs are fixed in event parsing, developers must wipe the entire database to re-index from scratch.\n\n### Proposed Solution\n1. Add CLI flag `--from-ledger <number>` and `--to-ledger <number>`.\n2. Allow selective re-indexing of specific contracts or block ranges with upsert semantics.\n\n### Acceptance Criteria\n- CLI allows re-indexing targeted ledger intervals without wiping unaffected data.",
        "labels": [
            "blockchain",
            "cron",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement integration tests with mock Soroban RPC server simulating reorgs",
        "body": "### Context & Problem\nIndexer resilience during network forks and reorgs is untested in automated CI.\n\n### Proposed Solution\n1. Build mock RPC test server that simulates ledger forks, skipped sequences, and 429 rate limits.\n2. Verify indexer handles all fault conditions cleanly.\n\n### Acceptance Criteria\n- Comprehensive test suite validates recovery scenarios in CI.",
        "labels": [
            "blockchain",
            "testing",
            "feature"
        ]
    },
    {
        "title": "[Indexer] Implement Docker healthcheck verifying indexer ledger processing freshness",
        "body": "### Context & Problem\nThe indexer container in `docker-compose.yml` lacks a healthcheck, preventing orchestrators from restarting hung containers.\n\n### Proposed Solution\n1. Add healthcheck script checking timestamp of last processed event in DB.\n2. Configure `healthcheck` in `docker-compose.yml`.\n\n### Acceptance Criteria\n- Unhealthy indexer container status triggers restart automatically.",
        "labels": [
            "blockchain",
            "testing",
            "middleware"
        ]
    },
    {
        "title": "[Frontend] Fix Next.js hydration error caused by server-rendered locale-specific dates",
        "body": "### Context & Problem\nRendering market expiration dates with `toLocaleDateString()` produces different outputs on the Node.js server vs browser, triggering React hydration mismatch warnings.\n\n### Proposed Solution\n1. Create a `<FormattedDate date={...} />` component that renders a placeholder during SSR and updates on client mount.\n2. Alternatively, standardize on UTC format until hydration completes.\n\n### Acceptance Criteria\n- Zero hydration mismatch warnings in browser console on market pages.",
        "labels": [
            "markets",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix Freighter wallet unhandled rejection when user denies signature request",
        "body": "### Context & Problem\nWhen a user rejects a transaction signing prompt in the Freighter extension, the promise rejects without a catch block, displaying an uncaught error modal to the user.\n\n### Proposed Solution\n1. Wrap Freighter signing calls in try/catch.\n2. Display a user-friendly toast: 'Transaction was cancelled in wallet.'\n\n### Acceptance Criteria\n- Rejecting signature in wallet handles gracefully without application error.",
        "labels": [
            "wallet",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix NaN displaying in betting slip odds when market liquidity is zero",
        "body": "### Context & Problem\nWhen viewing a newly created market before initial liquidity is deposited, the odds calculation divides by zero, displaying `NaN%` and breaking the betting slip input.\n\n### Proposed Solution\n1. Guard division: if total liquidity is 0, display default odds (e.g. 50% / 50%) or disabled state 'Awaiting Liquidity'.\n2. Disable bet placement buttons until liquidity exists.\n\n### Acceptance Criteria\n- Zero-liquidity markets display clear status message without NaN.",
        "labels": [
            "markets",
            "predictions",
            "bug"
        ]
    },
    {
        "title": "[Frontend] Fix missing React Error Boundary on market trading widget causing entire page whiteout",
        "body": "### Context & Problem\nAn unhandled exception in the order book or chart component crashes the entire page tree to a white screen.\n\n### Proposed Solution\n1. Wrap `TradingWidget`, `OrderBook`, and `PriceChart` in dedicated React Error Boundaries.\n2. Render fallback UI with a 'Reload Widget' button.\n\n### Acceptance Criteria\n- Widget errors are isolated without crashing navigation or adjacent components.",
        "labels": [
            "trading",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix memory leak in WebSocket hook failing to unsubscribe on component unmount",
        "body": "### Context & Problem\n`useMarketWebSocket` hook registers event listeners on global socket manager but does not clean them up in the `useEffect` return function.\n\n### Proposed Solution\n1. Return cleanup function calling `socket.off(...)` and unsubscribe from market channel on unmount.\n\n### Acceptance Criteria\n- Listener count returns to baseline when navigating between market pages.",
        "labels": [
            "websocket",
            "bug",
            "markets"
        ]
    },
    {
        "title": "[Frontend] Fix stale market prices displayed after WebSocket reconnection",
        "body": "### Context & Problem\nWhen WebSocket reconnects after a temporary network drop, client retains stale market prices until a new trade event occurs.\n\n### Proposed Solution\n1. On WebSocket reconnect event, immediately trigger a background REST refetch of active market data.\n\n### Acceptance Criteria\n- Reconnecting socket synchronizes prices with server immediately.",
        "labels": [
            "websocket",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Frontend] Fix form submission double-click triggering duplicate Soroban transactions",
        "body": "### Context & Problem\nRapidly clicking 'Place Bet' or 'Create Market' triggers two concurrent Freighter signature prompts, leading to accidental duplicate transactions.\n\n### Proposed Solution\n1. Set button loading state immediately on first click and disable the button until transaction settles or fails.\n2. Use idempotency keys on client-side requests.\n\n### Acceptance Criteria\n- Double-clicking is prevented; only one transaction is built and submitted.",
        "labels": [
            "predictions",
            "wallet",
            "bug"
        ]
    },
    {
        "title": "[Frontend] Fix dark mode color contrast ratios failing WCAG 2.1 AA accessibility guidelines",
        "body": "### Context & Problem\nCertain text labels (muted timestamps, odds pills) have insufficient contrast in dark mode (< 4.5:1 ratio), failing accessibility audits.\n\n### Proposed Solution\n1. Adjust Tailwind color tokens in `tailwind.config.ts` for dark mode variants to guarantee >= 4.5:1 contrast.\n2. Run automated axe-core accessibility checks.\n\n### Acceptance Criteria\n- All text elements pass WCAG 2.1 AA contrast requirements.",
        "labels": [
            "feature",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix mobile viewport layout breaking on market detail order book tabs",
        "body": "### Context & Problem\nOn mobile screens (< 375px), the order book table overflows horizontally, breaking the viewport and hiding action buttons.\n\n### Proposed Solution\n1. Implement responsive horizontal scroll or compact view for mobile viewports.\n2. Ensure betting slip docks neatly to bottom of screen on mobile.\n\n### Acceptance Criteria\n- Zero horizontal overflow on screen widths down to 320px.",
        "labels": [
            "trading",
            "markets",
            "bug"
        ]
    },
    {
        "title": "[Frontend] Fix token balance not refreshing automatically after transaction confirmation",
        "body": "### Context & Problem\nAfter completing a bet or liquidity deposit, the displayed wallet token balance remains unchanged until full page refresh.\n\n### Proposed Solution\n1. Trigger global balance invalidation via React Query / SWR upon transaction confirmation receipt.\n\n### Acceptance Criteria\n- Wallet token balance updates within 2 seconds of transaction confirmation.",
        "labels": [
            "wallet",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix user notification dropdown failing to mark notifications as read",
        "body": "### Context & Problem\nClicking 'Mark all as read' in the notification dropdown updates local state but does not send the mutation to the backend API.\n\n### Proposed Solution\n1. Wire mutation to `POST /api/notifications/mark-read`.\n2. Sync unread badge count with server response.\n\n### Acceptance Criteria\n- Notifications remain marked as read across page refreshes.",
        "labels": [
            "notifications",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix XSS vulnerability in user profile bio and display name rendering",
        "body": "### Context & Problem\nUser profile bio renders raw HTML in user card without sanitization, allowing stored XSS attacks.\n\n### Proposed Solution\n1. Use `DOMPurify` to sanitize user bio text or render as plain text only.\n2. Set strict Content Security Policy (CSP) headers in Next.js configuration.\n\n### Acceptance Criteria\n- Malicious `<script>` and `onerror` payloads in bios are neutralized.",
        "labels": [
            "security",
            "users",
            "bug"
        ]
    },
    {
        "title": "[Frontend] Fix infinite re-render loop in useMarketData hook dependencies",
        "body": "### Context & Problem\n`useMarketData` defines an object literal inside `useEffect` dependency array, triggering infinite re-renders on market detail page.\n\n### Proposed Solution\n1. Memoize query options using `useMemo` and extract primitive dependencies (`marketId`).\n\n### Acceptance Criteria\n- Hook re-executes only when `marketId` actually changes.",
        "labels": [
            "markets",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Fix transaction toast notification persisting indefinitely on network timeout",
        "body": "### Context & Problem\nIf transaction polling times out, the 'Transaction in progress' toast never dismisses or transitions to error state.\n\n### Proposed Solution\n1. Add a 60-second timeout to transaction status watchers.\n2. Transition toast to 'Transaction taking longer than expected. Check Stellar Expert' with link.\n\n### Acceptance Criteria\n- Toast automatically dismisses or displays error after timeout.",
        "labels": [
            "notifications",
            "bug",
            "wallet"
        ]
    },
    {
        "title": "[Frontend] Fix dispute evidence upload failing without user-visible error on oversized files",
        "body": "### Context & Problem\nUploading evidence files > 5MB fails silently without alerting the user.\n\n### Proposed Solution\n1. Add client-side file size check before initiating upload.\n2. Display clear error: 'File exceeds 5MB limit. Please upload a smaller screenshot/PDF.'\n\n### Acceptance Criteria\n- Oversized uploads are rejected immediately with user-facing message.",
        "labels": [
            "disputes",
            "bug",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Implement optimistic UI state updates with automatic rollback on transaction failure",
        "body": "### Context & Problem\nUsers wait several seconds for Soroban transaction confirmation before seeing their bet appear in the active positions table.\n\n### Proposed Solution\n1. Immediately append pending position to local state.\n2. Revert to previous state with an error toast if transaction fails on-chain.\n\n### Acceptance Criteria\n- Bet appears instantly in UI with 'Pending confirmation' status indicator.",
        "labels": [
            "predictions",
            "trading",
            "feature"
        ]
    },
    {
        "title": "[Frontend] Implement skeleton loading states across market lists, portfolios, and leaderboards",
        "body": "### Context & Problem\nPages display blank screens or jarring layout shifts while data is loading from the API.\n\n### Proposed Solution\n1. Create reusable SVG skeleton loader components matching market card, table row, and chart dimensions.\n2. Display skeletons during loading states.\n\n### Acceptance Criteria\n- Smooth visual transition from skeleton to populated content without layout shifts.",
        "labels": [
            "markets",
            "leaderboard",
            "feature"
        ]
    },
    {
        "title": "[Frontend] Implement responsive sticky betting slip for mobile screens",
        "body": "### Context & Problem\nMobile users have to scroll back and forth between market chart and betting slip.\n\n### Proposed Solution\n1. Create bottom-sheet drawer for betting slip on viewports < 768px.\n2. Allow swipe down to minimize and tap to expand.\n\n### Acceptance Criteria\n- Mobile users can interact with betting slip seamlessly from anywhere on page.",
        "labels": [
            "trading",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Implement comprehensive form validation with clear inline error messages",
        "body": "### Context & Problem\nMarket creation form errors are only shown in a top banner, making it hard to see which input was invalid.\n\n### Proposed Solution\n1. Integrate React Hook Form with Zod resolver.\n2. Highlight invalid fields with red borders and inline explanation text.\n\n### Acceptance Criteria\n- Form fields validate on blur with clear error feedback.",
        "labels": [
            "markets",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Implement localized currency and timezone formatters across all financial tables",
        "body": "### Context & Problem\nTimestamps and currency amounts use unformatted numbers, causing confusion for global users.\n\n### Proposed Solution\n1. Create formatting utilities using `Intl.NumberFormat` and `Intl.DateTimeFormat`.\n2. Display user's local timezone alongside UTC indicator.\n\n### Acceptance Criteria\n- All numbers format with thousands separators and accurate decimal places.",
        "labels": [
            "wallet",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Implement market search and multi-facet filtering (category, status, liquidity, volume)",
        "body": "### Context & Problem\nUsers cannot easily filter markets by status (Open, Resolved, Disputed) or category (Crypto, Sports, Politics).\n\n### Proposed Solution\n1. Add interactive filter sidebar and debounce search bar.\n2. Synchronize filters with URL search params for shareable links.\n\n### Acceptance Criteria\n- Filtering updates market list instantly; URL reflects active filter state.",
        "labels": [
            "markets",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[Frontend] Implement user activity feed with real-time bet placement toasts",
        "body": "### Context & Problem\nThe platform lacks social proof and real-time excitement of ongoing market activity.\n\n### Proposed Solution\n1. Subscribe to global trade WebSocket channel.\n2. Display unobtrusive toast for recent bets over threshold ($50+).\n\n### Acceptance Criteria\n- Activity feed updates in real-time with toggle to mute in user settings.",
        "labels": [
            "notifications",
            "websocket",
            "feature"
        ]
    },
    {
        "title": "[Frontend] Implement Playwright E2E tests for wallet connection and market creation flow",
        "body": "### Context & Problem\nEnd-to-end user journeys are not tested automatically, leading to regressions in releases.\n\n### Proposed Solution\n1. Create Playwright test suite using mock wallet extension.\n2. Test end-to-end market creation and form validation.\n\n### Acceptance Criteria\n- E2E test runs headlessly in CI pipeline and passes reliably.",
        "labels": [
            "testing",
            "markets",
            "wallet"
        ]
    },
    {
        "title": "[Frontend] Implement Playwright E2E tests for placing predictions and claiming payouts",
        "body": "### Context & Problem\nPrediction placement, share redemption, and payout claiming lack automated E2E test coverage.\n\n### Proposed Solution\n1. Write Playwright test simulating full user bet lifecycle from purchase to payout claim.\n\n### Acceptance Criteria\n- Automated test verifies balance updates and success confirmation modal.",
        "labels": [
            "testing",
            "predictions",
            "trading"
        ]
    },
    {
        "title": "[Frontend] Implement client-side error telemetry reporting to Sentry",
        "body": "### Context & Problem\nFrontend JavaScript exceptions in user browsers go unnoticed unless reported manually.\n\n### Proposed Solution\n1. Configure `@sentry/nextjs` with environment-specific DSN.\n2. Capture unhandled errors and React Error Boundary events with user consent.\n\n### Acceptance Criteria\n- Errors report to Sentry dashboard with sourcemaps and breadcrumbs.",
        "labels": [
            "testing",
            "feature",
            "middleware"
        ]
    },
    {
        "title": "[Treasury] Fix quorum percentage rounding allowing proposals to pass with insufficient votes",
        "body": "### Context & Problem\nInteger division when calculating 66% supermajority quorum rounds down, allowing proposals to pass with fewer votes than legally required.\n\n### Proposed Solution\n1. Implement ceiling division for quorum: `(total_votes * required_bps + 9999) / 10000`.\n2. Ensure strict `>` or `>=` threshold enforcement.\n\n### Acceptance Criteria\n- Quorum math requires strict qualifying vote count before passing.",
        "labels": [
            "treasury",
            "bug",
            "security"
        ]
    },
    {
        "title": "[Treasury] Fix proposal vote double-counting when user transfers governance tokens mid-vote",
        "body": "### Context & Problem\nA user can vote on a proposal, transfer governance tokens to another address, and vote again on the same proposal.\n\n### Proposed Solution\n1. Implement voting snapshot mechanism based on token balance at proposal creation ledger height.\n2. Reject votes from tokens acquired after proposal start.\n\n### Acceptance Criteria\n- Tokens can only vote once per proposal based on snapshot balance.",
        "labels": [
            "treasury",
            "security",
            "bug"
        ]
    },
    {
        "title": "[Treasury] Fix oracle resolution timeout window mismatch between contract and backend cron",
        "body": "### Context & Problem\nThe backend cron attempts to trigger default resolution at 24 hours, while the smart contract requires 48 hours, causing repeated transaction failures.\n\n### Proposed Solution\n1. Align timeout constants across `contracts/shared/src/lib.rs` and `backend/src/config.ts`.\n2. Document dispute and resolution timing parameters clearly.\n\n### Acceptance Criteria\n- Automated resolution executes cleanly once contract window opens.",
        "labels": [
            "treasury",
            "oracle",
            "bug"
        ]
    },
    {
        "title": "[Treasury] Fix dispute bond confiscation failing when dispute resolves as inconclusive",
        "body": "### Context & Problem\nIf a market resolves as 'Inconclusive / Cancelled', the dispute bond is locked in the contract rather than returned to the disputer.\n\n### Proposed Solution\n1. Add logic to return 100% of dispute bond to disputer when outcome is deemed inconclusive through no fault of their own.\n\n### Acceptance Criteria\n- Bonds refund properly upon inconclusive market cancellation.",
        "labels": [
            "treasury",
            "disputes",
            "bug"
        ]
    },
    {
        "title": "[Treasury] Fix multi-sig execution authorization bypass in treasury withdrawal proposals",
        "body": "### Context & Problem\nA logic flaw in signature counting allows multiple signatures from the same authorized signer to count toward the threshold.\n\n### Proposed Solution\n1. Enforce unique signer addresses using a bitmask or set verification.\n2. Assert `unique_signers.len() >= required_signatures`.\n\n### Acceptance Criteria\n- Replay signatures from the same key are rejected with `DuplicateSigner`.",
        "labels": [
            "treasury",
            "security",
            "bug"
        ]
    },
    {
        "title": "[Treasury] Fix staking reward distribution integer truncation favoring early claimants",
        "body": "### Context & Problem\nReward rate truncation in early blocks over-allocates rewards to early stakers, leaving insufficient reward pool for subsequent stakers.\n\n### Proposed Solution\n1. Implement standard Synthetix-style `rewardPerTokenStored` accumulator with high-precision scaling (1e18).\n\n### Acceptance Criteria\n- Reward distribution remains mathematically fair across all staker deposit times.",
        "labels": [
            "treasury",
            "bug",
            "wallet"
        ]
    },
    {
        "title": "[Treasury] Fix emergency freeze failing to pause withdrawal queues in treasury",
        "body": "### Context & Problem\nTriggering `freeze()` halts new withdrawal requests but fails to pause queued withdrawals already scheduled for release.\n\n### Proposed Solution\n1. Check `!frozen` flag inside `execute_withdrawal` as well as `request_withdrawal`.\n\n### Acceptance Criteria\n- All withdrawal executions are halted while freeze is active.",
        "labels": [
            "treasury",
            "security",
            "bug"
        ]
    },
    {
        "title": "[Treasury] Fix oracle reputation score not decrementing after submitting refuted outcome",
        "body": "### Context & Problem\nWhen an oracle's reported outcome is overturned by governance dispute, the oracle's on-chain reputation score remains unchanged.\n\n### Proposed Solution\n1. Deduct reputation points upon upheld dispute and slash a portion of the oracle's staked bond.\n2. Auto-delist oracle if score drops below minimum threshold.\n\n### Acceptance Criteria\n- Erroneous oracle reports result in automatic penalty and slashing.",
        "labels": [
            "oracle",
            "disputes",
            "bug"
        ]
    },
    {
        "title": "[Treasury] Implement 2-of-3 oracle consensus validation with signature verification",
        "body": "### Context & Problem\nSingle-oracle market resolution creates centralization risk and single points of failure.\n\n### Proposed Solution\n1. Require outcome reports from at least 2 independent registered oracles.\n2. Resolve market only when reports match; trigger dispute automatically if reports conflict.\n\n### Acceptance Criteria\n- Markets resolve automatically when 2 of 3 oracles submit matching reports.",
        "labels": [
            "oracle",
            "security",
            "feature"
        ]
    },
    {
        "title": "[Treasury] Implement dispute escalation tier requiring increasing bond deposits per appeal",
        "body": "### Context & Problem\nTrivially low dispute bond amounts allow bad actors to repeatedly stall market settlements with frivolous appeals.\n\n### Proposed Solution\n1. Double the required bond deposit on each subsequent appeal tier (100 -> 200 -> 400 XLM).\n2. Cap appeals at 3 tiers before ultimate community referendum.\n\n### Acceptance Criteria\n- Escalated disputes require exponentially higher bond amounts.",
        "labels": [
            "disputes",
            "feature",
            "treasury"
        ]
    },
    {
        "title": "[Treasury] Implement quadratic voting mechanism for governance grant allocations",
        "body": "### Context & Problem\nLarge token holders completely dominate governance treasury funding decisions.\n\n### Proposed Solution\n1. Calculate voting weight as `sqrt(token_balance)` for ecosystem grant proposals.\n\n### Acceptance Criteria\n- Quadratic vote weighting verified in unit tests.",
        "labels": [
            "treasury",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[Treasury] Implement automated treasury balance reconciliation cron job with Slack alerting",
        "body": "### Context & Problem\nNo automated system verifies that on-chain treasury token balances match internal ledger records.\n\n### Proposed Solution\n1. Create hourly cron comparing on-chain contract balances against database aggregates.\n2. Trigger high-priority alert if delta exceeds tolerance threshold.\n\n### Acceptance Criteria\n- Hourly reconciliation logs balance parity; alerts on discrepancies.",
        "labels": [
            "treasury",
            "cron",
            "feature"
        ]
    },
    {
        "title": "[Treasury] Implement governance proposal cancellation by author before voting starts",
        "body": "### Context & Problem\nProposers who discover a typo or flaw in their proposal cannot cancel it once submitted.\n\n### Proposed Solution\n1. Add `cancel_proposal` allowing proposer to withdraw proposal before voting opens.\n2. Return submission deposit.\n\n### Acceptance Criteria\n- Authors can cancel pending proposals and reclaim deposit.",
        "labels": [
            "treasury",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[Treasury] Implement time-locked delay on critical parameter changes (fees, oracle whitelist)",
        "body": "### Context & Problem\nImmediate parameter changes give users no time to exit positions if fees or governance rules change unfavorably.\n\n### Proposed Solution\n1. Enforce 48-hour timelock between proposing a fee change and executing it.\n\n### Acceptance Criteria\n- Parameter modifications enforce 48-hour delay with event notification.",
        "labels": [
            "treasury",
            "security",
            "feature"
        ]
    },
    {
        "title": "[Treasury] Implement unit tests for multi-sig threshold changes and timelock expiration",
        "body": "### Context & Problem\nThreshold change edge cases (e.g. reducing threshold below signer count, removing active signers) need thorough test coverage.\n\n### Proposed Solution\n1. Write test suite in `contracts/treasury/src/test.rs` covering all governance mutation scenarios.\n\n### Acceptance Criteria\n- 100% test coverage of multi-sig admin operations.",
        "labels": [
            "treasury",
            "testing",
            "security"
        ]
    },
    {
        "title": "[DevOps] Fix Docker Compose staging container startup race condition between DB and backend",
        "body": "### Context & Problem\nIn `docker-compose.staging.yml`, the backend service starts before PostgreSQL is ready to accept connections, causing boot crash loops.\n\n### Proposed Solution\n1. Add `pg_isready` healthcheck to the `db` service.\n2. Use `depends_on: db: condition: service_healthy` on backend and indexer containers.\n\n### Acceptance Criteria\n- `docker compose -f docker-compose.staging.yml up` boots cleanly without container restarts.",
        "labels": [
            "security",
            "middleware",
            "bug"
        ]
    },
    {
        "title": "[DevOps] Fix Dependabot alerts and update vulnerable dependencies in backend and frontend",
        "body": "### Context & Problem\nMultiple high and moderate severity Dependabot alerts exist across npm dependencies (`cross-spawn`, `cookie`, `micromatch`).\n\n### Proposed Solution\n1. Audit and upgrade vulnerable dependencies in `backend/package.json` and `frontend/package.json`.\n2. Run automated test suites to ensure zero breaking regressions.\n\n### Acceptance Criteria\n- `npm audit` reports 0 high or critical vulnerabilities.",
        "labels": [
            "security",
            "backend",
            "bug"
        ]
    },
    {
        "title": "[DevOps] Fix Gitleaks false positives and enforce secret scanning in pre-commit hooks",
        "body": "### Context & Problem\nTest keys and mock tokens in test files trigger false positive failures in Gitleaks.\n\n### Proposed Solution\n1. Update `.gitleaks.toml` with explicit path allowlists for mock fixtures.\n2. Add pre-commit hook script blocking commits with actual credentials.\n\n### Acceptance Criteria\n- Gitleaks scans pass cleanly in CI while protecting against real leaks.",
        "labels": [
            "security",
            "testing",
            "bug"
        ]
    },
    {
        "title": "[DevOps] Fix missing non-root user in Dockerfiles posing container escape risks",
        "body": "### Context & Problem\n`backend/Dockerfile` and `indexer/Dockerfile` run applications as `root`, violating container security best practices.\n\n### Proposed Solution\n1. Create a dedicated non-root user: `RUN addgroup -S app && adduser -S app -G app`.\n2. Add `USER app` before `CMD` instruction.\n\n### Acceptance Criteria\n- Containers execute under unprivileged user permissions.",
        "labels": [
            "security",
            "middleware",
            "bug"
        ]
    },
    {
        "title": "[DevOps] Implement GitHub Actions workflow for automated Soroban contract compilation and test",
        "body": "### Context & Problem\nPull requests can merge with broken Soroban contract code because CI only tests backend TypeScript.\n\n### Proposed Solution\n1. Add `.github/workflows/contracts.yml` running `cargo clippy`, `cargo test`, and `cargo check`.\n\n### Acceptance Criteria\n- Every PR automatically tests Rust contracts in CI.",
        "labels": [
            "testing",
            "blockchain",
            "feature"
        ]
    },
    {
        "title": "[DevOps] Implement automated testnet deployment pipeline triggered on main branch merge",
        "body": "### Context & Problem\nDeploying contracts and backend to Stellar Testnet requires manual developer intervention.\n\n### Proposed Solution\n1. Create CD workflow deploying updated contracts to Stellar testnet and updating contract ID configs.\n\n### Acceptance Criteria\n- Merges to `main` trigger automated deployment and smoke tests.",
        "labels": [
            "blockchain",
            "feature",
            "cron"
        ]
    },
    {
        "title": "[DevOps] Implement database connection pooling tuning for high-concurrency production load",
        "body": "### Context & Problem\nDefault connection pool limit of 10 clients exhausts quickly under concurrent traffic spikes.\n\n### Proposed Solution\n1. Tune pool settings in `backend/src/db/index.ts`: `max: 50, idleTimeoutMillis: 30000, connectionTimeoutMillis: 5000`.\n2. Configure PgBouncer in staging docker compose.\n\n### Acceptance Criteria\n- System handles 500 concurrent requests without connection acquisition errors.",
        "labels": [
            "backend",
            "repository",
            "feature"
        ]
    },
    {
        "title": "[DevOps] Implement automated contract bytecode size and optimization verification in CI",
        "body": "### Context & Problem\nUnchecked WASM sizes can exceed Soroban limits silently.\n\n### Proposed Solution\n1. Integrate `soroban contract optimize` in CI workflow.\n2. Assert optimized WASM <= 64KB with artifact upload.\n\n### Acceptance Criteria\n- PRs report compiled WASM sizes; fail if over limit.",
        "labels": [
            "blockchain",
            "testing",
            "feature"
        ]
    },
    {
        "title": "[DevOps] Implement comprehensive seed script for local development and testnet simulation",
        "body": "### Context & Problem\nNew developers starting locally have an empty database with no markets, categories, or test users.\n\n### Proposed Solution\n1. Create `npm run db:seed` script generating realistic categories, active markets, orders, and mock oracles.\n\n### Acceptance Criteria\n- Single command seeds a fully functional local development environment.",
        "labels": [
            "backend",
            "feature",
            "good first issue"
        ]
    },
    {
        "title": "[DevOps] Implement centralized logging and metric dashboard configuration with Grafana and Prometheus",
        "body": "### Context & Problem\nNo consolidated dashboard exists to monitor system health across backend, indexer, and contract interactions.\n\n### Proposed Solution\n1. Add Prometheus and Grafana service definitions to `docker-compose.staging.yml`.\n2. Pre-configure dashboard JSON tracking API RPS, error rates, indexer lag, and contract volume.\n\n### Acceptance Criteria\n- Grafana dashboard visualizes full-stack metrics out-of-the-box.",
        "labels": [
            "middleware",
            "feature",
            "testing"
        ]
    }
]

def export_documentation():
    # Export to markdown
    with open("ISSUES_125.md", "w") as f:
        f.write("# BANKERCHANGER - 125 Repository Issues & Action Items\n\n")
        f.write("Comprehensive task backlog covering every component of the repository: Smart Contracts, Backend API, Blockchain Indexer, Frontend UI/UX, Treasury & Governance, and DevOps / CI/CD.\n\n")
        f.write("A significant portion of these issues directly address critical bugs, compilation failures, security vulnerabilities, and stability fixes necessary to make the repository production-ready.\n\n")
        f.write("---\n\n")
        
        for idx, issue in enumerate(ISSUES, 1):
            f.write(f"## Issue #{idx}: {issue['title']}\n\n")
            f.write(f"**Labels**: `{', '.join(issue['labels'])}`\n\n")
            f.write(issue['body'] + "\n\n")
            f.write("---\n\n")
    print("Exported ISSUES_125.md")

    # Export to JSON
    with open("issues_125.json", "w") as f:
        json.dump(ISSUES, f, indent=2)
    print("Exported issues_125.json")

def main():
    export_documentation()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    gh_bin = subprocess.run(["which", "gh"], capture_output=True, text=True).stdout.strip()
    if not gh_bin and os.path.exists(os.path.expanduser("~/.local/bin/gh")):
        gh_bin = os.path.expanduser("~/.local/bin/gh")

    print(f"Total issues to process: {len(ISSUES)}")
    print(f"Total labels to process: {len(LABELS)}")

    # Check authentication
    has_auth = False
    if gh_bin:
        check = subprocess.run([gh_bin, "auth", "status"], capture_output=True, text=True)
        if check.returncode == 0:
            has_auth = True
    if token:
        has_auth = True

    if not has_auth:
        print("\n[!] Notice: No active GitHub CLI login or GH_TOKEN detected.")
        print("To push these 125 issues directly to GitHub, run:")
        print("  gh auth login")
        print("  OR")
        print("  GH_TOKEN=<your_token> python3 create_125_issues.py")
        print("\nAll 125 issues have been compiled and exported to ISSUES_125.md and issues_125.json.")
        return

    # 1. Create labels
    print("\nCreating / verifying GitHub labels...")
    for label in LABELS:
        name = label["name"]
        color = label["color"]
        desc = label.get("description", "")
        if gh_bin:
            cmd = [gh_bin, "label", "create", name, "--color", color, "--description", desc, "--repo", REPO, "--force"]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif token:
            url = f"https://api.github.com/repos/{REPO}/labels"
            data = json.dumps({"name": name, "color": color, "description": desc})
            subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: token {token}", "-H", "Accept: application/vnd.github.v3+json", url, "-d", data], stdout=subprocess.DEVNULL)
    print("All labels verified.")

def create_issue_api(gh_bin, token, title, body, labels):
    payload = json.dumps({"title": title, "body": body, "labels": labels})
    if gh_bin:
        cmd = [gh_bin, "api", f"repos/{REPO}/issues", "--input", "-"]
        proc = subprocess.run(cmd, input=payload, text=True, capture_output=True)
        return proc.returncode == 0, proc.stdout, proc.stderr
    elif token:
        url = f"https://api.github.com/repos/{REPO}/issues"
        proc = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}", "-X", "POST",
             "-H", f"Authorization: token {token}",
             "-H", "Accept: application/vnd.github.v3+json",
             url, "-d", payload],
            capture_output=True, text=True
        )
        lines = proc.stdout.strip().split("\n")
        code = lines[-1] if lines else "500"
        body_resp = "\n".join(lines[:-1])
        return code in ["200", "201"], body_resp, f"HTTP {code}"
    return False, "", "No gh CLI or GH_TOKEN found"

    print("Labels verified.")

    # 2. Create issues
    print(f"\nPushing {len(ISSUES)} issues to {REPO}...")
    success_count = 0
    failed = []

    print(f"\nStarting creation and push of {len(ISSUES)} issues to {REPO}...")
    for idx, item in enumerate(ISSUES, 1):
        title = item["title"]
        body = item["body"]
        labels = item["labels"]

        retries = 3
        created = False
        while retries > 0 and not created:
            ok, out, err = create_issue_api(gh_bin, token, title, body, labels)
            if ok:
                try:
                    res_json = json.loads(out)
                    issue_num = res_json.get("number", "N/A")
                    print(f"[{idx}/{len(ISSUES)}] Created issue #{issue_num}: {title}")
                except Exception:
                    print(f"[{idx}/{len(ISSUES)}] Created issue: {title}")
                success_count += 1
                created = True
            else:
                print(f"[{idx}/{len(ISSUES)}] API Error: {res.stdout[:100]}")
        
        time.sleep(0.2)

    print(f"\n==================================================")
    print(f"Finished! Successfully created {success_count} / {len(ISSUES)} issues on {REPO}.")
    if failed:
        print(f"Failed issues ({len(failed)}): {failed}")
    print(f"==================================================")

if __name__ == "__main__":
    main()
