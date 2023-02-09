from os.path import exists
import uuid
from kubernetes.dynamic.exceptions import NotFoundError, ApiException
from datetime import datetime
from deployment_service.gateways.output.mom.amqp import MOMAMQPOutputGateway
from deployment_service.repositories.mongo.deployment import MongoDeploymentRepository
from deployment_service.repositories.dbapi.deployment import DBAPIDeploymentRepository
from deployment_service.gateways.output.deploy.kubernetes import KubernetesDeploymentOutputGateway
from deployment_service.gateways.input.git.git_input import GitInputGateway
from deployment_service.gateways.input.dockerfile.sheet import DockerfileSheet
from deployment_service.config.settings import Settings
from deployment_service.config.logging import logger as l

settings = Settings()

def get_deployments_list(gateway):
    return gateway.list_deployments()

def create_or_update_deployment(k8s_url, k8s_token, name, username, container_port, replicas, gitlab_ci_path, service_id):  
    k_gw = KubernetesDeploymentOutputGateway(k8s_url, k8s_token, gitlab_ci_path) 
    deployment_result = k_gw.run(
            name=name, 
            image=f'{username}/{name}', 
            replicas=int(replicas),
            port=container_port
        )


    # if hasattr(deployment_result, 'body'):
    #     return deployment_result
    if isinstance(deployment_result, ApiException):
        return deployment_result
        
    if deployment_result:
        repo = MongoDeploymentRepository()
        repo = DBAPIDeploymentRepository()
        id = str(uuid.uuid4())
        deployment = repo.create_or_update_deployment(
            {
                'id': id,
                'user': username,
                'project': name,
                'port': container_port,
                'service_url': 'http://{}:{}'.format(deployment_result, container_port),
                'replicas': replicas,
                'state': 'active',
                'k8s_url': k8s_url,
                'created_at': datetime.now().isoformat(),
                'stopped_at': '',
                'service_id': service_id
            }
        )

        if  deployment and settings.mom['host'] and settings.mom['port']:             
            mom_gw = MOMAMQPOutputGateway()
            ret = mom_gw.send_deployment_is_running(name, id)
            if not ret:
                l.error('Failed to notify to MOM')
            
            return deployment
        
        else: 
            raise Exception('Failed to create or update deployment')

def clone_repository(url, branch):
    g_gw = GitInputGateway()
    return g_gw.clone_repo(url, branch)

def check_dockerfile_exists(repo_path):
    f_path = f'{repo_path}/Dockerfile'
    return exists(f_path)

def generate_dockerfile(url, cloned_repo_path, token):
    d_gw = DockerfileSheet(url, token)
    return d_gw.run(cloned_repo_path)

def check_gitlab_ci_file_exists(repo_path):
    f_path = f'{repo_path}/.gitlab-ci.yml'
    return exists(f_path)

def generate_gitlab_ci_file(repo_path):
    g_gw = GitInputGateway()
    g_gw.write_cdci_file(repo_path)

def prepare_deployment(repository_url, repository_token, branch):
    url_parts = repository_url.split('//')
    auth_url_parts = []
    auth_url_parts.append('https://oauth2:{}@'.format(repository_token))
    auth_url_parts.append(url_parts[1])
    auth_url = ''.join(auth_url_parts)

    repository_path = clone_repository(auth_url, branch)
    # if not repository_path:
    if not check_dockerfile_exists(repository_path): 
        generate_dockerfile(repository_url, repository_path, repository_token)
        return False

    if not check_gitlab_ci_file_exists(repository_path): 
        generate_gitlab_ci_file(repository_path)

    g_gw = GitInputGateway()
    g_gw.commit_changes(repository_path)
    result = g_gw.push_repository(repository_path)
    if result:
        gl_ci_path = '{}/.gitlab-ci.yml'.format(repository_path)
        return gl_ci_path
