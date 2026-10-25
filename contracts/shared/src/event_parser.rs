//! ============================================================
//! BANKERCHANGER — Event Parsing Utilities
//! Parse raw Soroban event payloads into typed event structs.
//! ============================================================

use soroban_sdk::{Address, Env, String, TryFromVal, Val, Vec};

use crate::types::{BetPlacedPayload, BetRecord, ClaimReceipt, OddsSnapshot, Outcome};

// ─── Typed event structs ──────────────────────────────────────────────────────

/// All terminal states a boxing match can reach.
///
/// This enum is the canonical representation used throughout the indexer and
/// contract layer once an event has been parsed.  It is deliberately separate
/// from the on-chain [`Outcome`] type so that parsing logic never leaks raw
/// enum variants to callers — every path is handled explicitly here, and
/// callers that pattern-match on `ParsedResolution` will get a compile error
/// if a new variant is added without being covered.
///
/// | Variant    | Meaning                                                  |
/// |------------|----------------------------------------------------------|
/// | FighterA   | Fighter A wins; `FighterA` bettors receive winnings.     |
/// | FighterB   | Fighter B wins; `FighterB` bettors receive winnings.     |
/// | Draw       | Match judged a draw; `Draw` bettors receive winnings.    |
/// | NoContest  | Fight invalidated (DQ, early stop, etc.); full refunds.  |
/// | Void       | Market cancelled before resolution; full refunds.        |
#[derive(Clone, Debug, PartialEq)]
pub enum ParsedResolution {
    /// Fighter A is the declared winner.
    FighterA,
    /// Fighter B is the declared winner.
    FighterB,
    /// The match ended in a draw.
    Draw,
    /// The fight was declared a no-contest (disqualification, early stoppage,
    /// failed drug test, etc.).  All stakes are refunded.
    NoContest,
    /// The market was cancelled before a result could be declared, or the
    /// on-chain outcome field was absent (`OptionalOutcome::None`).
    /// All stakes are refunded.
    Void,
}

impl ParsedResolution {
    /// Convert a raw on-chain [`Outcome`] into a [`ParsedResolution`].
    ///
    /// This is infallible — every `Outcome` variant maps to exactly one
    /// `ParsedResolution` variant.  No `unwrap` or `panic` is ever needed.
    pub fn from_outcome(outcome: &Outcome) -> Self {
        match outcome {
            Outcome::FighterA  => ParsedResolution::FighterA,
            Outcome::FighterB  => ParsedResolution::FighterB,
            Outcome::Draw      => ParsedResolution::Draw,
            Outcome::NoContest => ParsedResolution::NoContest,
        }
    }
}

#[derive(Clone, Debug)]
pub struct MarketCreatedEvent {
    pub market_id: u64,
    pub contract_address: Address,
    pub match_id: String,
}

#[derive(Clone, Debug)]
pub struct MarketLockedEvent {
    pub market_id: u64,
}

/// Parsed representation of a `market_resolved` on-chain event.
///
/// `resolution` is a [`ParsedResolution`] rather than a raw [`Outcome`] so
/// that all terminal states — including `NoContest` and the `Void` sentinel
/// — are handled without any `unwrap` calls.
#[derive(Clone, Debug)]
pub struct MarketResolvedEvent {
    pub market_id: u64,
    pub resolution: ParsedResolution,
    pub oracle_address: Address,
}

#[derive(Clone, Debug)]
pub struct ParsedBetPlaced {
    pub market_id: u64,
    pub bet: BetRecord,
    pub odds_snapshot: OddsSnapshot,
}

#[derive(Clone, Debug)]
pub struct WinningsClaimedEvent {
    pub market_id: u64,
    pub receipt: ClaimReceipt,
}

#[derive(Clone, Debug)]
pub struct RefundClaimedEvent {
    pub market_id: u64,
    pub bettor: Address,
    pub amount: i128,
}

pub use crate::events::MarketCancelled;
pub type MarketCancelledEvent = MarketCancelled;

#[derive(Clone, Debug)]
pub struct MarketDisputedEvent {
    pub market_id: u64,
    pub reason: String,
}

