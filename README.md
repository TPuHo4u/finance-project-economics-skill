# Finance Project Economics

A Codex and Claude Code skill for building and reviewing project financial and economic cases (ФЭО). The skill instructions and working material are in Russian.

Use it on its own with a project description, decision question, or financial model; access to the course or another skill is not required. It also accepts finished UX research, a CJM, a problem card, or outputs from other course skills without asking the user to repeat that work. It adds a financial layer, keeps evidence and assumptions distinct, and returns decision thresholds and pilot measurements. A UX hypothesis does not become a proven financial effect just by being handed off.

The package includes source references and four SHA-256 identifiers, but not the source PDFs or course files.

## Clone

```sh
git clone https://github.com/TPuHo4u/finance-project-economics-skill.git
cd finance-project-economics-skill
```

## Install for Codex

```sh
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD/skills/finance-project-economics" "$HOME/.agents/skills/finance-project-economics"
```

## Install for Claude Code

```sh
mkdir -p "$HOME/.claude/skills"
ln -s "$PWD/skills/finance-project-economics" "$HOME/.claude/skills/finance-project-economics"
```

The `ln -s` commands are quoted and do not replace an existing destination. If a destination already exists, inspect it before changing the installation.

## Check the package

Run `python3 -B dev/check.py` to verify copied-file hashes, skill frontmatter, relative links, and the source-hash manifest. If a ZIP bundle is added to the repository root, the checker also compares its copied skill files byte-for-byte.
