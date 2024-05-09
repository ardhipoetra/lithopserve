"""
Simple Lithops example using one single function invocation
with a class as the function and a function as the parameter
"""
import lithopserve

def mult(x, y):
    return x * y


class MyClass:
    def __init__(self, base) -> None:
        self.base = base

    def __call__(self, x, fn) -> int:
        return fn(self.base, x)


if __name__ == '__main__':
    fexec = lithopserve.FunctionExecutor()
    inst = MyClass(5)
    fexec.map(inst, [(2, mult), (3, mult)])
    print(fexec.get_result())
