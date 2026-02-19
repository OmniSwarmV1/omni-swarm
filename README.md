# OmniSwarm

**Ilk AI kolektif super-zeka.**  
18 Subat 2026

Her cihazda calisan yerel node'lar -> dinamik swarm'lar -> kesif simulasyonu -> royalty dagitimi.

Hedef: 2026 sonu 1 milyon node, haftada 1 cigir acan kesif.

## Hizli Baslangic

```bash
pip install -r requirements.txt
python -m core.node
```

Ilk node calisinca otomatik $OMNI airdrop havuzuna katilir.

## Runtime Modlari

- `mock` (varsayilan): Tamamen yerel simulasyon.
- `simulated_graph`: LangGraph tabanli simulasyon akisi.

Not: Gercek LLM entegrasyonu v1.1'de planlaniyor (Opus 4.6 + tool calling).

## P2P Notu

IPFS pubsub adapter `ipfshttpclient` kullanir. Bu client su an eski daemon serileri ile daha stabil calisir
(dogrulama testi go-ipfs v0.7.x ile yapildi).

## Ilk 1000 Node Icin Claim Linki

- Claim portal (testnet dummy): `https://claim.omniswarm.local/testnet/v0.1`
- Snapshot dosyasi: `token/airdrop_snapshot.json`
- Claim flow dokumani: `token/claim_flow.md`
