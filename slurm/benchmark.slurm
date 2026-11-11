#!/bin/bash
# Simulation throughput on one haswell node (32 CPUs): sims/hour and the time for a 30x50 GA run.
#SBATCH --job-name=slime-bench
#SBATCH --partition=haswell
#SBATCH --account=student
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --mem-per-cpu=1700M
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
source "$HOME/slime-roads-ro/slurm/env.sh"
run scripts/benchmark.py --workers "$SLURM_CPUS_PER_TASK" --sims 96
