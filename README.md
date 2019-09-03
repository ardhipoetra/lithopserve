PyWren over IBM Cloud Functions and IBM Cloud Object Storage
==============================

### What is PyWren
[PyWren](https://github.com/pywren/pywren) is an open source project whose goals are massively scaling the execution of Python code and its dependencies on serverless computing platforms and monitoring the results. PyWren delivers the user’s code into the serverless platform without requiring knowledge of how functions are invoked and run. 

PyWren provides great value for the variety of uses cases, like processing data in object storage, running embarrassingly parallel compute jobs (e.g. Monte-Carlo simulations), enriching data with additional attributes and many more

### PyWren and IBM Cloud
This repository is based on [PyWren](https://github.com/pywren/pywren) main branch and adapted for IBM Cloud Functions and IBM Cloud Object Storage. 
PyWren for IBM Cloud is based on Docker images and we also extended PyWren to execute a reduce function, which now enables PyWren to run complete map reduce flows.  In extending PyWren to work with IBM Cloud Object Storage, we also added a partition discovery component that allows PyWren to process large amounts of data stored in the IBM Cloud Object Storage. See [changelog](CHANGELOG.md) for more details.

This document describes the steps to use PyWren over IBM Cloud Functions and IBM Cloud Object Storage.

### IBM Cloud for Academic institutions
[IBM Academic Initiative](https://ibm.biz/academic) is a special program that allows free trial of IBM Cloud for Academic institutions. This program is provided for students and faculty staff members, and allow up to 12 month of free usage. You can register your university email and get a free of charge account.


# Getting Started
1. [Initial requirements](#initial-requirements)
2. [PyWren setup](#pywren-setup)
3. [Configuration](#configuration)
4. [Verify installation](#verify)
5. [How to use PyWren for IBM Cloud](#how-to-use-pywren-for-ibm-cloud-functions)
6. [Using PyWren to process data from IBM Cloud Object Storage](#using-pywren-to-process-data-from-ibm-cloud-object-storage)
7. [PyWren on IBM Watson Studio and Jupyter notebooks](#pywren-on-ibm-watson-studio-and-jupyter-notebooks)
8. [Additional resources](#additional-resources)


## Initial Requirements
* IBM Cloud Functions account, as described [here](https://cloud.ibm.com/openwhisk/). Make sure you can run end-to-end example with Python.
* IBM Cloud Object Storage [account](https://www.ibm.com/cloud/object-storage)
* Python 3.5, Python 3.6 or Python 3.7


## PyWren Setup

Install PyWren from the PyPi repository:

	pip install pywren-ibm-cloud

Installation for developers can be found [here](docs/dev-installation.md).


## Configuration
To make IBM-PyWren running, configure the client with the access details to your IBM Cloud Object Storage and IBM Cloud Functions accounts. IBM-PyWren can be configured trough a configuration file or an in-runtime Python dictionary.

You can find the complete instructions and all the available configuration keys [here](config/).


##  Runtime
The runtime is the place where your functions will be executed. In IBM-PyWren, runtimes are based on docker images, and it includes by default three different runtimes that allows you to run functions with Python 3.5, 3.6 and 3.7 environments. IBM-PyWren automatically deploys the default runtime, based on the Python version you are using, the first time you execute a function. Additionally, you can also build custom runtimes with libraries that your functions depends on. 

Check more information about runtimes [here](runtime/).


## Verify 

To test that all is working, use the command:

    python -m pywren_ibm_cloud.tests

Notice that if you didn't set a local PyWren's config file, you need to provide it as a json file path by `-c <CONFIG>` flag. 

Alternatively, for debugging purposes, you can run specific tests by `-t <TESTNAME>`. use `--help` flag to get more information about the test script.


## How to use PyWren for IBM Cloud Functions

The primary object in IBM-PyWren is an executor. The standard way to get everything set up is to import pywren_ibm_cloud, and call the ibm_cf_executor() function.

```python
import pywren_ibm_cloud as pywren
pw = pywren.ibm_cf_executor()
```

IBM-PyWren API (executor) includes three different methods to execute functions in the cloud: `call_async()`, `map()`, and `map_reduce()`, one method to track function activations: `monitor()`, and one method to get the final results: `get_result()`. Additionally, it has two new methods: `create_execution_plots()` and `clean()` described below.


|API Call| Type | Description|
|---|---|---|
|call_async() | Async. | Method used to spawn one function activation |
|map() | Async. | Method used to spawn multiple function activations |
|map_reduce() | Async. | Method used to spawn multiple function activations with one (or multiple) reducers|
|---|---|---|
|monitor() | Sync. | Method used to track function activations. It blocks the local execution until all the function activations finished their execution (configurable)|
|get_result() | Sync. | Method used to retrieve the results of all function activations. The results are returned within an ordered list, where each element of the list is the result of one activation|
|---|---|---|
|create_execution_plots() | Sync. | Method used to create execution plots |
|clean() | Async. | Method used to clean the temporary data generated by PyWren in IBM COS |


The complete API details and instructions on how to use PyWren for IBM Cloud can be found [here](docs/pywren-usage.md).


## Using PyWren to process data from IBM Cloud Object Storage

PyWren for IBM Cloud functions has built-in logic for processing data objects from IBM Cloud Object Storage.
	
We designed a partitioner within the **map()** and **map_reduce()** methods that is configurable by specifying the size of the chunk.  The input to the partitioner may be either a list of data objects, a list of URLs or the entire bucket itself. The partitioner is activated inside PyWren and it responsible to split the objects into smaller chunks. It executes one *`my_map_function`* for each object chunk and when all executions are completed, the partitioner executes the *`my_reduce_function`*. The reduce function will wait for all the partial results before processing them. 

In the parameters of the `my_map_function` function you must specify a parameter called **data_stream**. This variable allows access to the data stream of the object.

`map_reduce` method has different signatures as shown in the following examples

#### `map_reduce` where partitioner get the list of objects

```python
import pywren_ibm_cloud as pywren

iterdata = ['ibm_cos://bucket1/object1', 'ibm_cos://bucket1/object2', 'ibm_cos://bucket1/object3'] 

def my_map_function(obj):
    for line in obj.data_stream:
        # Do some process
    return partial_intersting_data

def my_reduce_function(results):
    for partial_intersting_data in results:
        # Do some process
    return final_result

chunk_size = 4*1024**2  # 4MB

pw = pywren.ibm_cf_executor()
pw.map_reduce(my_map_function, iterdata, my_reduce_function, chunk_size=chunk_size)
result = pw.get_result()
```

| method | method signature |
|---| ---| 
| `pw.map_reduce`(`my_map_function`, `iterdata`, `my_reduce_function`, `chunk_size`)| `iterdata` contains list of objects in the format of `bucket_name/object_name` |
| `my_map_function`(`obj`) | `obj` is a Python class that contains the *bucket*, *key* and *data_stream* of the object assigned to the activation|

#### `map_reduce` where partitioner gets entire bucket

Commonly, a dataset may contains hundreds or thousands of files, so the previous approach where you have to specify each object one by one is not well suited in this case. With this new **map_reduce()** method you can specify, instead, the bucket name which contains all the object of the dataset.
	
```python
import pywren_ibm_cloud as pywren

bucket_name = 'ibm_cos://my_data_bucket'

def my_map_function(obj, ibm_cos):
    for line in obj.data_stream:
        # Do some process
    return partial_intersting_data

def my_reduce_function(results):
    for partial_intersting_data in results:
        # Do some process
    return final_result

chunk_size = 4*1024**2  # 4MB

pw = pywren.ibm_cf_executor()
pw.map_reduce(my_map_function, bucket_name, my_reduce_function, chunk_size=chunk_size)
result = pw.get_result()
```

* If `chunk_size=None` then partitioner's granularity is a single object. 
	
| method | method signature |
|---| ---| 
| `pw.map_reduce`(`my_map_function`, `bucket_name`, `my_reduce_function`, `chunk_size`)| `bucket_name` contains the name of the bucket |
| `my_map_function`(`obj`, `ibm_cos`) | `obj` is a Python class that contains the *bucket*, *key* and *data_stream* of the object assigned to the activation. `ibm_cos` is an optional parameter which provides a `boto3_client` (see [here](#geting-boto3-client-from-any-map-function))|



#### `map_reduce` where partitioner gets the list of urls

```python
import pywren_ibm_cloud as pywren

iterdata = ['http://myurl/myobject1', 'http://myurl/myobject1'] 

def my_map_function(url):
    for line in url.data_stream:
        # Do some process
    return partial_intersting_data

def my_reduce_function(results):
    for partial_intersting_data in results:
        # Do some process
    return final_result

chunk_size = 4*1024**2  # 4MB

pw = pywren.ibm_cf_executor()
pw.map_reduce(my_map_function, iterdata, my_reduce_function, chunk_size=chunk_size)
result = pw.get_result()
```

| method | method signature |
|---| ---| 
| `pw.map_reduce`(`my_map_function`, `iterdata`, `my_reduce_function`, `chunk_size`)| `iterdata` contains list of objects in the format of `http://myurl/myobject.data` |
| `my_map_function`(`url`) | `url` is an object Pytnon class that contains the url *path* assigned to the activation (an entry of iterdata) and the *data_stream*|

### Reducer granularity			
By default there will be one reducer for all the objects. If you need one reducer for each object, you must set the parameter
`reducer_one_per_object=True` into the **map_reduce()** method.

```python
pw.map_reduce(my_map_function, bucket_name, my_reduce_function, 
              chunk_size=chunk_size, reducer_one_per_object=True)
```

### Geting boto3 client from any map function
Any map function can get `ibm_cos` parameter which is [boto3_client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#client). This allows you to access your IBM COS account from any map function, for example:
    
```python
import pywren_ibm_cloud as pywren

iterdata = [1, 2, 3, 4]

def my_map_function(x, ibm_cos):
    data_object = ibm_cos.get_object(Bucket='mybucket', Key='mydata.data')
    # Do some process over the object
    return x + 7

pw = pywren.ibm_cf_executor()
pw.map(my_map_function, iterdata)
result = pw.get_result()
```

## PyWren on IBM Watson Studio and Jupyter notebooks
You can use IBM-PyWren inside an **IBM Watson Studio** or Jupyter notebooks in order to execute parallel data analytics by using **IBM Cloud functions**.

### How to install PyWren within IBM Watson Studio
As the current **IBM Watson Studio** runtimes does not contains the **PyWren** package, it is needed to install it. Add these lines at the beginning of the notebook:

```python
import sys
try:
    import pywren_ibm_cloud as pywren
except:
    !{sys.executable} -m pip install pywren-ibm-cloud
    import pywren_ibm_cloud as pywren
```
Installation supports PyWren version as an input parameter, for example:

	!{sys.executable} -m pip install -U pywren-ibm-cloud==1.0.15

### Usage in notebooks
Once installed, you can use IBM-PyWren as usual inside a notebook. Don't forget of the [configuration](#configuration):

```python
import pywren_ibm_cloud as pywren

iterdata = [1, 2, 3, 4]

def my_map_function(x):
    return x + 7

pw = pywren.ibm_cf_executor()
pw.map(my_map_function, iterdata)
result = pw.get_result()
```

## Additional resources

* [Ants, serverless computing, and simplified data processing](https://developer.ibm.com/blogs/2019/01/31/ants-serverless-computing-and-simplified-data-processing/)
* [Speed up data pre-processing with PyWren in deep learning](https://developer.ibm.com/patterns/speed-up-data-pre-processing-with-pywren-in-deep-learning/)
* [Predicting the future with Monte Carlo simulations over IBM Cloud Functions](https://www.ibm.com/blogs/bluemix/2019/01/monte-carlo-simulations-with-ibm-cloud-functions/)
* [Process large data sets at massive scale with PyWren over IBM Cloud Functions](https://www.ibm.com/blogs/bluemix/2018/04/process-large-data-sets-massive-scale-pywren-ibm-cloud-functions/)
* [PyWren for IBM Cloud on CODAIT](https://developer.ibm.com/code/open/centers/codait/projects/pywren/)
* [Industrial project in Technion on PyWren-IBM](http://www.cs.technion.ac.il/~cs234313/projects_sites/W19/04/site/)
* [Serverless data analytics in the IBM Cloud](https://dl.acm.org/citation.cfm?id=3284029) - Proceedings of the 19th International Middleware Conference (Industry)