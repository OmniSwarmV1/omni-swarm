# OmniSwarm Testnet Dummy Claim Flow

This flow is for `TESTNET_DUMMY_CONTRACT.py` only.

## Inputs

- `token/airdrop_snapshot.json`
- Wallet ID from snapshot

## Steps

1. Load snapshot JSON.
2. Verify wallet exists under `claims`.
3. Call `TestnetDummyClaimContract.can_claim(wallet)`.
4. If `true`, call `claim(wallet)`.
5. Persist claim receipt in your backend/event log.

## Safety Notes

- This is not a real Solana on-chain program.
- Use only for pre-mainnet integration and QA.
- Production claim flow requires audited on-chain contract + signature verification.

## Placeholder Claim Link

- `https://claim.omniswarm.local/testnet/v0.1`
