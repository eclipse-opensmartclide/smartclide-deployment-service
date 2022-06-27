#*******************************************************************************
# Copyright (C) 2021-2022 Wellness TechGroup
# 
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
# 
# SPDX-License-Identifier: EPL-2.0
#*******************************************************************************

from fastapi.responses import JSONResponse
from deployment_service.gateways.output.kubernetes_deployment import KubernetesDeploymentOutputGateway
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter

router = APIRouter()

@router.get('/metrics')
async def metrics(project):
    try:
        deployment = KubernetesDeploymentOutputGateway()
        containers_metrics = deployment.get_deployment_metrics(project)
        # json_compatible_item_data = jsonable_encoder(deployment_status)
        # return JSONResponse(content=json_compatible_item_data, status_code=200)
        return JSONResponse(content={'containers': containers_metrics}, status_code=200)
    except Exception as ex:
        return JSONResponse(content={'message': 'deployment not found'}, status_code=404)
    except:
        return JSONResponse(content={'message': 'internal server error'}, status_code=500)
