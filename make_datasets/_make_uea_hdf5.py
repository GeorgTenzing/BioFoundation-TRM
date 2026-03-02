import os
import json
import argparse
import numpy as np
import h5py

# aeon provides a built-in loader for BasicMotions
# returns X as numpy3d by default: (n_cases, n_channels, n_timepoints) for equal-length data
from aeon.datasets import load_basic_motions  # aeon>=? provides this API


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _stratified_train_val_split(X, y, val_ratio=0.2, seed=0):
    """
    Simple stratified split without depending hard on scikit-learn.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y)

    train_idx = []
    val_idx = []

    classes = np.unique(y)
    for c in classes:
        idx = np.flatnonzero(y == c)
        rng.shuffle(idx)
        n_val = int(np.round(len(idx) * val_ratio))
        val_idx.append(idx[:n_val])
        train_idx.append(idx[n_val:])

    train_idx = np.concatenate(train_idx) if train_idx else np.array([], dtype=int)
    val_idx = np.concatenate(val_idx) if val_idx else np.array([], dtype=int)

    rng.shuffle(train_idx)
    rng.shuffle(val_idx)

    return X[train_idx], y[train_idx], X[val_idx], y[val_idx]


def _encode_labels(y):
    """
    Ensure y is int64 [0..K-1]. Keep mapping for reproducibility.
    """
    y = np.asarray(y)
    # If already numeric ints starting at 0, keep it (but still record mapping)
    if np.issubdtype(y.dtype, np.integer):
        classes = np.unique(y)
        class_to_id = {str(c): int(c) for c in classes}
        y_enc = y.astype(np.int64)
        return y_enc, class_to_id

    classes = np.unique(y.astype(str))
    class_to_id = {c: i for i, c in enumerate(classes)}
    y_enc = np.array([class_to_id[str(v)] for v in y], dtype=np.int64)
    return y_enc, class_to_id


def write_h5(filepath: str, group_name: str, X: np.ndarray, y: np.ndarray):
    """
    BioFoundation's HDF5Loader iterates over top-level groups, and expects each group
    to have datasets 'X' and (in finetune mode) 'y'. :contentReference[oaicite:2]{index=2}
    """
    X = np.asarray(X, dtype=np.float32)   # model inputs
    y = np.asarray(y, dtype=np.int64)     # classification labels

    _ensure_dir(os.path.dirname(filepath))

    with h5py.File(filepath, "w") as h5f:
        grp = h5f.create_group(group_name)

        # Chunking + compression helps when datasets get larger; harmless here.
        grp.create_dataset(
            "X",
            data=X,
            compression="gzip",
            chunks=True,
            shuffle=True,
        )
        grp.create_dataset(
            "y",
            data=y,
            compression="gzip",
            chunks=True,
            shuffle=True,
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out_dir",
        type=str,
        required=True,
        help="Output directory, e.g. ${DATA_PATH}/UEA_MTS/BasicMotions/processed",
    )
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--group_name",
        type=str,
        default="basicmotions",
        help="Top-level HDF5 group name (any name is fine).",
    )
    args = parser.parse_args()

    # 1) Load data via aeon (downloads from timeseriesclassification.com if needed)
    # BasicMotions is equal length multivariate; X is (N, C, T) in numpy3d return_type. :contentReference[oaicite:3]{index=3}
    X_train, y_train = load_basic_motions(split="TRAIN", return_type="numpy3d")
    X_test, y_test = load_basic_motions(split="TEST", return_type="numpy3d")

    # 2) Encode labels to 0..K-1 consistently across splits
    y_train_enc, class_to_id = _encode_labels(y_train)
    # apply mapping to test
    y_test = np.asarray(y_test).astype(str)
    y_test_enc = np.array([class_to_id[str(v)] for v in y_test], dtype=np.int64)

    # 3) Train/val split (stratified)
    X_tr, y_tr, X_val, y_val = _stratified_train_val_split(
        X_train, y_train_enc, val_ratio=args.val_ratio, seed=args.seed
    )

    # 4) Write HDF5 files
    out_train = os.path.join(args.out_dir, "train.h5")
    out_val = os.path.join(args.out_dir, "val.h5")
    out_test = os.path.join(args.out_dir, "test.h5")

    write_h5(out_train, args.group_name, X_tr, y_tr)
    write_h5(out_val, args.group_name, X_val, y_val)
    write_h5(out_test, args.group_name, X_test, y_test_enc)

    # 5) Save metadata (optional but recommended)
    meta = {
        "dataset": "BasicMotions",
        "X_format": "numpy3d",
        "shape_train": list(X_tr.shape),
        "shape_val": list(X_val.shape),
        "shape_test": list(X_test.shape),
        "class_to_id": class_to_id,
        "channel_order_note": "acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z",
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("Wrote:", out_train, out_val, out_test)
    print("Meta:", os.path.join(args.out_dir, "meta.json"))


if __name__ == "__main__":
    main()