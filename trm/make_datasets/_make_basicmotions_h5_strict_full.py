import os
import numpy as np
import h5py
from aeon.datasets import load_classification

# Optional but recommended for stratified split
try:
    from sklearn.model_selection import train_test_split
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False


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

    print("Wrote", out_path, "X:", X.shape, "y:", y.shape)


def encode_labels_from_train(y_train, y_other):
    """Fit mapping on train labels, apply to any other split."""
    classes = np.unique(y_train)
    class_to_id = {c: i for i, c in enumerate(classes)}

    def _map(y):
        y = np.asarray(y)
        # Fail early if test/val contains unseen labels (shouldn't happen for UEA)
        unknown = set(np.unique(y)) - set(classes)
        if unknown:
            raise ValueError(f"Found labels not in train classes: {unknown}")
        return np.array([class_to_id[c] for c in y], dtype=np.int64)

    return _map(y_train), _map(y_other)


def make_train_val_split(X_train, y_train, val_ratio=0.2, seed=42):
    """Split train into (train, val). Stratified if sklearn exists."""
    n = len(y_train)
    if val_ratio <= 0.0:
        return X_train, y_train, None, None

    if _HAS_SKLEARN:
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train, y_train,
            test_size=val_ratio,
            random_state=seed,
            shuffle=True,
            stratify=y_train,
        )
        return X_tr, y_tr, X_val, y_val

    # Fallback: no sklearn → do a simple shuffled split (not stratified)
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_val = int(round(n * val_ratio))
    val_idx = idx[:n_val]
    tr_idx  = idx[n_val:]
    return X_train[tr_idx], y_train[tr_idx], X_train[val_idx], y_train[val_idx]


if __name__ == "__main__":
    dataset = "BasicMotions"
    val_ratio = 0.2
    seed = 42

    X_train_full, y_train_full = load_classification(dataset, split="train")
    X_test,       y_test       = load_classification(dataset, split="test")

    # --- create val split from train ---
    X_train, y_train, X_val, y_val = make_train_val_split(
        np.asarray(X_train_full),
        np.asarray(y_train_full),
        val_ratio=val_ratio,
        seed=seed,
    )

    # --- label encoding: fit on TRAIN ONLY ---
    y_train_enc, y_test_enc = encode_labels_from_train(y_train, y_test)
    if X_val is not None:
        y_train_enc, y_val_enc = encode_labels_from_train(y_train, y_val)
    else:
        y_val_enc = None

    base = "/home/gtenzing/BioFoundation-TRM/trm/make_datasets/Datasets/UEA/BasicMotions/processed"
    save_strict_grouped_h5(X_train, y_train_enc, os.path.join(base, "train.h5"))
    if X_val is not None:
        save_strict_grouped_h5(X_val, y_val_enc, os.path.join(base, "val.h5"))
    save_strict_grouped_h5(X_test,  y_test_enc,  os.path.join(base, "test.h5"))

    print("Done.")