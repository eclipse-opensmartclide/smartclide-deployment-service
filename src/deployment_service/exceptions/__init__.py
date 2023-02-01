import sys, os
from deployment_service.config.logging import logger

class DeploymentServiceException(Exception):
    def __init__(self, message):            
        super().__init__(message)
        logger.error(message)