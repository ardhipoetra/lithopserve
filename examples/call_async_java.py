"""
Simple Lithops example for running non-python code that is
present in the docker container runtime
"""
import lithopserve
import os
import subprocess

def my_function(arg1, arg2):
    # run an external program using the os library
    os.system(f'java your.path.Main {arg1} {arg2}')
    # or using the subrpocess library
    subprocess.Popen(f'java your.path.Main {arg1} {arg2}')


if __name__ == '__main__':
    fexec = lithopserve.FunctionExecutor()
    fexec.call_async(my_function, [3, 1])
    print(fexec.get_result())
