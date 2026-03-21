# Metrics Output Reference

The old path is now named `legacy` in the config. The runtime accepts:

- `processing_method: "legacy"`
- `processing_method: "hybrid"`

Both paths produce the same top-level shape:

- `per_issue`: keyed by issue or PR number
- `per_period`: keyed by period-end timestamp for a 12-week bucket
- `per_period.<period>.keys`: the issue or PR IDs that landed in that bucket

For aggregate fields, the suffixes mean:

- `min`: minimum node value in that graph
- `avg`: average node value in that graph
- `max`: maximum node value in that graph
- `sum`: sum of node values in that graph

## Legacy Output

Source:

- `metrics_aggregator/legacy/per_issue.py`
- `metrics_aggregator/legacy/per_period.py`

### `per_issue`

- `per_issue.<issue>.num_comments`: number of comments on that issue or PR
- `per_issue.<issue>.num_discussants`: number of unique participants, including the original poster
- `per_issue.<issue>.wordiness`: count of words longer than 2 characters across the issue body and comments

### `per_period`

- `per_period.<period>.keys`: issue or PR IDs in that period
- `per_period.<period>.edges`: number of edges in the period conversation graph
- `per_period.<period>.vertices`: number of unique people in the period graph
- `per_period.<period>.density`: graph density for the period graph
- `per_period.<period>.diameter`: graph diameter for the period graph
- `per_period.<period>.constraint_avg`: average structural-hole constraint across all people in the period graph
- `per_period.<period>.constraint_max`: maximum structural-hole constraint across all people in the period graph
- `per_period.<period>.constraint_sum`: sum of structural-hole constraint across all people in the period graph
- `per_period.<period>.betweenness_avg`: average betweenness centrality across all people in the period graph
- `per_period.<period>.betweenness_max`: maximum betweenness centrality across all people in the period graph
- `per_period.<period>.betweenness_sum`: sum of betweenness centrality across all people in the period graph
- `per_period.<period>.closeness_avg`: average closeness centrality across all people in the period graph
- `per_period.<period>.closeness_max`: maximum closeness centrality across all people in the period graph
- `per_period.<period>.closeness_sum`: sum of closeness centrality across all people in the period graph
- `per_period.<period>.effective_size_avg`: average effective size across all people in the period graph
- `per_period.<period>.effective_size_max`: maximum effective size across all people in the period graph
- `per_period.<period>.effective_size_sum`: sum of effective size across all people in the period graph
- `per_period.<period>.efficiency_avg`: average efficiency across all people in the period graph
- `per_period.<period>.efficiency_max`: maximum efficiency across all people in the period graph
- `per_period.<period>.efficiency_sum`: sum of efficiency across all people in the period graph
- `per_period.<period>.hierarchy_avg`: average hierarchy across all people in the period graph
- `per_period.<period>.hierarchy_max`: maximum hierarchy across all people in the period graph
- `per_period.<period>.hierarchy_sum`: sum of hierarchy across all people in the period graph

## Hybrid Output

Source:

- `metrics_aggregator/hybrid/per_issue.py`
- `metrics_aggregator/hybrid/per_period.py`

### `per_issue`

- `per_issue.<issue>.num_comments`: number of comments on that issue or PR
- `per_issue.<issue>.num_discussants`: number of unique participants, including the original poster
- `per_issue.<issue>.wordiness`: count of words longer than 2 characters across the issue body and comments
- `per_issue.<issue>.edges`: number of edges in that issue conversation graph
- `per_issue.<issue>.vertices`: number of unique people in that issue graph
- `per_issue.<issue>.density`: graph density for that issue graph
- `per_issue.<issue>.diameter`: graph diameter for that issue graph

### `per_period`

- `per_period.<period>.keys`: issue or PR IDs in that period
- `per_period.<period>.per_period_issue`: nested issue-level summaries inside the period
- `per_period.<period>.edges`: number of edges in the whole-period conversation graph
- `per_period.<period>.vertices`: number of unique people in the whole-period graph
- `per_period.<period>.density`: graph density for the whole-period graph
- `per_period.<period>.diameter`: graph diameter for the whole-period graph
- `per_period.<period>.constraint_min`: minimum structural-hole constraint across all people in the period graph
- `per_period.<period>.constraint_avg`: average structural-hole constraint across all people in the period graph
- `per_period.<period>.constraint_max`: maximum structural-hole constraint across all people in the period graph
- `per_period.<period>.constraint_sum`: sum of structural-hole constraint across all people in the period graph
- `per_period.<period>.betweenness_min`: minimum betweenness centrality across all people in the period graph
- `per_period.<period>.betweenness_avg`: average betweenness centrality across all people in the period graph
- `per_period.<period>.betweenness_max`: maximum betweenness centrality across all people in the period graph
- `per_period.<period>.betweenness_sum`: sum of betweenness centrality across all people in the period graph
- `per_period.<period>.closeness_min`: minimum closeness centrality across all people in the period graph
- `per_period.<period>.closeness_avg`: average closeness centrality across all people in the period graph
- `per_period.<period>.closeness_max`: maximum closeness centrality across all people in the period graph
- `per_period.<period>.closeness_sum`: sum of closeness centrality across all people in the period graph
- `per_period.<period>.effective_size_min`: minimum effective size across all people in the period graph
- `per_period.<period>.effective_size_avg`: average effective size across all people in the period graph
- `per_period.<period>.effective_size_max`: maximum effective size across all people in the period graph
- `per_period.<period>.effective_size_sum`: sum of effective size across all people in the period graph
- `per_period.<period>.efficiency_min`: minimum efficiency across all people in the period graph
- `per_period.<period>.efficiency_avg`: average efficiency across all people in the period graph
- `per_period.<period>.efficiency_max`: maximum efficiency across all people in the period graph
- `per_period.<period>.efficiency_sum`: sum of efficiency across all people in the period graph
- `per_period.<period>.hierarchy_min`: minimum hierarchy across all people in the period graph
- `per_period.<period>.hierarchy_avg`: average hierarchy across all people in the period graph
- `per_period.<period>.hierarchy_max`: maximum hierarchy across all people in the period graph
- `per_period.<period>.hierarchy_sum`: sum of hierarchy across all people in the period graph

### `per_period_issue`

- `per_period.<period>.per_period_issue.<issue>.participants`: unique participants in that issue or PR
- `per_period.<period>.per_period_issue.<issue>.betweenness_min`: minimum betweenness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.betweenness_avg`: average betweenness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.betweenness_max`: maximum betweenness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.betweenness_sum`: sum of betweenness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.closeness_min`: minimum closeness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.closeness_avg`: average closeness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.closeness_max`: maximum closeness for that issue's participants, using their scores in the whole-period graph
- `per_period.<period>.per_period_issue.<issue>.closeness_sum`: sum of closeness for that issue's participants, using their scores in the whole-period graph

## Practical Difference

- `legacy` gives simpler per-issue output and whole-period summaries
- `hybrid` gives the whole-period summary plus richer per-issue graph metrics plus nested issue-within-period summaries
