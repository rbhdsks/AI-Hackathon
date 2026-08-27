# Blockchain and consensus decision

## Decision

Do not add blockchain to the MVP. The single-hospital prototype already has a hash-chained SQLite audit log that detects modification of recorded events. Blockchain would add operational and governance complexity without improving the ranking model or the bedside workflow.

## When a distributed ledger could become relevant

A permissioned consortium ledger may be defensible only if several independent institutions need to verify shared audit anchors without trusting one database operator. Even then, no directly identifying health data should be written to the ledger. Store only event hashes, policy versions, consent references, and timestamps; keep clinical data in governed hospital systems.

## Consensus comparison

| Mechanism | Fault model | Fit | Decision |
|---|---|---|---|
| Public proof of work / stake | Open, adversarial membership | Cryptocurrency/public networks | Reject: privacy, cost, latency, and governance mismatch |
| Raft in Hyperledger Fabric | Crash-fault tolerant | Known consortium members that trust the operator set against crashes | Candidate for a small trusted consortium |
| SmartBFT in Hyperledger Fabric | Byzantine-fault tolerant | Multiple organizations that need protection against faulty or malicious orderers | Candidate only if the threat model justifies lower throughput and more governance |
| Single-owner hash chain | Detects log rewriting when independently anchored or monitored | One hospital prototype and early shadow pilot | Recommended now |

Hyperledger Fabric documents Raft as crash-fault tolerant and SmartBFT as Byzantine-fault tolerant. Its upgrade guidance also notes that Byzantine-fault tolerance can reduce throughput. Consensus selection must follow an explicit threat model, not a branding goal.

## Future gate

Consider a ledger only after all of the following are true:

1. Two or more legally independent institutions share audit evidence.
2. A governance body defines membership, key rotation, incident handling, and exit.
3. Data-protection review approves the on-chain data model.
4. A normal signed transparency log or independently anchored hash chain is shown to be insufficient.
5. Latency, recovery, and support burden are measured.

Sources:

- https://hyperledger-fabric.readthedocs.io/en/release-2.2/orderer/ordering_service.html
- https://hyperledger-fabric.readthedocs.io/en/latest/bft_configuration.html
- https://hyperledger-fabric.readthedocs.io/en/latest/upgrade_to_newest_version.html
