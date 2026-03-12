"""
Download/load a UCR/UEA dataset with aeon, then write BioFoundation-compatible HDF5.

Outputs:
  <out_dir>/train.h5
  <out_dir>/val.h5
  <out_dir>/test.h5

Each .h5 contains a single group (default: dataset name) with:
  X: float32 array of shape (N, C, T)
  y: int64 array of shape (N,)

Usage (CLI):
  python make_datasets/aeon_to_hdf5.py --dataset BasicMotions --out_dir ${DATA_PATH}/Datasets/UEA/BasicMotions/processed

Usage (Jupyter):
  !python make_datasets/aeon_to_hdf5.py --dataset BasicMotions --out_dir /your/path
"""

import os
import json
import argparse
from collections import defaultdict

import numpy as np
import h5py

from aeon.datasets import load_classification

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def encode_labels_consistent(y_train, y_test):
    """
    Map labels to int64 [0..K-1] consistently across splits.
    Works for string labels or numeric labels.
    """
    y_train = np.asarray(y_train)
    y_test = np.asarray(y_test)

    # Convert to strings for a stable mapping if not already integer
    if np.issubdtype(y_train.dtype, np.integer) and np.issubdtype(y_test.dtype, np.integer):
        # Still normalize to 0..K-1 (some datasets may use 1..K)
        all_labels = np.unique(np.concatenate([y_train, y_test]))
        all_labels_sorted = np.sort(all_labels)
        mapping = {int(lbl): i for i, lbl in enumerate(all_labels_sorted)}
        y_train_enc = np.array([mapping[int(v)] for v in y_train], dtype=np.int64)
        y_test_enc = np.array([mapping[int(v)] for v in y_test], dtype=np.int64)
        class_to_id = {str(k): int(v) for k, v in mapping.items()}
        return y_train_enc, y_test_enc, class_to_id

    # string mapping
    y_train_s = y_train.astype(str)
    y_test_s = y_test.astype(str)
    all_labels = np.unique(np.concatenate([y_train_s, y_test_s]))
    class_to_id = {lbl: i for i, lbl in enumerate(all_labels)}
    y_train_enc = np.array([class_to_id[v] for v in y_train_s], dtype=np.int64)
    y_test_enc = np.array([class_to_id[v] for v in y_test_s], dtype=np.int64)
    return y_train_enc, y_test_enc, class_to_id


def stratified_split_indices(y: np.ndarray, val_ratio: float, seed: int):
    """
    Stratified train/val split indices without sklearn.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y)

    cls_to_idx = defaultdict(list)
    for i, c in enumerate(y):
        cls_to_idx[int(c)].append(i)

    train_idx, val_idx = [], []
    for c, idxs in cls_to_idx.items():
        idxs = np.array(idxs, dtype=int)
        rng.shuffle(idxs)
        n_val = int(np.round(len(idxs) * val_ratio))
        val_idx.append(idxs[:n_val])
        train_idx.append(idxs[n_val:])

    train_idx = np.concatenate(train_idx) if train_idx else np.array([], dtype=int)
    val_idx = np.concatenate(val_idx) if val_idx else np.array([], dtype=int)
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    return train_idx, val_idx


def write_h5(path: str, group: str, X: np.ndarray, y: np.ndarray) -> None:
    """
    BioFoundation expects groups with datasets X and y.
    Store X float32 and y int64.
    """
    ensure_dir(os.path.dirname(path))
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64)

    with h5py.File(path, "w") as f:
        g = f.create_group(group)
        g.create_dataset("X", data=X, compression="gzip", shuffle=True, chunks=True)
        g.create_dataset("y", data=y, compression="gzip", shuffle=True, chunks=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name (e.g., BasicMotions, ECG200, ...)")
    parser.add_argument("--out_dir", type=str, required=True, help="Output directory for processed HDF5 files")
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--group_name", type=str, default=None, help="HDF5 group name (defaults to dataset name)")

    # IMPORTANT: this makes it safe to run in Jupyter (ignores ipykernel args like --f=...)
    args, _ = parser.parse_known_args()

    group = args.group_name or args.dataset
    out_dir = args.out_dir

    # 1) Load via aeon (downloads if needed)
    # return_type="numpy3d" => X shape (N, C, T) for multivariate,
    # and (N, 1, T) for univariate (nice uniform handling).
    X_train, y_train = load_classification(args.dataset, split="train", return_type="numpy3d")
    X_test, y_test = load_classification(args.dataset, split="test", return_type="numpy3d")

    # 2) Encode labels consistently
    y_train_enc, y_test_enc, class_to_id = encode_labels_consistent(y_train, y_test)

    # 3) Train/val split from TRAIN
    tr_idx, va_idx = stratified_split_indices(y_train_enc, val_ratio=args.val_ratio, seed=args.seed)
    X_tr, y_tr = X_train[tr_idx], y_train_enc[tr_idx]
    X_va, y_va = X_train[va_idx], y_train_enc[va_idx]

    # 4) Write BioFoundation-compatible HDF5
    train_h5 = os.path.join(out_dir, "train.h5")
    val_h5 = os.path.join(out_dir, "val.h5")
    test_h5 = os.path.join(out_dir, "test.h5")

    write_h5(train_h5, group, X_tr, y_tr)
    write_h5(val_h5, group, X_va, y_va)
    write_h5(test_h5, group, X_test, y_test_enc)

    # 5) Metadata (helps debugging + config sanity)
    meta = {
        "dataset": args.dataset,
        "group": group,
        "X_layout": "(N, C, T)",
        "train_shape": list(X_tr.shape),
        "val_shape": list(X_va.shape),
        "test_shape": list(X_test.shape),
        "num_classes": int(len(np.unique(np.concatenate([y_train_enc, y_test_enc])))),
        "class_to_id": class_to_id,
        "val_ratio": args.val_ratio,
        "seed": args.seed,
    }
    ensure_dir(out_dir)
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("Wrote:")
    print(" ", train_h5)
    print(" ", val_h5)
    print(" ", test_h5)
    print("Meta:")
    print(" ", os.path.join(out_dir, "meta.json"))


if __name__ == "__main__":
    main()