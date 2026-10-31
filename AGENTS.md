# Repository contribution instructions

## Publication quality gate

Use the locally installed `blader/humanizer` agent skill on **all human-facing prose** changed by a contribution, including README files, Markdown documentation, notebook markdown cells, comments/docstrings when prose needs editing, commit/PR descriptions, and tutorial text. Read the skill rules from the installed skill rather than relying on vague "make it human" wording.

- Rewrite prose into natural, precise technical or research writing.
- Preserve facts, exact benchmark values, citations, code, mathematical definitions, data contracts, paths, and link destinations.
- Do not rewrite algorithms, tests, datasets, configuration syntax, generated outputs, or lockfiles merely to make them sound human.
- Do not invent experiments or results. Notebook outputs must come from genuinely executed cells on the documented dataset.
- Each notebook should be a complete, independent data-science report modeled on the depth of `Cancer Cell Detection.ipynb`: research questions, thoughtful EDA, feature analysis, visualization, comparison, errors, conclusions and limitations. Mention the engineering implementation only briefly at the end.
- The modular software-engineering implementation and its tests remain a separate maintained component.
- Use genuine real datasets and record provenance and rights. If unavailable, do not substitute synthetic observations for project performance claims.

Before publishing, run tests, inspect the notebook cell execution/output state when applicable, review the diff for sensitive information and unsupported claims, and confirm that Humanizer was applied to changed prose. If it was not, **do not claim the publication review passed**.

## Codex review instruction

When asked to prepare changes for GitHub:

1. Use the installed `humanizer` skill on the changed prose.
2. Run the appropriate project tests and check notebook outputs when relevant.
3. Summarize any findings, including missing real data, uncleared rights, or unexecuted cells.
4. Only then propose a commit or push. Never fake output to pass a check.

This file guides AI coding agents. It does not by itself enforce a server-side GitHub protection rule; branch protection or a CI check is needed for mechanical enforcement.
