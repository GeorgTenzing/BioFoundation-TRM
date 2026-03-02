import os
import numpy as np
import h5py
from aeon.datasets import load_classification


def save_h5(X, y, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with h5py.File(path, "w") as h5f:
        h5f.create_dataset("X", data=X)
        h5f.create_dataset("y", data=y)
    print(f"Saved {path}")


if __name__ == "__main__":
    # load train
    X_train, y_train = load_classification(
        name="BasicMotions",
        split="train",
        return_metadata=False
    )

    # load test
    X_test, y_test = load_classification(
        name="BasicMotions",
        split="test",
        return_metadata=False
    )
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