/// Parsed representation of a `dispute_resolved` on-chain event.
///
/// `resolution` is a [`ParsedResolution`] rather than a raw [`Outcome`] so
/// that dispute outcomes that include `NoContest` are handled cleanly.
#[derive(Clone, Debug)]
pub struct DisputeResolvedEvent {
    pub market_id: u64,
    pub resolution: ParsedResolution,
}

// ─── Error type ───────────────────────────────────────────────────────────────

#[derive(Copy, Clone, Debug, PartialEq)]
pub enum ParseError {
    /// Topics or data Vec does not have the expected length
    InvalidLength,
    /// A Val could not be converted to the expected type
    InvalidType,
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

fn get_topic<T: TryFromVal<Env, Val>>(
    env: &Env,
    topics: &Vec<Val>,
    idx: u32,
) -> Result<T, ParseError> {
    let val = topics.get(idx).ok_or(ParseError::InvalidLength)?;
    T::try_from_val(env, &val).map_err(|_| ParseError::InvalidType)
}

fn decode_data<T: TryFromVal<Env, Val>>(env: &Env, data: &Val) -> Result<T, ParseError> {
    T::try_from_val(env, data).map_err(|_| ParseError::InvalidType)
}

// ─── Parsers ──────────────────────────────────────────────────────────────────

/// Parses a raw `market_created` event.
///
/// Topics: `(Symbol("market_created"), market_id: u64)`
/// Data:   `(contract_address: Address, match_id: String)`
pub fn parse_market_created_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<MarketCreatedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let (contract_address, match_id): (Address, String) = decode_data(env, data)?;
    Ok(MarketCreatedEvent {
        market_id,
        contract_address,
        match_id,
    })
}

/// Parses a raw `market_locked` event.
///
/// Topics: `(Symbol("market_locked"), market_id: u64)`
/// Data:   `()`
pub fn parse_market_locked_event(
    env: &Env,
    topics: &Vec<Val>,
    _data: &Val,
) -> Result<MarketLockedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    Ok(MarketLockedEvent { market_id })
}

/// Parses a raw `market_resolved` event.
///
/// Topics: `(Symbol("market_resolved"), market_id: u64)`
/// Data:   `(outcome: Outcome, oracle_address: Address)`
///
/// The raw [`Outcome`] is mapped to a [`ParsedResolution`] so that
/// `NoContest` and all other terminal states are handled without panics.
pub fn parse_market_resolved_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<MarketResolvedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let (outcome, oracle_address): (Outcome, Address) = decode_data(env, data)?;
    Ok(MarketResolvedEvent {
        market_id,
        resolution: ParsedResolution::from_outcome(&outcome),
        oracle_address,
    })
}

/// Parses a raw `bet_placed` event.
///
/// Topics: `(Symbol("bet_placed"), market_id: u64)`
/// Data:   `BetPlacedPayload` (legacy events containing only `BetRecord` are
///         parsed with a zero-valued odds snapshot)
pub fn parse_bet_placed_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<ParsedBetPlaced, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let (bet, odds_snapshot) = match BetPlacedPayload::try_from_val(env, data) {
        Ok(payload) => (payload.bet, payload.odds_at_bet_time),
        Err(_) => (
            decode_data::<BetRecord>(env, data)?,
            OddsSnapshot {
                odds_a: 0,
                odds_b: 0,
                odds_draw: 0,
            },
        ),
    };
    Ok(ParsedBetPlaced {
        market_id,
        bet,
        odds_snapshot,
    })
}

/// Parses a raw `winnings_claimed` event.
///
/// Topics: `(Symbol("winnings_claimed"), market_id: u64)`
/// Data:   `ClaimReceipt`
pub fn parse_winnings_claimed_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<WinningsClaimedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let receipt: ClaimReceipt = decode_data(env, data)?;
    Ok(WinningsClaimedEvent { market_id, receipt })
}

/// Parses a raw `refund_claimed` event.
///
/// Topics: `(Symbol("refund_claimed"), market_id: u64)`
/// Data:   `(bettor: Address, amount: i128)`
pub fn parse_refund_claimed_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<RefundClaimedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let (bettor, amount): (Address, i128) = decode_data(env, data)?;
    Ok(RefundClaimedEvent {
        market_id,
        bettor,
        amount,
    })
}

