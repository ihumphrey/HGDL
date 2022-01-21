# HGDL

HGDL is an API for HPC distributed function optimization. At the core, the algorithm uses local and global optimization and bump-function-based deflation to provide a growing list of unique optima of a differetniable functions. This tackles the common problem of non-uniquness of optimization problems, especially in machine learning.

## Usage

The following demonstrates a simple usage of the HGDL API

```python
import numpy as np
from hgdl.hgdl import HGDL as hgdl
from support_functions import *
import dask.distributed as distributed

bounds = np.array([[-500,500],[-500,500]])
#dask_client = distributed.Client("10.0.0.184:8786")
a = hgdl(schwefel, schwefel_gradient, bounds,
        hess = schwefel_hessian,
        #global_optimizer = "random",
        global_optimizer = "genetic",
        #global_optimizer = "gauss",
        local_optimizer = "dNewton",
        number_of_optima = 30000, info = True,
        args = (arr,brr), radius = None, num_epochs = 100)

x0 = np.random.uniform(low = bounds[:, 0], high = bounds[:,1],size = (20,2))
a.optimize(x0 = x0)
```


## Credits

Main Developers: Marcus Noack ([MarcusNoack@lbl.gov](mailto:MarcusNoack@lbl.gov)) and David Perryman
Several people from across the DOE national labs have given insights
that led the code in it's current form.
See [AUTHORS](AUTHORS.rst) for more details on that.


