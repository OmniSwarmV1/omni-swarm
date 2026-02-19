# OmniSwarm P3-P5 Execution Plan

## Goal
P3, P4, P5 islerini 19 Subat 2026 22:41 baz alinarak sirali ve kanitli sekilde tamamlamak.

## Schedule
- P3 hedef bitis: 20 Subat 2026 02:41
- P4 hedef bitis: 20 Subat 2026 16:41
- P5 hedef bitis: 20 Subat 2026 22:41

## Tasks
- [ ] P3.1: `tests/test_multi_node_integration.py` ekle (3 node/process, tek gorev, katkilar, birlesik sonuc, royalty, evolution) -> Verify: `pytest -q tests/test_multi_node_integration.py`
- [ ] P3.2: Dagitik swarm orkestratoru ekle (`core/distributed_swarm.py` veya `core/swarm_engine.py` extension) -> Verify: testte `"Distributed swarm completed - 3/3 nodes contributed"` ve her node icin `generation >= 1`
- [ ] P3.3: P3 regression -> Verify: `pytest -q tests/test_node.py tests/test_p2p_discovery.py tests/test_omni_token.py tests/test_multi_node_integration.py`

- [ ] P4.1: PyInstaller spec + build script ekle (`scripts/build_binary.ps1` ve gerekiyorsa `.spec`) -> Verify: local one-file binary build cikar
- [ ] P4.2: GitHub Actions matrix workflow ekle (`.github/workflows/release.yml`) Windows/macOS/Linux -> Verify: `workflow_dispatch` dry-run + artifact isimleri dogru
- [ ] P4.3: `v0.1` release adimi (artifact upload) -> Verify: release page’de 3 platform artifact gorunsun

- [ ] P5.1: `token/` klasoru olustur, `omni_token/` ile uyumlu migration/planned deprecation notu ekle -> Verify: yeni yol README’de referansli
- [ ] P5.2: Dummy Solana claimable contract stublari ekle (`token/solana_dummy/`) + claim instruction dokumani -> Verify: unit test veya deterministic simulator script
- [ ] P5.3: Airdrop snapshot + claim flow ekle (`token/airdrop_snapshot.json`, `token/claim_flow.md`) -> Verify: snapshot -> claim input -> proof check pathi calisiyor
- [ ] P5.4: README’ye `Ilk 1000 node icin claim linki` bolumu ekle -> Verify: link/placeholder + guvenlik notu mevcut

## Done When
- [ ] P3 testi geciyor ve logta dagitik katkı + evolution kaniti var
- [ ] P4 release workflow’dan 3 platform artifact yukleniyor
- [ ] P5 token klasoru, claim flow, snapshot ve README claim bolumu tamam
