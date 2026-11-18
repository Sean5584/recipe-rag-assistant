# Topic 5 evaluation results

These snapshots record the results for the [QA benchmark](../qa_benchmark.json) on the same corpus of 374 HowToCook recipes. The experiment scripts and question set are in commit `81fa52a`. The 20 answerable questions include the 8 pilot questions; this is not an independent held-out test set.

| Chunking strategy | Document Hit@3 | Evidence Hit@3 |
| --- | ---: | ---: |
| Markdown headings | 19/20 (95%) | 14/20 (70%) |
| Fixed windows (400 characters, 80 overlap) | 20/20 (100%) | 18/20 (90%) |

[Chunking results](chunking-benchmark.json) compare pure BGE vector retrieval with identical questions and k. Evidence Hit@3 requires a retrieved chunk from the annotated recipe to contain the annotated excerpt, ignoring whitespace.

[Graded answers](graded-answers.json) record a separate run of the default QA application, using Markdown chunks, exact recipe-name lookup or hybrid retrieval, and Kimi. Answer correctness was **16/20 (80%)**; refusal correctness was **4/4 (100%)**. Answers were judged against the reference answers and source excerpts. One answerable question was incorrectly declined (p02), and three did not produce a verifiable answer (p13, p15, p19). Refusals were scored on whether the system explicitly acknowledged missing information without guessing; a citation from one excerpt does not independently prove the information is absent from the entire recipe.
