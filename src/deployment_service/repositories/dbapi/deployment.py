from deployment_service.models.deployment import Deployment
from deployment_service.config.settings import Settings
from deployment_service.exceptions import DeploymentServiceException
from datetime import datetime
import requests
import json

class DBAPIDeploymentRepository(object):
    def __init__(self):
        self.settings = Settings()
        self.url = self.settings.repositories['dbapi']['url']
        self.token = self.settings.repositories['dbapi']['token']
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _create_deployment_obj(self, deployment: dict) -> Deployment:
        return Deployment(
            id=str(deployment['id']),
            user=deployment['user'],
            project=deployment['project'],
            service_url=deployment['service_url'],
            port=deployment['port'],
            replicas=deployment['replicas'],
            state=deployment['state'],
            k8s_url=deployment['k8s_url'],
            created_at=deployment['created_at'],
            stopped_at=deployment['stopped_at'], 
            workflow_id=deployment['workflow_id'],
            user_id=deployment['user_id'], 
            service_id=deployment['service_id'],
            git_credentials_id=deployment['git_credentials_id'] if deployment['git_credentials_id'] else 'No git credentials id were supplied', 
            name=deployment['project']
        )

    def create_or_update_deployment(self, deployment: dict) -> bool:
        try:
            service_fields = self._get_service_fields(deployment['service_id'])
            deployment.update(service_fields)
            deployment_obj =  self._create_deployment_obj(deployment)
            response = requests.post(self.url, json=json.dumps(deployment_obj.to_dict()), headers=self.headers)
            if response.status_code == 200: return deployment_obj
            else: return response

        except Exception as ex:
            print('{}: Failed to update or create deployment'.format(ex))
            return False

    def _get_service_fields(self, service_id):
        services_url = self.url.replace('deployments', 'services')
        response = requests.get(f"{services_url}/{service_id}", headers=self.headers)

        return {
            'service_id': response.json()['id'], 
            'workflow_id': response.json()['workspace_id'], 
            'git_credentials_id': response.json()['git_credentials_id'],
            'user_id': response.json()['user_id']
        }

    def create_deployment_objects(self, results: list) -> list:
        return [self._create_deployment_obj(q).to_dict() for q in results]


    def list_deployments(self, user, project, skip: int = 0, limit: int=20) -> list:
        filters = {'user': user, 'project': project}
        try:
            deployments = requests.get(self.url, params=filters, headers=self.headers)
            if deployments.status_code == 200:
                deployments = deployments.json()[skip:(skip+limit)]

                return {
                    'data': self.create_deployment_objects(deployments),
                    'count': len(deployments)
                }
            else:
                return deployments.status_code
        except:
            import traceback; traceback.print_exc()

    def show_deployment(self, id):
        try:
            deployment = requests.get(f"{self.url}/{id}", headers=self.headers)
            if deployment.status_code != 200: 
                raise Exception(f"Failed to get deployment with status code {deployment.status_code}")
            if len(deployment.json()) == 0:
                return []
            else:
                return self._create_deployment_obj(deployment.json()).to_dict()
        except Exception as ex:
            import traceback; traceback.print_exc()
            raise Exception(ex)
            
    def set_deployment_stopped(self, id):
        try:
            deployments = requests.get(f"{self.url}/{id}", headers=self.headers)
            if len(deployments.json()):
                deployment = self.create_deployment_objects(deployments)
                deployment['status'] = 'stopped'
                deployment['stopped_at'] = datetime.now().isoformat()
                stopped_deployment = self.create_or_update_deployment(deployment)
                return stopped_deployment
        except:
            import traceback; traceback.print_exc()