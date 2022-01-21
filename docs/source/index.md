```{toctree}
---
hidden: true
maxdepth: 2
caption: About
---
```

# HGDL

The HGDL package is a high-performance, distributed, asynchronous optimizer that can be used for fvGP and therefore gpCAM training and the acquisition function optimization. However, it is its own python API which can be installed via "pip install hgdl". We present the API below. 

Installation: pip install hgdl

To see the code and the tests: git clone https://github.com/lbl-camera/HGDL.git

current version 1.4.3

```{eval-rst}
.. autoclass:: hgdl.hgdl.HGDL
    :members:
    :special-members: __init__

```

## Example

```{code-block} python3
---
---
def main():

    from time import sleep, perf_counter
    
    from scipy.optimize import rosen, rosen_der, rosen_hess
    import numpy as np

    from hgdl.hgdl import HGDL
    
    print('this will create an hgdl object, sleep for 3'
            ' seconds, get the best result, sleep for 3 seconds,'
            'then get the final result.\n'
            'working on the epochs should happend even during sleeping\n'
            )
    a = HGDL(rosen, rosen_der,[[-2,2],[-2,2]], hess = rosen_hess, radius = 0.1, num_epochs = 10000)
    a.optimize()

    print("main thread submitted HGDL and will now sleep for 10 seconds")
    sleep(5)
    print("main thread asks for 10 best solutions:")
    print(a.get_latest(10))
    print("main sleeps for another 10 seconds")
    sleep(3)
    print("main thread kills optimization")
    res = a.kill_client()
    print("hgdl was killed but I am waiting 2s")
    sleep(2)
    print("")
    print("")
    print("")
    print("")
    print(res)

if __name__ == "__main__":
    main()
```

