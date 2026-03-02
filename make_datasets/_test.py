# import numpy as np
# print("Hello world")
# print(np.array([1, 2, 3]))
import sys, site
print("executable:", sys.executable)
print("version:", sys.version)
print("usersite:", site.getusersitepackages())
print("sitepackages:", site.getsitepackages() if hasattr(site, "getsitepackages") else "n/a")