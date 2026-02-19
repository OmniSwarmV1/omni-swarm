# OmniSwarm P3-P5 Execution Plan

## Goal
Complete P3, P4, and P5 tasks sequentially and verifiably by February 19, 2026, 22:41.

## Schedule
- P3 target completion: February 20, 2026, 02:41
- P4 target completion: February 20, 2026, 16:41
- P5 target completion: February 20, 2026, 22:41

## Tasks
- [ ] P3.1: Add `tests/test_multi_node_integration.py` (3 node/process, single task, contributions, combined result, royalty, evolution) -> Verification: `pytest -q tests/test_multi_node_integration.py`
- [ ] P3.2: Add digital swarm orchestrator (`core/distributed_swarm.py` or `core/swarm_engine.py` extension) -> Verification: test for `“Distributed swarm completed - 3/3 nodes contributed”` and `generation >= 1` for each node
- [ ] P3.3: P3 regression -> Verification: `pytest -q tests/test_node.py tests/test_p2p_discovery.py tests/test_omni_token.py tests/test_multi_node_integration.py`

- [ ] P4.1: Add PyInstaller spec + build script (`scripts/build_binary.ps1` and `.spec` if needed) -> Verification: Extract local single-file binary build
- [ ] P4.2: Add GitHub Actions matrix workflow (`.github/workflows/release.yml`) Windows/macOS/Linux -> Verification: `workflow_dispatch` dry run + artifact names are correct
- [ ] P4.3: `v0.1` version step (artifact upload) -> Verification: 3 platform artifacts should appear on the version page


- [ ] P5.1: Create `token/` folder, add migration/planned deprecation note compatible with `omni_token/` -> Verification: new path referenced in README
- [ ] P5.2: Add dummy Solana claimable contract stubs (`token/solana_dummy/`) + claim instructions
