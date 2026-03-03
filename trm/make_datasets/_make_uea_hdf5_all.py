import os
import numpy as np
import h5py
from aeon.datasets import load_classification


def stratified_split_indices(y_int, val_ratio=0.2, seed=0):
    """
    Returns: train_idx, val_idx as numpy arrays
    Stratified split over integer labels y_int.
    """
    rng = np.random.default_rng(seed)
    y_int = np.asarray(y_int)

    train_idx = []
    val_idx = []

    for cls in np.unique(y_int):
        cls_idx = np.flatnonzero(y_int == cls)
        rng.shuffle(cls_idx)

        n_val = int(round(len(cls_idx) * val_ratio))
        val_idx.append(cls_idx[:n_val])
        train_idx.append(cls_idx[n_val:])

    train_idx = np.concatenate(train_idx) if train_idx else np.array([], dtype=int)
    val_idx = np.concatenate(val_idx) if val_idx else np.array([], dtype=int)

    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    return train_idx, val_idx


def encode_labels_with_train_classes(y_train_str, y_other_str):
    """
    Build class list from train labels, encode train and other using same mapping.
    Returns: classes (np.array of strings), y_train_int, y_other_int
    """
    classes = np.unique(y_train_str)  # sorted
    class_to_id = {c: i for i, c in enumerate(classes)}

    y_train_int = np.array([class_to_id[c] for c in y_train_str], dtype=np.int64)
    y_other_int = np.array([class_to_id[c] for c in y_other_str], dtype=np.int64)

    return classes, y_train_int, y_other_int


def save_h5(X, y_int, classes, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    X = np.asarray(X, dtype=np.float32)
    y_int = np.asarray(y_int, dtype=np.int64)

    with h5py.File(path, "w") as h5f:
        h5f.create_dataset("X", data=X)
        h5f.create_dataset("y", data=y_int)

        str_dt = h5py.string_dtype(encoding="utf-8")
        h5f.create_dataset("classes", data=classes.astype(object), dtype=str_dt)

    print(f"Saved {path} | X={X.shape} y={y_int.shape} classes={classes.tolist()}")


if __name__ == "__main__":
    # 1) Load official splits from UEA archive
    X_train_full, y_train_full = load_classification("BasicMotions", split="train")
    X_test, y_test = load_classification("BasicMotions", split="test")

    # 2) Encode labels using TRAIN classes (consistent across all splits)
    classes, y_train_full_int, y_test_int = encode_labels_with_train_classes(
        y_train_full, y_test
    )

    # 3) Create a stratified train/val split from the official train split
    train_idx, val_idx = stratified_split_indices(
        y_train_full_int, val_ratio=0.2, seed=0
    )

    X_train = X_train_full[train_idx]
    y_train = y_train_full_int[train_idx]

    X_val = X_train_full[val_idx]
    y_val = y_train_full_int[val_idx]

    # 4) Save all three
    base = "Datasets/UEA/BasicMotions/processed"
    save_h5(X_train, y_train, classes, os.path.join(base, "train.h5"))
    save_h5(X_val, y_val, classes, os.path.join(base, "val.h5"))
    save_h5(X_test, y_test_int, classes, os.path.join(base, "test.h5"))

    # 5) Tiny sanity prints
    print("Split sizes:", len(y_train), len(y_val), len(y_test_int))
    print("Train label counts:", np.bincount(y_train, minlength=len(classes)))
    print("Val   label counts:", np.bincount(y_val, minlength=len(classes)))
    print("Test  label counts:", np.bincount(y_test_int, minlength=len(classes)))