# Sourced by every slurm/*.slurm script: go to the project, check the container, define `run`.
#   source slurm/env.sh
#   run scripts/benchmark.py --workers "$SLURM_CPUS_PER_TASK"
# `run` is python inside slime-roads.sif, with the synced code (src/) on PYTHONPATH.
cd "$HOME/slime-roads-ro"
SIF="$HOME/slime-roads-ro/slime-roads.sif"
if [ ! -f "$SIF" ]; then
    echo "missing $SIF: build it on the login node with: bash slurm/build_sif.sh" >&2
    exit 1
fi
if [ "$(cat slurm/slime-roads.def slurm/requirements-sif.txt | sha256sum)" != "$(cat slime-roads.sif.sha256 2>/dev/null)" ]; then
    echo "WARNING: slime-roads.sif is older than slurm/slime-roads.def or requirements-sif.txt; rebuild it" >&2
fi
run() {
    apptainer exec --env PYTHONPATH="$HOME/slime-roads-ro/src" "$SIF" python "$@"
}
echo "commit: $(cat COMMIT)  node: $(hostname)  cpus: ${SLURM_CPUS_PER_TASK:-?}  job: ${SLURM_JOB_ID:-}"
