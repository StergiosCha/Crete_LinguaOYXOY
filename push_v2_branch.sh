#!/bin/bash
# Run this from your Mac terminal inside the Crete_LinguaOYXOY_v2 folder.
# It creates a 'v2' branch on the GitHub repo with the new experiment structure.
#
# Usage:
#   cd ~/Dropbox/GLOF024/Crete_LinguaOYXOY_v2
#   bash push_v2_branch.sh

set -e

REPO="https://github.com/StergiosCha/Crete_LinguaOYXOY.git"

# 1. Remove the broken .git from Dropbox (if present)
rm -rf .git

# 2. Init fresh, add remote
git init -b main
git remote add origin "$REPO"

# 3. Fetch existing repo so we share history
git fetch origin

# 4. Create v2 branch from main
git checkout -b v2

# 5. Stage everything (except junk)
cat > .gitignore << 'EOF'
results/*.json
results/*.csv
__pycache__/
*.pyc
.DS_Store
~$*
*.tmp
EOF

git add -A

# 6. Remove old top-level stimuli files (v1 leftovers) from staging
git rm --cached stimuli/binding.jsonl stimuli/cd.jsonl stimuli/clld.jsonl \
  stimuli/crossover.jsonl stimuli/fillers.jsonl stimuli/plural_conjunction.jsonl 2>/dev/null || true

# 7. Commit
git commit -m "v2: split experiments (A: CD+CLLD, B: Binding+Crossover+PC)

- Split into Experiment A and Experiment B for human participant feasibility
- Finer-grained conditions: separate quantifier types (merikous, pollous, kathe, kanenan)
- CLLD island sub-conditions (temporal, causal, relative, complement)
- 270 total items: 134 (exp_a) + 93 (exp_b) + 43 (shared)
- Updated run_experiment.py with --exp a/b flag
- New student guide docx for v2
- Latin square design for human participants (3 lists, ~15 min each)"

# 8. Push
git push origin v2

echo ""
echo "Done! Branch 'v2' pushed to $REPO"
echo "View at: https://github.com/StergiosCha/Crete_LinguaOYXOY/tree/v2"
