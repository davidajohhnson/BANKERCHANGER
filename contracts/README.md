# Contracts

The default Cargo workspace includes the deployable contracts and shared library. The fuzz crate is excluded because it requires `cargo-fuzz` and a nightly Rust toolchain.

## Fuzzing

Install `cargo-fuzz` and the nightly toolchain, then run a target from the `contracts` directory:

```sh
cargo +nightly fuzz run --manifest-path shared/fuzz/Cargo.toml amm_fuzz
cargo +nightly fuzz run --manifest-path shared/fuzz/Cargo.toml payout_fuzz
```