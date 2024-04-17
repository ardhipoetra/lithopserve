from joblib.parallel import register_parallel_backend


def register_lithops():
    """ Register Lithops Backend to be called with parallel_backend("lithops_inference"). """
    try:
        from lithops_inference.util.joblib.lithops_backend import LithopsBackend
        register_parallel_backend("lithops_inference", LithopsBackend)
    except ImportError:
        msg = ("To use the Lithops backend you must install lithops_inference.")
        raise ImportError(msg)


__all__ = ["register_lithops"]
