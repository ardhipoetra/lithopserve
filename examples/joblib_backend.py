import joblib
from joblib import Parallel, delayed
from lithopserve.util.joblib import register_lithops
from lithopserve.utils import setup_lithops_logger

register_lithops()


def my_function(x):
    print(x)


setup_lithops_logger('INFO')

with joblib.parallel_backend('lithopserve'):
    Parallel()(delayed(my_function)(i) for i in range(10))
