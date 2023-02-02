from abc import ABCMeta
from pydantic.dataclasses import dataclass
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from gitlab.v4.objects import deployments
from deployment_service.models.service import Service
from deployment_service.models.provider import Provider
from typing import List
import uuid

@dataclass
class Deployment():
    id: str
    user: str
    project: str
    service_url: str
    port: int
    # provider: Provider
    # services: List[Service]
    replicas: int
    state: str
    name: str
    k8s_url: str
    created_at: datetime
    stopped_at: datetime
    workflow_id: Optional[str] = ''
    user_id: Optional[str] = ''
    service_id: Optional[str] = ''
    git_credentials_id: Optional[str] = ''


    @classmethod
    def from_dict(self, d):
        return self(**d)

    def to_dict(self):
        return asdict(self)


# {
#     "id": "637f238e2aa7a54df9aa6e2f",
#     "user_id": "628c87f6aa5a2857398a80a0",
#     "user": null,
#     "git_credentials_id": "628c922780b42501489a85dd",
#     "name": "Test service",
#     "project": null,
#     "service_url": null,
#     "k8s_url": null,
#     "port": null,
#     "replicas": null,
#     "workflow_id": "6283ac19189ff14b1516c11c",
#     "service_id": "628c928d80b42501489a85de",
#     "version": "$deployment_version",
#     "state": "$deployment_state",
#     "created_at": null,
#     "updated_at": null,
#     "stopped_at": null
#   }