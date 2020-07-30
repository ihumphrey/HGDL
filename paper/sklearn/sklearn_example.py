import numpy as np

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
# for the fit function
from sklearn.base import clone
from sklearn.utils import check_random_state
from scipy.linalg import cholesky, cho_solve, solve_triangular
from operator import itemgetter


def main():
    def fit(self, X, y):
        if self.kernel is None:  # Use an RBF kernel as default
            self.kernel_ = C(1.0, constant_value_bounds="fixed") \
                * RBF(1.0, length_scale_bounds="fixed")
        else:
            self.kernel_ = clone(self.kernel)

        self._rng = check_random_state(self.random_state)

        if self.kernel_.requires_vector_input:
            X, y = self._validate_data(X, y, multi_output=True, y_numeric=True,
                                       ensure_2d=True, dtype="numeric")
        else:
            X, y = self._validate_data(X, y, multi_output=True, y_numeric=True,
                                       ensure_2d=False, dtype=None)

        # Normalize target value
        if self.normalize_y:
            self._y_train_mean = np.mean(y, axis=0)
            self._y_train_std = np.std(y, axis=0)

            # Remove mean and make unit variance
            y = (y - self._y_train_mean) / self._y_train_std

        else:
            self._y_train_mean = np.zeros(1)
            self._y_train_std = 1

        if np.iterable(self.alpha) \
           and self.alpha.shape[0] != y.shape[0]:
            if self.alpha.shape[0] == 1:
                self.alpha = self.alpha[0]
            else:
                raise ValueError("alpha must be a scalar or an array"
                                 " with same number of entries as y.(%d != %d)"
                                 % (self.alpha.shape[0], y.shape[0]))

        self.X_train_ = np.copy(X) if self.copy_X_train else X
        self.y_train_ = np.copy(y) if self.copy_X_train else y
        if self.optimizer is not None and self.kernel_.n_dims > 0:
            # this is the part that i wrote --------------------------------- 
            if self.optimizer == "hgdl":
                def obj(x):
                    return -self.log_marginal_likelihood(theta=x, clone_kernel=True)
                def grad(x):
                    return -self.log_marginal_likelihood(theta=x, eval_gradient=True, clone_kernel=True)[1]
                from scipy.optimize import minimize
                res = minimize(fun=obj, x0=self.kernel_.theta,
                        jac=grad, bounds=self.kernel_.bounds)
                from hgdl import HGDL
                from dask.distributed import Client
                res = HGDL(func=obj, grad=grad, bounds=self.kernel_.bounds, hess=None,
                        r = 1., client = Client(),
                        local_method='scipy', local_kwargs={'method':'L-BFGS-B'})
                res = res.get_final()
                self.log_marginal_likelihood_value_ = res['best_y']
                self.kernel_.theta = res['best_x']
                GPs = []
                for i in range(len(res['minima_y'])):
                    x, y = res['minima_x'][i], res['minima_y'][i]
                    kernel = clone(self.kernel_)
                    kernel.theta = x
                    gp = GaussianProcessRegressor(alpha=self.alpha, kernel=kernel)
                    gp.kernel_ = kernel
                    gp.log_marginal_likelihood_value_ = -y
                    GPs.append(gp)
                return GPs
            # end of the part that i wrote --------------------------------- 
            else:
                # Choose hyperparameters based on maximizing the log-marginal
                # likelihood (potentially starting from several initial values)
                def obj_func(theta, eval_gradient=True):
                    if eval_gradient:
                        lml, grad = self.log_marginal_likelihood(
                            theta, eval_gradient=True, clone_kernel=False)
                        return -lml, -grad
                    else:
                        return -self.log_marginal_likelihood(theta,
                                                             clone_kernel=False)

                # First optimize starting from theta specified in kernel
                optima = [(self._constrained_optimization(obj_func,
                                                          self.kernel_.theta,
                                                          self.kernel_.bounds))]
                # Additional runs are performed from log-uniform chosen initial
                # theta
                if self.n_restarts_optimizer > 0:
                    if not np.isfinite(self.kernel_.bounds).all():
                        raise ValueError(
                            "Multiple optimizer restarts (n_restarts_optimizer>0) "
                            "requires that all bounds are finite.")
                    bounds = self.kernel_.bounds
                    for iteration in range(self.n_restarts_optimizer):
                        theta_initial = \
                            self._rng.uniform(bounds[:, 0], bounds[:, 1])
                        optima.append(
                            self._constrained_optimization(obj_func, theta_initial,
                                                           bounds))
                # Select result from run with minimal (negative) log-marginal
                # likelihood
                lml_values = list(map(itemgetter(1), optima))
                self.kernel_.theta = optima[np.argmin(lml_values)][0]
                # this doesn't work for me - TODO
                # self.kernel_._check_bounds_params()

                self.log_marginal_likelihood_value_ = -np.min(lml_values)
        else:
            self.log_marginal_likelihood_value_ = \
                self.log_marginal_likelihood(self.kernel_.theta,
                                             clone_kernel=False)

        # Precompute quantities required for predictions which are independent
        # of actual query points
        K = self.kernel_(self.X_train_)
        K[np.diag_indices_from(K)] += self.alpha
        try:
            self.L_ = cholesky(K, lower=True)  # Line 2
            # self.L_ changed, self._K_inv needs to be recomputed
            self._K_inv = None
        except np.linalg.LinAlgError as exc:
            exc.args = ("The kernel, %s, is not returning a "
                        "positive definite matrix. Try gradually "
                        "increasing the 'alpha' parameter of your "
                        "GaussianProcessRegressor estimator."
                        % self.kernel_,) + exc.args
            raise
        self.alpha_ = cho_solve((self.L_, True), self.y_train_)  # Line 3
        return self

    # declare that we should use my fitting method
    GaussianProcessRegressor.fit = fit
    # generate data exactly as in the example
    rng = np.random.RandomState(0)
    X = rng.uniform(0, 5, 20)[:, np.newaxis]
    y = 0.5 * np.sin(3 * X[:, 0]) + rng.normal(0, 0.5, X.shape[0])
    # use the example kernels
    print('example -----------------------------------------------------------')
    kernel1 = 1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e3)) \
        + WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-10, 1e+1))
    kernel2 = 1.0 * RBF(length_scale=100.0, length_scale_bounds=(1e-2, 1e3)) \
        + WhiteKernel(noise_level=1, noise_level_bounds=(1e-10, 1e+1))
    gp1 = GaussianProcessRegressor(kernel=kernel1,alpha=0.0).fit(X, y)
    gp2 = GaussianProcessRegressor(kernel=kernel2,alpha=0.0).fit(X, y)
    for i, gp in enumerate([gp1, gp2]):
        print('gp - example (',i+1,'): ', gp, '\nkernel:', gp.kernel_)
        print('likelihood:', gp.log_marginal_likelihood_value_)
    # one function call to find many minima 
    print('HGDL -----------------------------------------------------------')
    GPs = GaussianProcessRegressor(kernel=kernel1,alpha=0.0, optimizer='hgdl').fit(X, y)
    for i, gp in enumerate(GPs):
        print('gp - HGDL (',i+1,'): ', gp, '\nkernel:', gp.kernel_)
        print('likelihood:', gp.log_marginal_likelihood_value_)



if __name__ == "__main__":
    main()