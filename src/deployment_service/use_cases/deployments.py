from os.path import exists
import uuid
from datetime import datetime
from deployment_service.gateways.output.mom.amqp import MOMAMQPOutputGateway
from deployment_service.repositories.mongo.deployment import MongoDeploymentRepository
from deployment_service.gateways.output.deploy.kubernetes import KubernetesDeploymentOutputGateway
from deployment_service.gateways.input.git.git_input import GitInputGateway
from deployment_service.gateways.input.dockerfile.sheet import DockerfileSheet
from deployment_service.config.settings import Settings

settings = Settings()

def get_deployments_list(gateway):
    return gateway.list_deployments()

def create_or_update_deployment(k8s_url, k8s_token, name, username, container_port, replicas):   
    k_gw = KubernetesDeploymentOutputGateway(k8s_url, k8s_token) 
    deployment_result = k_gw.run(
            name=name, 
            image=f'{username}/{name}', 
            replicas=int(replicas),
            port=container_port
        )
    if hasattr(deployment_result, 'body'):
        return deployment_result

    if deployment_result:
        repo = MongoDeploymentRepository()
        id = str(uuid.uuid4())
        deployment = repo.create_or_update_deployment(
            {
                'id': id,
                'user': username,
                'project': name,
                'port': container_port,
                'hostname': '',
                'replicas': replicas,
                'status': 'active',
                'k8s_url': k8s_url,
                'created_at': datetime.now().isoformat(),
                'stopped_at': ''
            }
        )
        if deployment:
            mom_gw = MOMAMQPOutputGateway()
            ret = mom_gw.send_deployment_is_running(name, id)
            if ret: return deployment.to_dict()

def clone_repository(url):
    g_gw = GitInputGateway()
    return g_gw.clone_repo(url)

def check_dockerfile_exists(repo_path):
    f_path = f'{repo_path}/Dockerfile'
    return exists(f_path)

def generate_dockerfile(url, cloned_repo_path):
    d_gw = DockerfileSheet(url)
    return d_gw.run(cloned_repo_path)

def check_gitlab_ci_file_exists(repo_path):
    f_path = f'{repo_path}/.gitlab-ci.yml'
    return exists(f_path)

def generate_gitlab_ci_file(repo_path):
    g_gw = GitInputGateway()
    g_gw.write_cdci_file(repo_path)

def prepare_deployment(repository_url, user, repository_name):
    repository_path = clone_repository(repository_url)

    if not check_dockerfile_exists(repository_path): 
        generate_dockerfile(repository_path)
        return False

    if not check_gitlab_ci_file_exists(repository_path): 
        generate_gitlab_ci_file(repository_path)

    g_gw = GitInputGateway()
    g_gw.commit_changes(repository_name)
    result = g_gw.push_repository(repository_path)

    return result

