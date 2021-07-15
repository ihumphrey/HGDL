import numpy as np
from hgdl.hgdl import HGDL as hgdl
from test_functions import *
import time
import dask.distributed as distributed
import tracemalloc



def main():
    arr  = 5
    brr  = 6
    bounds = np.array([[-500,500],[-500,500]])
    #dask_client = distributed.Client("10.0.0.184:8786")
    a = hgdl(schwefel, schwefel_gradient, hess = schwefel_hessian,bounds = bounds,
            global_optimizer = "genetic",
            local_optimizer = "L-BFGS-B",
            number_of_optima = 300,
            args = (arr,brr), radius = 5.0, num_epochs = 8000)
    #a.optimize(dask_client = distributed.Client())
    x0 = np.random.uniform(low = bounds[:, 0], high = bounds[:,1],size = (20,2))
    print("starting positions: ")
    print(x0)
    print("--------------------")
    a.optimize(x0 = x0)
    #a.optimize(dask_client = False)
    #res = a.optima_list
    #print(res)


    #print(a.optima_list)
    print("main thread submitted HGDL and will now sleep for 2 seconds")
    time.sleep(2)
    print("main thread asks for 10 best solutions:")
    print(a.get_latest())
    #a.cancel_tasks()
    print("main sleeps for another 2 seconds")
    time.sleep(2)
    print("main thread kills optimization")
    res = a.kill()
    print("hgdl was killed but I am waiting 2s")
    print("")
    print("")
    print("")
    print("")
    print(res)

if __name__ == '__main__':
    main()