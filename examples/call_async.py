"""
Simple Lithops example using one single function invocation
"""
import lithopserve


def my_function(x):
    return x + 7


if __name__ == '__main__':
    fexec = lithopserve.FunctionExecutor()
    fexec.call_async(my_function, 3)
    print(fexec.get_result())
