#!/bin/bash
set -e

export PYTHONPATH=/home/ysd2484/vela2
PYTHON=/home/ysd2484/miniconda3/envs/vela313/bin/python

# $PYTHON scripts/get_hub_sizes.py
# $PYTHON scripts/build_graph.py

# for Y in 2023 2024; do
#   echo "--- RUNNING PIPELINE FOR $Y-01-01 ---"
#   $PYTHON scripts/query_graph.py --t-anchor $Y-01-01
#   $PYTHON scripts/train_embeddings.py --t-anchor $Y-01-01
#   $PYTHON scripts/assemble_features.py --t-anchor $Y-01-01
#   # Individual models still trained for reference
#   $PYTHON scripts/train_model.py --t-anchor $Y-01-01 || true
# done

echo "--- CACHING POOLED MODEL TARGETS ---"
for Y in 2010 2013 2016 2019 2022; do
  $PYTHON scripts/cache_targets.py $Y-01-01
done

echo "--- CACHING POOLED MODEL TARGETS ---"
for Y in 2010 2013 2016 2019 2022 2024; do
  $PYTHON scripts/cache_targets.py $Y-01-01
done

echo "--- TRAINING POOLED SUPER MODEL ---"
$PYTHON scripts/train_pooled_model.py --train-anchors 2010-01-01 2013-01-01 2016-01-01 2019-01-01

echo "--- RUNNING EVALUATION ---"
$PYTHON scripts/test_model_performance.py --t-anchor 2024-01-01 --out-dir docs/
