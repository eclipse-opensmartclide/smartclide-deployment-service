from kubernetes.dynamic.exceptions import NotFoundError, ApiException
from urllib3.exceptions import MaxRetryError
from fastapi import APIRouter, Query, Header
from typing import Optional
import json
from fastapi.responses import JSONResponse
from deployment_service.gateways.output.deploy.kubernetes import KubernetesDeploymentOutputGateway
from deployment_service.repositories.mongo.deployment import MongoDeploymentRepository
from deployment_service.use_cases.deployments import create_or_update_deployment, get_deployments_list, prepare_deployment
from deployment_service.models.deployment import Deployment
from deployment_service.config.settings import Settings

settings = Settings()
router = APIRouter()
mongo_repo = MongoDeploymentRepository()

@router.get('/deployments/')
async def list_deployments(user: str, project: str, skip: int = 0, limit: int = 10):

    try:
        deployments = mongo_repo.list_deployments(user, project, skip, limit)
        if not deployments:
            return JSONResponse(content={'message': 'Deployments not found'}, status_code=404)
        else:
            return JSONResponse(content=deployments, status_code=200)
    
    except Exception as ex:
        import traceback; traceback.print_exc()
        return JSONResponse(content={'message': f'Internal server error: {ex}'}, status_code=500)


@router.get('/deployments/{id}')
async def read_deployment(id: str, k8s_token: str = Header(None)):

    try:    
        deployment = mongo_repo.show_deployment(id)
        if deployment:
            # import pdb; pdb.set_trace()
            kubernetes_gw = KubernetesDeploymentOutputGateway(deployment['k8s_url'], k8s_token, '')
            status = kubernetes_gw.deployment_status(deployment['project'])

            # if not status:
            #     return JSONResponse(content={'message': 'Deployment not running'}, status_code=404)
            # else:
            return JSONResponse(content=deployment, status_code=200)
        else: return JSONResponse(content={'message': 'deployment not found'}, status_code=404)
    except Exception as ex:
        import traceback; traceback.print_exc()
        return JSONResponse(content={'message': f'Internal server error: {ex}'}, status_code=500)


    
@router.post('/deployments/')
async def run_deployment(
    username: str,
    repository_url: str,
    repository_name: str,
    k8s_url: str,
    container_port: int,
    k8s_token: str = Header(None), 
    gitlab_token: str = Header(None),
    branch: Optional[str] = 'master',
    replicas: Optional[int] = 1):
    
    try:
        gitlab_ci_path = prepare_deployment(repository_url, gitlab_token, branch)
        if gitlab_ci_path:
            result = create_or_update_deployment(k8s_url, k8s_token, repository_name, username, container_port, replicas, gitlab_ci_path)
        else: 
            return JSONResponse(content ={'message': 'Can not deploy'}, status_code = 404 ) 
        if result:
            if isinstance(result, ApiException):
                return JSONResponse(content={'message': json.loads(result.body)['message']}, status_code=result.status)
            else:
                return JSONResponse(content = result,status_code = 200 )
        # else:
        #     return JSONResponse(content={'message': 'Deployment already running'}, status_code=409)

    except Exception as ex:
        import traceback; traceback.print_exc()
        return JSONResponse(content={'message': f'Internal server error: {ex}'},status_code=500)


@router.delete('/deployments/{id}')
async def delete_deployment(id: str, k8s_token: str = Header(None)):

    try:
        deployment = mongo_repo.show_deployment(id)
        kubernetes_gw = KubernetesDeploymentOutputGateway(deployment['k8s_url'], k8s_token, '')
        stopped_deployment = mongo_repo.set_deployment_stopped(id)
        result = kubernetes_gw.stop(deployment['project'])
        if result:
            return JSONResponse(content=stopped_deployment.to_dict(), status_code=200)
        else:
            return JSONResponse(content={'message': 'Deployment not running'}, status_code=404)    
    except (NotFoundError, ApiException):
        return JSONResponse(content={'message': 'Deployment not found'}, status_code=404)
    except MaxRetryError:
        return JSONResponse(content={'message': 'Max retries'}, status_code=500)
    except Exception as ex:
        import traceback; traceback.print_exc()
        return JSONResponse(content={'message': f'Internal server error: {ex}'}, status_code=500)
