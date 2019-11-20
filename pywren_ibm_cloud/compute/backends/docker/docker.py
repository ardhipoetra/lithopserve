import os
import json
import sys
import uuid
import docker
import logging
import tempfile
from . import config as docker_config
from pywren_ibm_cloud.utils import version_str
from pywren_ibm_cloud.config import STORAGE_PREFIX_DEFAULT
from pywren_ibm_cloud.version import __version__

logger = logging.getLogger(__name__)

TEMP = tempfile.gettempdir()
STORAGE_BASE_DIR = os.path.join(TEMP, STORAGE_PREFIX_DEFAULT)
LOCAL_RUN_DIR = os.path.join(os.getcwd(), 'pywren_jobs')


class DockerBackend:
    """
    A wrap-up around Docker APIs.
    """

    def __init__(self, docker_config):
        self.log_level = os.getenv('PYWREN_LOGLEVEL')
        self.config = docker_config
        self.name = 'docker'
        self.run_dir = LOCAL_RUN_DIR

        self.workers = self.config['workers']
        self.docker_client = docker.from_env()

        log_msg = 'PyWren v{} init for Docker - Total workers: {}'.format(__version__, self.workers)
        logger.info(log_msg)
        if not self.log_level:
            print(log_msg)

    def _format_runtime_name(self, docker_image_name, runtime_memory):
        runtime_name = docker_image_name.replace('/', '_').replace(':', '_')
        return '{}_{}MB'.format(runtime_name, runtime_memory)

    def _unformat_runtime_name(self, action_name):
        runtime_name, memory = action_name.rsplit('_', 1)
        image_name = runtime_name.replace('_', '/', 1)
        image_name = image_name.replace('_', ':', -1)
        return image_name, int(memory.replace('MB', ''))

    def _get_default_runtime_image_name(self):
        this_version_str = version_str(sys.version_info)
        if this_version_str == '3.5':
            image_name = docker_config.RUNTIME_DEFAULT_35
        elif this_version_str == '3.6':
            image_name = docker_config.RUNTIME_DEFAULT_36
        elif this_version_str == '3.7':
            image_name = docker_config.RUNTIME_DEFAULT_37
        return image_name

    def _generate_runtime_meta(self, runtime_name):
        """
        Extracts installed Python modules from the local machine
        """
        runtime_meta = self.docker_client.containers.run(runtime_name, 'metadata', auto_remove=True)
        runtime_meta = json.loads(runtime_meta)

        if not runtime_meta or 'preinstalls' not in runtime_meta:
            raise Exception(runtime_meta)

        return runtime_meta

    def invoke(self, runtime_name, memory, payload):
        """
        Invoke the function with the payload. runtime_name and memory
        are not used since it runs in the local machine.
        """
        exec_id = payload['executor_id']
        job_id = payload['job_id']
        call_id = payload['call_id']

        payload_dir = os.path.join(STORAGE_BASE_DIR, exec_id, job_id, call_id)
        os.makedirs(payload_dir, exist_ok=True)
        payload_filename = os.path.join(payload_dir, 'payload.json')

        with open(payload_filename, "w") as f:
            f.write(json.dumps(payload))

        self.docker_client.containers.run(runtime_name, ['run', payload_filename],
                                          volumes=['{}:/tmp'.format(TEMP)],
                                          detach=True, auto_remove=True)

        act_id = str(uuid.uuid4()).replace('-', '')[:12]
        return act_id

    def invoke_with_result(self, runtime_name, memory, payload={}):
        """
        Invoke waiting for a result. Never called in this case
        """
        return self.invoke(runtime_name, memory, payload)

    def create_runtime(self, docker_image_name, memory, timeout):
        """
        Extracts local python metadata. No need to create any runtime
        since it runs in the local machine
        """
        if docker_image_name == 'default':
            docker_image_name = self._get_default_runtime_image_name()

        runtime_meta = self._generate_runtime_meta(docker_image_name)

        return runtime_meta

    def build_runtime(self, runtime_name, dockerfile):
        """
        Pass. No need to build any runtime since it runs in the local machine
        """
        pass

    def delete_runtime(self, runtime_name, memory):
        """
        Pass. No runtime to delete since it runs in the local machine
        """
        pass

    def delete_all_runtimes(self):
        """
        Pass. No runtimes to delete since it runs in the local machine
        """
        pass

    def list_runtimes(self, runtime_name='all'):
        """
        Pass. No runtimes to list since it runs in the local machine
        """
        pass

    def get_runtime_key(self, docker_image_name, runtime_memory):
        """
        Method that creates and returns the runtime key.
        Runtime keys are used to uniquely identify runtimes within the storage,
        in order to know what runtimes are installed and what not.
        """
        runtime_name = self._format_runtime_name(docker_image_name, runtime_memory)
        runtime_key = os.path.join(self.name, runtime_name)

        return runtime_key
