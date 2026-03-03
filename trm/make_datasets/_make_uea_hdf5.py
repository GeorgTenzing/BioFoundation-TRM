import os
import numpy as np
import h5py
from aeon.datasets import load_classification
import matplotlib.pyplot as plt
import torch


def save_h5(X, y, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Convert string labels -> integer ids, and keep mapping
    classes, y_int = np.unique(y, return_inverse=True)   # classes: sorted unique strings
    y_int = y_int.astype(np.int64)

    # (optional) store X as float32 to save space + be ML-friendly
    X = X.astype(np.float32)
    
    with h5py.File(path, "w") as h5f:
        h5f.create_dataset("X", data=X)
        h5f.create_dataset("y", data=y_int)
        
        # store mapping (id -> class name) as UTF-8 variable-length strings
        str_dt = h5py.string_dtype(encoding="utf-8")
        h5f.create_dataset("classes", data=classes.astype(object), dtype=str_dt)

    print(f"Saved {path} | X={X.shape} y={y_int.shape} classes={classes.tolist()}")


if __name__ == "__main__":
    X_train, y_train = load_classification("BasicMotions", split="train")
    X_test,  y_test  = load_classification("BasicMotions", split="test")
    
    print("X_train:", type(X_train), X_train.shape, X_train.dtype)
    print("y_train:", type(y_train), y_train.shape, y_train.dtype)
    print("Unique labels train:", np.unique(y_train), "count:", len(np.unique(y_train)))

    assert isinstance(X_train, np.ndarray) and X_train.ndim == 3
    assert isinstance(y_train, np.ndarray) and y_train.ndim == 1
    assert X_train.shape[0] == y_train.shape[0]
    assert np.isfinite(X_train).all(), "Found NaN/Inf in X_train"

    # save to .h5
    save_h5(X_train, y_train, "Datasets/UEA/BasicMotions/processed/train.h5")
    save_h5(X_test,  y_test,  "Datasets/UEA/BasicMotions/processed/test.h5")
    inspect_h5()




# import os
# import pickle
# import numpy as np
# import h5py
# from tqdm import tqdm
# import argparse
# import shutil

# def create_hdf5(source_dir, target_file, group_size=1000):

#     files = os.listdir(source_dir)
#     data_group = []
    
#     files = [f for f in files if f.endswith('.npz')]
    
#     with h5py.File(target_file, 'w') as h5f:
#         for i, file in enumerate(tqdm(files, desc=f"Creating {target_file}")):
#             with open(os.path.join(source_dir, file), 'rb') as f:
#                 sample = np.load(f)
#                 data_group.append(sample)
                
#                 if (i + 1) % group_size == 0 or i == len(files) - 1:
#                     if not data_group:
#                         continue
                    
#                     X_data = np.array([s['X'] for s in data_group])
                    
#                     grp = h5f.create_group(f"data_group_{i // group_size}")
#                     grp.create_dataset("X", data=X_data)

#                     data_group = []
                    

# if __name__ == "__main__":
#     source_dir  = "/Datasets/UEA/BasicMotions/raw"
#     target_file = "/Datasets/UEA/BasicMotions/processed/train.hdf5"




def inspect_h5(): 
    path = "Datasets/UEA/BasicMotions/processed/train.h5"
    with h5py.File(path, "r") as f:
        print("keys:", list(f.keys()))
        print("X:", f["X"].shape, f["X"].dtype)
        print("y:", f["y"].shape, f["y"].dtype)
        print("classes:", f["classes"].shape, f["classes"].dtype)
    
    with h5py.File(path, "r") as f:
        y = f["y"][:]
        classes = [c.decode("utf-8") if isinstance(c, (bytes, bytearray)) else str(c) for c in f["classes"][:]]

    print("y min/max:", y.min(), y.max())
    print("unique y:", np.unique(y))
    print("classes:", classes)

    assert y.min() == 0
    assert y.max() == len(classes) - 1
    assert set(np.unique(y)) == set(range(len(classes)))
    print("✅ labels + mapping look consistent")
    
    p_tr = "Datasets/UEA/BasicMotions/processed/train.h5"
    p_te = "Datasets/UEA/BasicMotions/processed/test.h5"

    def read_classes(p):
        with h5py.File(p, "r") as f:
            cls = f["classes"][:]
        return [c.decode("utf-8") if isinstance(c, (bytes, bytearray)) else str(c) for c in cls]

    c_tr = read_classes(p_tr)
    c_te = read_classes(p_te)

    print("train classes:", c_tr)
    print("test  classes:", c_te)
    assert c_tr == c_te, "❌ train/test classes ordering differs!"
    print("✅ train/test class ordering matches")
    
    with h5py.File(path, "r") as f:
        X = torch.from_numpy(f["X"][:8])   # (B,C,T)
        y = torch.from_numpy(f["y"][:8])   # (B,)

    print("X:", X.shape, X.dtype)
    print("y:", y.shape, y.dtype)

    assert X.ndim == 3 and X.shape[1] == 6 and X.shape[2] == 100
    assert y.ndim == 1 and y.shape[0] == X.shape[0]
    print("✅ TRM-ready shapes")
    
    with h5py.File(path, "r") as f:
        X = f["X"][:]
        y = f["y"][:]
        classes = f["classes"][:]

    idx = 0
    label = classes[y[idx]]
    label = label.decode("utf-8") if isinstance(label, (bytes, bytearray)) else str(label)

    plt.figure()
    for c in range(X.shape[1]):
        plt.plot(X[idx, c], label=f"ch{c}")
    plt.title(f"train sample {idx} | y={y[idx]} ({label})")
    plt.legend()
    plt.show()
