#
# (C) Copyright Cloudlab URV 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os

DEFAULT_CONFIG_KEYS = {
    'runtime_timeout': 600,  # Default: 10 minutes
    'runtime_memory': 512,  # Default memory: 512 MB
    'runtime_cpu': 1,  # 1 vCPU
    'max_workers': 100,
    'worker_processes': 1,
    'docker_server': 'docker.io'
}

# mig 09may2024 - Patch by Miguel @ SCONTAIN. New SCONE related configuration
SCONE_CONFIG_KEYS = {
    'scone_master_requests_cpu': '0.1',
    'scone_master_requests_memory': '384Mi',
    'scone_master_limits_cpu': '2',
    'scone_master_limits_memory': '2048Mi',
    'scone_master_limits_sgx': '1',
    'scone_master_heap'            : '256M',
    'scone_master_mode'            : 'AUTO',
    'scone_master_allow_dl_open'   : '0',
    'scone_master_fork'            : '0',
    'scone_master_syslibs'         : '0',
    'scone_worker_requests_cpu': '0.1',
    'scone_worker_requests_memory': '768Mi',
    'scone_worker_limits_cpu': '2',
    'scone_worker_limits_memory': '2048Mi',
    'scone_worker_limits_sgx': '1',
    'scone_worker_heap'            : '512M',
    'scone_worker_mode'            : 'AUTO',
    'scone_worker_allow_dl_open'   : '0',
    'scone_worker_fork'            : '0',
    'scone_worker_syslibs'         : '0',
    'scone_cas_addr'        : '172.20.0.1',
    'scone_las_addr'        : '172.20.0.1',
    'scone_config_id'       : '',
    'k8s_master_ip'   : '0.0.0.0'
}

DEFAULT_GROUP = "batch"
DEFAULT_VERSION = "v1"
MASTER_NAME = "lithops-master"
MASTER_PORT = 8080

FH_ZIP_LOCATION = os.path.join(os.getcwd(), 'lithops_k8s.zip')


DOCKERFILE_DEFAULT = """
RUN apt-get update && apt-get install -y \
        zip redis-server curl \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade --ignore-installed setuptools six pip \
    && pip install --upgrade --no-cache-dir --ignore-installed \
        flask \
        pika \
        boto3 \
        ibm-cloud-sdk-core \
        ibm-cos-sdk \
        redis \
        requests \
        PyYAML \
        kubernetes \
        numpy \
        cloudpickle \
        ps-mem \
        tblib

ENV PYTHONUNBUFFERED TRUE

# Copy Lithops proxy and lib to the container image.
ENV APP_HOME /lithops
WORKDIR $APP_HOME

COPY lithops_k8s.zip .
RUN unzip lithops_k8s.zip && rm lithops_k8s.zip
"""

JOB_DEFAULT = """
apiVersion: batch/v1
kind: Job
metadata:
  name: lithops-worker-name
  namespace: default
  labels:
    type: lithops-worker
    version: lithops_vX.X.X
    user: lithops-user
spec:
  # mig 14apr2024 - Patch by Miguel @ SCONTAIN. Doubling the timeouts
  activeDeadlineSeconds: 1200
  ttlSecondsAfterFinished: 120
  parallelism: 1
  # mig 14apr2024 - Patch by Miguel @ SCONTAIN. Rerun if failed at most 6 times
  backoffLimit: 6
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: "lithops"
          image: "<INPUT>"
          # imagePullPolicy: IfNotPresent
          command: ["python3"]
          args:
            - "/lithops/lithopsentry.py"
            - "$(ACTION)"
            - "$(DATA)"
          env:
            - name: ACTION
              value: ''
            - name: DATA
              value: ''
            - name: MASTER_POD_IP
              value: ''
            - name: POD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
              # mig 14apr2024 - Patch by Miguel @ SCONTAIN. SCONE related variables
            - name: SCONE_HEAP
              value: '768M'
            - name: SCONE_MODE
              value: 'AUTO'
            - name: SCONE_ALLOW_DLOPEN
              value: '2'
            - name: SCONE_FORK
              value: '1'
            - name: SCONE_SYSLIBS
              value: '1'
            - name: SCONE_CAS_ADDR
              value: '172.20.0.1'
            - name: SCONE_LAS_ADDR
              value: '172.20.0.1'
            # - name: SCONE_CONFIG_ID_TEST
            #   value: 'Lithops-Benchmark-D41-123-45678-90120/benchmark'
          resources:
            # mig 14apr2024 - Patch by Miguel @ SCONTAIN. Increased initial memory and cpu and memory limits
              requests:
                cpu: '1'
                memory: 4096Mi
              limits:
                cpu: '8'
                memory: 8192Mi
                sgx.k8s.io/sgx: "1"
          securityContext:
            capabilities:
              add: ["SYS_RAWIO"]
      imagePullSecrets:
        - name: lithops-regcred
"""

POD = """
apiVersion: v1
kind: Pod
metadata:
  name: lithops-worker
spec:
  containers:
    - name: "lithops-worker"
      image: "<INPUT>"
      command: ["python3"]
      args:
        - "/lithops/lithopsentry.py"
        - "--"
        - "--"
      resources:
        requests:
          cpu: '1'
          memory: '512Mi'
"""

MASTER_CONFIG_RESOURCES = {
    'requests': {'cpu': '0.5', 'memory': '2096Mi'},
    'limits': {'cpu': '1', 'memory': '8292Mi'}
}

def load_config(config_data):
    for key in DEFAULT_CONFIG_KEYS:
        if key not in config_data['k8s']:
            config_data['k8s'][key] = DEFAULT_CONFIG_KEYS[key]

    if 'runtime' in config_data['k8s']:
        runtime = config_data['k8s']['runtime']
        registry = config_data['k8s']['docker_server']
        if runtime.count('/') == 1 and registry not in runtime:
            config_data['k8s']['runtime'] = f'{registry}/{runtime}'

    # mig 09may2024 - Patch by Miguel @ SCONTAIN. New SCONE related configuration
    for key in SCONE_CONFIG_KEYS:
        if key not in config_data['k8s']:
            config_data['k8s'][key] = SCONE_CONFIG_KEYS[key]

