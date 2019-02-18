import numpy as NP
import scipy.linalg
import matplotlib.pyplot as PLT
from tqdm import tqdm as TQDM
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from .variogram import variogram as VAR
from .utility import get_neighors_brutal

algorithms = ['kdtree', 'brutal']

class kriging_ordinary(VAR):

    def __init__(self, variogram=None, useNugget=False, distance_type='euclidean', lag_range=None, lag_max=NP.inf, variogram_model='poly1', variogram_params=None, variogram_paramsbound=None, n_jobs=1, variogram_good_lowbin_fit=False, tqdm=False, debug=False, algorithm='kdtree'):
     
        self.n_features = 0
        self.params = variogram_params 
        self.params_bound = variogram_paramsbound
        self.update_variogram(variogram)
        self.update_good_lowbin_fit(variogram_good_lowbin_fit)
        self.update_tqdm(tqdm)
        self.update_debug(debug)
        self.update_useNugget(useNugget)
        self.update_n_jobs(n_jobs)
        self.update_algorithm(algorithm)
        self.update_model(variogram_model)
        self.update_lag_range(lag_range)
        self.update_lag_max(lag_max)
        self.update_distance_type(distance_type)

    def update_good_lowbin_fit(self, good_lowbin_fit):
        '''
        [DESCRIPTION]
            Update good_lowbin_fit option to turn on/off to improve the fitting in lowed bins.
            The model has to be re-fit by calling update_fit() after updated variogram.
        [INPUT]
            good_lowbin_fit : bool 
        [OUTPUT]
            Null
        '''
        self.good_lowbin_fit = good_lowbin_fit

    def update_tqdm(self, tqdm):
        '''
        [DESCRIPTION]
            Turn on/off to runing process bar.
        [INPUT]
            tqdm : bool 
        [OUTPUT]
            Null
        '''
        self.tqdm = tqdm

    def update_debug(self, debug):
        '''
        [DESCRIPTION]
            Turn on/off to debug.
        [INPUT]
            debug : bool 
        [OUTPUT]
            Null
        '''

        self.debug = debug

    def update_useNugget(self, useNugget):
        '''
        [DESCRIPTION]
            Update useNugget option to turn on/off to use nugget be the diagonal of Kriging matrix.
            The model has to be re-fit by calling update_fit() after updated variogram.
        [INPUT]
            useNugget : bool 
        [OUTPUT]
            Null
        '''
        self._useNugget = useNugget

    def update_algorithm(self, algorithm):
        '''
        [DESCRIPTION]
            update algorithm of data structure
        [INPUT]
            algorithm : string, algorithm name of data structure %s
        [OUTPUT]
            Null
        '''%( algorithms )
        if algorithm.lower() in algorithms:
            self._algorithm = algorithm
        else:
            print('>> [WARNING] %d not found in algorithm list'% algorithm)
            print('             list: ', algorithms)
            self._algorithm = 'kdtree'

    def update_variogram(self, variogram):
        '''
        [DESCRIPTION]
            Update variogram model. The model has to be re-fit by calling update_fit() after updated variogram.
        [INPUT]
            variogram : callable, input variogram model
        [OUTPUT]
            Null
        '''
        self._variogram = variogram

    def update_fit(self, X=None, y=None, to=None, transparent=True, show=False):
        '''
        [DESCRIPTION]
            Update the fitting. If X and y are not None, it stores the data with KDTree or original data structure, 
            and it re-fit the variogram model with set parameters. Otherwise, it do re-fit only. 
        [INPUT]
            X          : array-like, input data with features, same data size with y. (None)
            y          : array-like, input data with interesting value, same data size with X. (None)
            to         : string,     path to save plot (None) 
            transparent: True,       transparent background of plot (True)
            show       : bool,       if show on screen (True)
        [OUTPUT]
            Null
        '''
        if X is not None:
            if self._algorithm == 'kdtree':
                self.X = cKDTree(X, copy_data=True)
            else:
                self.X = X
        if y is not None: 
            self.y = y

        if self._algorithm == 'kdtree': 
            self.fit(self.X.data, self.y, to=to, transparent=transparent, show=show)
        else:
            self.fit(self.X, self.y, to=to, transparent=transparent, show=show)

    def fit(self, X, y, to=None, transparent=True, show=False):
        '''
        [DESCRIPTION]
            Store the data with KDTree or original data structure, and fit the variogram model with set parameters. 
        [INPUT]
            X          : array-like, input data with features, same data size with y.
            y          : array-like, input data with interesting value, same data size with X
            to         : string,     path to save plot (None) 
            transparent: True,       transparent background of plot (True)
            show       : bool,       if show on screen (True)
        [OUTPUT]
            Null
        '''
        X = NP.atleast_1d(X)
        y = NP.atleast_1d(y)
        if len(X) != len(y):
            print(">> [ERROR] different size %di, %d"%(len(X), len(y)))
            raise
        if self._variogram is None:
            print('>> [INFO] creating variogram....')
            self._variogram = VAR(lag_range=self.lag_range, 
                                  lag_max=self.lag_max, 
                                  distance_type=self.distance_type, 
                                  model=self.model_name, 
                                  model_params=self.params, 
                                  model_paramsbound=self.params_bound, 
                                  n_jobs=self.n_jobs, 
                                  good_lowbin_fit=self.good_lowbin_fit, 
                                  tqdm=self.tqdm,
                                  debug=self.debug)
            self._variogram.fit(X,y)
            if self.debug:
                print('>> [DONE] Sill %.2f, ragne %.2f, nuget %.2f'%( self._variogram.get_params()[0], 
                                                                      self._variogram.get_params()[1], 
                                                                      self._variogram.get_params()[2]))
        else:
            if self.debug:
                print('>> [INFO] kriging_ordinary::fit(): do nothing due to variogram existed')
            else:
                pass

        self.y = y
        if self._algorithm == 'kdtree':
            self.X = cKDTree(X, copy_data=True)
        else:
            self.X = X

        if len(NP.shape(X)) == 1:
            self.n_features = 1
        else:
            self.n_features = NP.shape(X)[1]

        self._variogram.plot(to=to, transparent=transparent, show=show)

    def variogram(self):
        '''
        [DESCRIPTION]
            call the variogram model.
        [INPUT]
            Null
        [OUTPUT]
            callable, variogram model
        '''
        return self._variogram

    def predict(self, X, n_neighbor=5, radius=NP.inf, get_error=False):
        '''
        [DESCRIPTION]
           Calculate and predict interesting value with looping for all data, the method take long time but save memory
           Obtain the linear argibra terms
            | V_ij 1 || w_i | = | V_k |
            |  1   0 ||  u  |   |  1  |
                a    *   w    =    b
              w = a^-1 * b
              y = w_i * Y
            V_ij : semi-variance matrix within n neighors
            V_k  : semi-variance vector between interesting point and n neighbors
            w_i  : weights for linear combination
            u    : lagrainge multiplier
            Y    : true value of neighbors
            y    : predicted value of interesting point
        [INPUT]
            X          : array-like, input data with same number of fearture in training data
            n_neighbor : int,        number of neighbor w.r.t input data, while distance < searching radius (5)
            radius     : float,      searching radius w.r.t input data (inf)
            get_error  : bool,       if return error (False)
        [OUTPUT]
            1D/2D array(float)
            prediction : float, prdicted value via Kriging system
            error      : float, error of predicted value (only if get_error = True)
        '''
        X = NP.atleast_1d(X)
        if len(NP.shape(X)) == 1:
            if self.n_features == len(X):
                X = NP.atleast_2d(X)
            elif self.n_features != 1:
                print('>> [ERROR] wrong input number of features %d, %d'%( 1, self.n_features))
                return
        elif NP.shape(X)[1] != self.n_features:
            print('>> [ERROR] wrong input number of features %d, %d'%( NP.shape(X)[1], self.n_features))
            return

        if n_neighbor <= 0:
            print(">> [ERROR] number of neighbor must be > 0")
            return

        if radius <= 0:
            print('>> [ERROR] radius must be > 0')
            return

        ## Find the neighbors 
        if self._algorithm == 'kdtree':
            if self.debug:
                print('>> [INFO] Finding closest neighbors with kdtree....')
            if self.distance_type == 'cityblock':
                neighbor_dst, neighbor_idx = self.X.query(X, k=n_neighbor, p=1 )
            else:
                neighbor_dst, neighbor_idx = self.X.query(X, k=n_neighbor, p=2 )
        else:
            if self.debug:
                print('>> [INFO] Finding closest neighbors with brutal loops....')
            neighbor_dst, neighbor_idx = get_neighors_brutal( X, self.X, k=n_neighbor, distance=self.distance, n_jobs=self.n_jobs, tqdm=self.tqdm)

        ## Calculate prediction
        if self.debug:
            print('>> [INFO] calculation prediction for %d data....'% len(X))
        if self.tqdm:
            batches = TQDM(range(0, len(X)))
        else:
            batches = range(0, len(X))

        results = NP.zeros(len(X))
        errors = NP.zeros(len(X))
        for nd, ni, i in zip(neighbor_dst, neighbor_idx, batches):
            if self.tqdm:
                batches.set_description(">> ")

            ni = ni[nd < radius] # neighbors' index, while the distance < search radius
            nd = nd[nd < radius] # neighbors' distance, while the distance < search radius

            if len(ni) == 0: 
                continue 
            else: 
                n = len(ni)

            ## Initialization
            a = NP.zeros((n+1,n+1))  
            b = NP.ones((n+1, 1))

            ## Fill matrix a
            if self._algorithm == 'kdtree': 
                D = cdist(self.X.data[ni], self.X.data[ni], metric=self.distance_type)
            else:
                D = cdist(self.X[ni], self.X[ni], metric=self.distance_type)
            a[:n, :n] = self._variogram.predict(D)
            a[:, n] = 1
            a[n, :] = 1
            a[n, n] = 0

            ## Fill vector b
            b[:-1, 0] = self._variogram.predict(nd)

            ## set self-varinace is zero if not using Nugget
            if not self._useNugget:
                ## modify a
                NP.fill_diagonal(a, 0.)
                ## modify b
                zero_index = NP.where(NP.absolute(nd) == 0)
                if len(zero_index) > 0:
                    b[zero_index[0], 0] = 0.

            ## Get weights
            w = scipy.linalg.solve(a, b)

            ## Fill results
            results[i] = w[:n, 0].dot(self.y[ni])
            errors[i] = w[:, 0].dot(b[:, 0])

        if self.tqdm: 
            batches.close()

        if get_error:
            return results, errors
        else:
            return results

            
    def plot(self, to=None, title='', transparent=True, show=True):
        """
        [DESCRIPTION]
            Displays or draw variogram model with the actual binned data.
        [INPUT]
            to          : string, path to save plot (None) 
            title       : string, title in the plot ('')
            transparent : True,   transparent background of plot (True)
            show        : bool,   if show on screen (True)
        [OUTPUT]
            Null
        """
        fig = PLT.figure()
        ax = fig.add_subplot(111)
        ax.plot(self._variogram.lags, self._variogram.variances, 'r*')
        ax.plot(self._variogram.lags, self._variogram.model(self._variogram.params, self._variogram.lags), 'k-')
        PLT.title(title)
        if show:
            PLT.show()
        if to is not None:
            print('>> [INFO] Saving plot to %s'% to)
            PLT.savefig(to, transparent=transparent)

