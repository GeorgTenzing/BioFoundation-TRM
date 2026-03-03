import os
import numpy as np
import h5py
from aeon.datasets import load_classification

def save_strict_grouped_h5(X, y, out_path, group_size=1000):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64)

    with h5py.File(out_path, "w") as f:
        n = X.shape[0]
        num_groups = (n + group_size - 1) // group_size
        for g in range(num_groups):
            s = g * group_size
            e = min((g + 1) * group_size, n)
            grp = f.create_group(f"data_group_{g}")
            grp.create_dataset("X", data=X[s:e])
            grp.create_dataset("y", data=y[s:e])

    print("Wrote", out_path)

if __name__ == "__main__":
    X_train, y_train = load_classification("BasicMotions", split="train")
    X_test,  y_test  = load_classification("BasicMotions", split="test")

    # encode labels using TRAIN classes (sorted)
    classes = np.unique(y_train)
    class_to_id = {c: i for i, c in enumerate(classes)}
    y_train = np.array([class_to_id[c] for c in y_train], dtype=np.int64)
    y_test  = np.array([class_to_id[c] for c in y_test], dtype=np.int64)

    base = "/home/gtenzing/BioFoundation-TRM/make_datasets/Datasets/UEA/BasicMotions/processed"
    save_strict_grouped_h5(X_train, y_train, os.path.join(base, "train.h5"))
    save_strict_grouped_h5(X_test,  y_test,  os.path.join(base, "test.h5"))