/// Parses a raw `market_cancelled` event.
///
/// Topics: `(Symbol("market_cancelled"), market_id: u64)`
/// Data:   `(cancelled_by: Address, reason: String, cancelled_at: u64)`
pub fn parse_market_cancelled_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<MarketCancelledEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let (cancelled_by, reason, cancelled_at): (Address, String, u64) = decode_data(env, data)?;
    Ok(MarketCancelledEvent {
        market_id,
        cancelled_by,
        reason,
        cancelled_at,
    })
}

/// Parses a raw `market_disputed` event.
///
/// Topics: `(Symbol("market_disputed"), market_id: u64)`
/// Data:   `String` (reason)
pub fn parse_market_disputed_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<MarketDisputedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let reason: String = decode_data(env, data)?;
    Ok(MarketDisputedEvent { market_id, reason })
}

/// Parses a raw `dispute_resolved` event.
///
/// Topics: `(Symbol("dispute_resolved"), market_id: u64)`
/// Data:   `Outcome`
///
/// The raw [`Outcome`] is mapped to a [`ParsedResolution`] so that
/// `NoContest` rulings from admin dispute resolution are handled cleanly.
pub fn parse_dispute_resolved_event(
    env: &Env,
    topics: &Vec<Val>,
    data: &Val,
) -> Result<DisputeResolvedEvent, ParseError> {
    let market_id: u64 = get_topic(env, topics, 1)?;
    let outcome: Outcome = decode_data(env, data)?;
    Ok(DisputeResolvedEvent {
        market_id,
        resolution: ParsedResolution::from_outcome(&outcome),
    })
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use soroban_sdk::{
        contract, contractimpl,
        testutils::{Address as _, Events},
        Address, Env,
    };

    use crate::{
        event_parser::*,
        events::*,
        types::{BetRecord, BetSide, ClaimReceipt, OddsSnapshot, Outcome},
    };

    #[contract]
    struct Dummy;
    #[contractimpl]
    impl Dummy {}

    fn setup() -> (Env, Address) {
        let env = Env::default();
        let id = env.register(Dummy, ());
        (env, id)
    }

    fn addr(env: &Env) -> Address {
        Address::generate(env)
    }

    fn s(env: &Env, v: &str) -> soroban_sdk::String {
        soroban_sdk::String::from_str(env, v)
    }

    macro_rules! last_event {
        ($env:expr) => {{
            let all = $env.events().all();
            // soroban-sdk 22.x: Events::all() returns Vec<(Address, Vec<Val>, Val)>
            let (_, topics, data) = all.last().expect("no events emitted");
            (topics, data)
        }};
    }

    // ── Existing round-trip tests ─────────────────────────────────────────────

    #[test]
    fn test_parse_market_created_event() {
        let (env, id) = setup();
        let contract = addr(&env);
        env.as_contract(&id, || {
            emit_market_created(&env, 1, contract.clone(), s(&env, "FURY-USYK"));
        });
        let ev = last_event!(env);
        let parsed = parse_market_created_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 1);
        assert_eq!(parsed.contract_address, contract);
        assert_eq!(parsed.match_id, s(&env, "FURY-USYK"));
    }

    #[test]
    fn test_parse_market_locked_event() {
        let (env, id) = setup();
        env.as_contract(&id, || {
            emit_market_locked(&env, 2);
        });
        let ev = last_event!(env);
        let parsed = parse_market_locked_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 2);
    }

    #[test]
    fn test_parse_bet_placed_event() {
        let (env, id) = setup();
        let bettor = addr(&env);
        let bet = BetRecord {
            bettor: bettor.clone(),
            market_id: 4,
            side: BetSide::FighterB,
            amount: 5_000_000,
            placed_at: 1_000,
            claimed: false,
        };
        let odds = OddsSnapshot {
            odds_a: 4_000,
            odds_b: 3_500,
            odds_draw: 2_500,
        };
        env.as_contract(&id, || {
            emit_bet_placed_with_odds(&env, 4, bet.clone(), odds.clone());
        });
        let ev = last_event!(env);
        let parsed = parse_bet_placed_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 4);
        assert_eq!(parsed.bet.bettor, bettor);
        assert_eq!(parsed.bet.amount, 5_000_000);
        assert_eq!(parsed.odds_snapshot, odds);
    }

    #[test]
    fn test_parse_winnings_claimed_event() {
        let (env, id) = setup();
        let bettor = addr(&env);
        let receipt = ClaimReceipt {
            bettor: bettor.clone(),
            market_id: 5,
            amount_won: 9_800_000,
            fee_deducted: 200_000,
            claimed_at: 2_000,
        };
        env.as_contract(&id, || {
            emit_winnings_claimed(&env, 5, receipt.clone());
        });
        let ev = last_event!(env);
        let parsed = parse_winnings_claimed_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 5);
        assert_eq!(parsed.receipt.amount_won, 9_800_000);
        assert_eq!(parsed.receipt.fee_deducted, 200_000);
    }

    #[test]
    fn test_parse_refund_claimed_event() {
        let (env, id) = setup();
        let bettor = addr(&env);
        env.as_contract(&id, || {
            emit_refund_claimed(&env, 6, bettor.clone(), 3_000_000);
        });
        let ev = last_event!(env);
        let parsed = parse_refund_claimed_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 6);
        assert_eq!(parsed.bettor, bettor);
        assert_eq!(parsed.amount, 3_000_000);
    }

    #[test]
    fn test_parse_market_cancelled_event() {
        let (env, id) = setup();
        let canceller = addr(&env);
        env.as_contract(&id, || {
            emit_market_cancelled(&env, 7, canceller.clone(), s(&env, "postponed"), 1234);
        });
        let ev = last_event!(env);
        let parsed = parse_market_cancelled_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 7);
        assert_eq!(parsed.cancelled_by, canceller);
        assert_eq!(parsed.reason, s(&env, "postponed"));
        assert_eq!(parsed.cancelled_at, 1234);
    }

    #[test]
    fn test_parse_market_disputed_event() {
        let (env, id) = setup();
        env.as_contract(&id, || {
            emit_market_disputed(&env, 8, s(&env, "conflict"));
        });
        let ev = last_event!(env);
        let parsed = parse_market_disputed_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 8);
        assert_eq!(parsed.reason, s(&env, "conflict"));
    }

    // ── ParsedResolution: market_resolved terminal-state vectors ─────────────
    //
    // One test per terminal outcome so any regression is immediately obvious.

    #[test]
    fn test_market_resolved_fighter_a() {
        let (env, id) = setup();
        let oracle = addr(&env);
        env.as_contract(&id, || {
            emit_market_resolved(&env, 10, Outcome::FighterA, oracle.clone());
        });
        let ev = last_event!(env);
        let parsed = parse_market_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 10);
        assert_eq!(parsed.oracle_address, oracle);
        assert_eq!(parsed.resolution, ParsedResolution::FighterA);
    }

    #[test]
    fn test_market_resolved_fighter_b() {
        let (env, id) = setup();
        let oracle = addr(&env);
        env.as_contract(&id, || {
            emit_market_resolved(&env, 11, Outcome::FighterB, oracle.clone());
        });
        let ev = last_event!(env);
        let parsed = parse_market_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 11);
        assert_eq!(parsed.oracle_address, oracle);
        assert_eq!(parsed.resolution, ParsedResolution::FighterB);
    }

    #[test]
    fn test_market_resolved_draw() {
        let (env, id) = setup();
        let oracle = addr(&env);
        env.as_contract(&id, || {
            emit_market_resolved(&env, 12, Outcome::Draw, oracle.clone());
        });
        let ev = last_event!(env);
        let parsed = parse_market_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 12);
        assert_eq!(parsed.oracle_address, oracle);
        assert_eq!(parsed.resolution, ParsedResolution::Draw);
    }

    /// NoContest must parse without panicking and produce `ParsedResolution::NoContest`.
    #[test]
    fn test_market_resolved_no_contest() {
        let (env, id) = setup();
        let oracle = addr(&env);
        env.as_contract(&id, || {
            emit_market_resolved(&env, 13, Outcome::NoContest, oracle.clone());
        });
        let ev = last_event!(env);
        let parsed = parse_market_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 13);
        assert_eq!(parsed.oracle_address, oracle);
        assert_eq!(parsed.resolution, ParsedResolution::NoContest);
    }

    /// Void is produced when the caller explicitly builds a ParsedResolution::Void
    /// (e.g. after reading OptionalOutcome::None from storage).  Verify the
    /// enum variant exists and can be matched without exhaustiveness warnings.
    #[test]
    fn test_parsed_resolution_void_variant_exists() {
        // Void is not emitted by emit_market_resolved (OptionalOutcome::None never
        // reaches the event bus) but must be reachable for callers that read
        // MarketState.outcome == OptionalOutcome::None before an event fires.
        let r = ParsedResolution::Void;
        match r {
            ParsedResolution::FighterA  => panic!("wrong variant"),
            ParsedResolution::FighterB  => panic!("wrong variant"),
            ParsedResolution::Draw      => panic!("wrong variant"),
            ParsedResolution::NoContest => panic!("wrong variant"),
            ParsedResolution::Void      => { /* expected */ }
        }
    }

    // ── ParsedResolution: dispute_resolved terminal-state vectors ─────────────

    #[test]
    fn test_dispute_resolved_fighter_a() {
        let (env, id) = setup();
        env.as_contract(&id, || {
            emit_dispute_resolved(&env, 20, Outcome::FighterA);
        });
        let ev = last_event!(env);
        let parsed = parse_dispute_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 20);
        assert_eq!(parsed.resolution, ParsedResolution::FighterA);
    }

    #[test]
    fn test_dispute_resolved_fighter_b() {
        let (env, id) = setup();
        env.as_contract(&id, || {
            emit_dispute_resolved(&env, 21, Outcome::FighterB);
        });
        let ev = last_event!(env);
        let parsed = parse_dispute_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 21);
        assert_eq!(parsed.resolution, ParsedResolution::FighterB);
    }

    #[test]
    fn test_dispute_resolved_draw() {
        let (env, id) = setup();
        env.as_contract(&id, || {
            emit_dispute_resolved(&env, 22, Outcome::Draw);
        });
        let ev = last_event!(env);
        let parsed = parse_dispute_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 22);
        assert_eq!(parsed.resolution, ParsedResolution::Draw);
    }

    /// Admin dispute resolution can rule NoContest (e.g. post-fight DQ after
    /// initial FighterA result). Must not panic.
    #[test]
    fn test_dispute_resolved_no_contest() {
        let (env, id) = setup();
        env.as_contract(&id, || {
            emit_dispute_resolved(&env, 23, Outcome::NoContest);
        });
        let ev = last_event!(env);
        let parsed = parse_dispute_resolved_event(&env, &ev.0, &ev.1).unwrap();
        assert_eq!(parsed.market_id, 23);
        assert_eq!(parsed.resolution, ParsedResolution::NoContest);
    }

    // ── ParsedResolution::from_outcome unit tests ─────────────────────────────
    //
    // These tests exercise the mapping function in isolation so they run even
    // without Soroban environment setup and catch regressions cheaply.

    #[test]
    fn test_from_outcome_all_variants() {
        assert_eq!(
            ParsedResolution::from_outcome(&Outcome::FighterA),
            ParsedResolution::FighterA
        );
        assert_eq!(
            ParsedResolution::from_outcome(&Outcome::FighterB),
            ParsedResolution::FighterB
        );
        assert_eq!(
            ParsedResolution::from_outcome(&Outcome::Draw),
            ParsedResolution::Draw
        );
        assert_eq!(
            ParsedResolution::from_outcome(&Outcome::NoContest),
            ParsedResolution::NoContest
        );
    }

    // ── Error-path tests ──────────────────────────────────────────────────────

    #[test]
    fn test_parse_invalid_topics_returns_error() {
        let (env, _id) = setup();
        let empty: soroban_sdk::Vec<soroban_sdk::Val> = soroban_sdk::Vec::new(&env);
        let dummy_data: soroban_sdk::Val = soroban_sdk::Val::from_void().into();
        let result = parse_market_locked_event(&env, &empty, &dummy_data);
        assert_eq!(result.unwrap_err(), ParseError::InvalidLength);
    }
}
