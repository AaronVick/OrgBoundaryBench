# Next-Generation Public Run Plan

Primary optimization target:
- governance-preserving quotient recovery (primary)
- coordination-boundary recovery (secondary)
- org-chart recovery as a secondary endpoint, not sole target

Dataset stack:
1. email-Eu-core-temporal (full run)
2. wiki-talk-temporal (public temporal slice)
3. GitHub workflow temporal slice with review/escalation labels

Labels/endpoints:
- formal departments/roles where available
- coordination outcomes (handoff failure, escalation, unresolved challenge)
- governance outcomes (reversal success, responsibility attribution, recourse latency)

Baselines:
- one-block, singleton
- spectral, Louvain, Leiden
- simple statistical heuristics
- random matched partitions

Nulls:
- label permutation
- matched-block random
- degree-preserving rewire
- temporal timestamp shuffle

Stress suite:
- random node drop
- top-degree node drop
- edge drop
- block fragmentation

Acceptance criteria (all required):
1. nontriviality pass
2. external agreement pass
3. stress robustness pass
4. null/rival dominance pass
5. temporal validation pass
6. governance preservation pass

Execution discipline:
- staged sizes (80 -> 120 -> 200)
- preregistered gates
- model identity + artifact hash logging
- preserve negative results in publication artifacts
