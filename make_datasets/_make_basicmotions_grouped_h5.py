import os
import numpy as np
import h5py
from aeon.datasets import load_classification


def encode_with_train_classes(y_train_str, y_other_str):
    classes = np.unique(y_train_str)  # sorted
    class_to_id = {c: i for i, c in enumerate(classes)}
    y_train = np.array([class_to_id[c] for c in y_train_str], dtype=np.int64)
    y_other = np.array([class_to_id[c] for c in y_other_str], dtype=np.int64)
    return classes, y_train, y_other


def stratified_split_indices(y_int, val_ratio=0.2, seed=0):
    rng = np.random.default_rng(seed)
    y_int = np.asarray(y_int)

    train_idx, val_idx = [], []
    for cls in np.unique(y_int):
        idx = np.flatnonzero(y_int == cls)
        rng.shuffle(idx)
        n_val = int(round(len(idx) * val_ratio))
        val_idx.append(idx[:n_val])
        train_idx.append(idx[n_val:])

    train_idx = np.concatenate(train_idx)
    val_idx = np.concatenate(val_idx)
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    return train_idx, val_idx


def save_grouped_h5(X, y, classes, out_path, group_size=1000):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64)

    str_dt = h5py.string_dtype(encoding="utf-8")

    with h5py.File(out_path, "w") as f:
        # store classes once at root
        # f.create_dataset("classes", data=classes.astype(object), dtype=str_dt)

        n = X.shape[0]
        num_groups = (n + group_size - 1) // group_size

        for g in range(num_groups):
            start = g * group_size
            end = min((g + 1) * group_size, n)

            grp = f.create_group(f"data_group_{g}")
            grp.create_dataset("X", data=X[start:end])
            grp.create_dataset("y", data=y[start:end])

    print(f"Saved grouped H5: {out_path} | X={X.shape} y={y.shape} groups={num_groups}")


if __name__ == "__main__":
    X_train_full, y_train_full = load_classification("BasicMotions", split="train")
    X_test, y_test = load_classification("BasicMotions", split="test")

    classes, y_train_full_int, y_test_int = encode_with_train_classes(y_train_full, y_test)

    tr_idx, va_idx = stratified_split_indices(y_train_full_int, val_ratio=0.2, seed=0)

    X_train, y_train = X_train_full[tr_idx], y_train_full_int[tr_idx]
    X_val, y_val = X_train_full[va_idx], y_train_full_int[va_idx]

    base = "Datasets/UEA/BasicMotions/processed"
    save_grouped_h5(X_train, y_train, classes, os.path.join(base, "train.h5"), group_size=1000)
    save_grouped_h5(X_val, y_val, classes, os.path.join(base, "val.h5"), group_size=1000)
    save_grouped_h5(X_test, y_test_int, classes, os.path.join(base, "test.h5"), group_size=1000)