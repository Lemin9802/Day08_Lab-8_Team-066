# Evaluation Results

## Overall Scores

| Metric | Score |
|---|---:|
| context_recall | 1.000 |
| context_precision | 0.308 |
| faithfulness_proxy | 0.343 |
| citation_coverage | 0.343 |
| answer_relevance | 0.726 |

## Per Question

| ID | Category | By | Recall | Precision | Faithfulness | Citation | Relevance |
|---|---|---|---:|---:|---:|---:|---:|
| nhi_q001 | legal | Nhi | 1.000 | 0.375 | 0.300 | 0.300 | 0.833 |
| nhi_q002 | legal | Nhi | 1.000 | 0.375 | 0.167 | 0.167 | 0.524 |
| nhi_q003 | legal | Nhi | 1.000 | 0.375 | 0.250 | 0.250 | 0.886 |
| nhi_q004 | news | Nhi | 1.000 | 0.125 | 1.000 | 1.000 | 0.444 |
| nhi_q005 | news | Nhi | 1.000 | 0.125 | 0.300 | 0.300 | 0.733 |
| huy_q001 | legal | Huy | 1.000 | 0.375 | 0.333 | 0.333 | 0.636 |
| huy_q002 | legal | Huy | 1.000 | 0.250 | 0.375 | 0.375 | 0.848 |
| huy_q003 | news | Huy | 1.000 | 0.375 | 0.300 | 0.300 | 0.667 |
| huy_q004 | legal | Huy | 1.000 | 0.375 | 0.167 | 0.167 | 0.703 |
| huy_q005 | legal | Huy | 1.000 | 0.250 | 0.375 | 0.375 | 0.688 |
| nghia_q001 | legal | Nghia | 1.000 | 0.375 | 0.375 | 0.375 | 1.000 |
| nghia_q002 | news | Nghia | 1.000 | 0.375 | 0.333 | 0.333 | 0.824 |
| nghia_q003 | news | Nghia | 1.000 | 0.125 | 0.250 | 0.250 | 0.533 |
| nghia_q004 | news | Nghia | 1.000 | 0.375 | 0.375 | 0.375 | 0.800 |
| nghia_q005 | legal | Nghia | 1.000 | 0.375 | 0.250 | 0.250 | 0.774 |

## Worst Performers

| ID | Problem | Proposed Fix |
|---|---|---|
| nhi_q002 | Low combined score | Improve query expansion, reranking, metadata, or source chunks |
| nghia_q003 | Low combined score | Improve query expansion, reranking, metadata, or source chunks |
| huy_q004 | Low combined score | Improve query expansion, reranking, metadata, or source chunks |
| huy_q003 | Low combined score | Improve query expansion, reranking, metadata, or source chunks |
| huy_q001 | Low combined score | Improve query expansion, reranking, metadata, or source chunks |