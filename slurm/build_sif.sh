#!/bin/bash
# Build ~/slime-roads-ro/slime-roads.sif from slurm/slime-roads.def on the FEP login node (it has internet).
# Unprivileged build (Apptainer >= 1.1, user namespaces). A few minutes; ~0.4 GB.
# slime-roads.sif.sha256 records which def + requirements it was built from; cluster-sync compares it.
set -euo pipefail
cd "$HOME/slime-roads-ro"
export APPTAINER_TMPDIR="${APPTAINER_TMPDIR:-/tmp}"
apptainer build --force slime-roads.sif.new slurm/slime-roads.def
mv slime-roads.sif.new slime-roads.sif
cat slurm/slime-roads.def slurm/requirements-sif.txt | sha256sum > slime-roads.sif.sha256
apptainer exec --env PYTHONPATH="$PWD/src" slime-roads.sif \
    python -c "import slime.sim.agent; print('slime package imports inside the sif')"
ls -lh slime-roads.sif
