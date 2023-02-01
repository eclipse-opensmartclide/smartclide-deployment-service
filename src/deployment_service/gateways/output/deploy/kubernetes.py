from datetime import datetime
import yaml
import time
from kubernetes import client, dynamic
from kubernetes.client.exceptions import ApiException
from deployment_service.config.logging import logger as l
from deployment_service.config.settings import Settings
from deployment_service.gateways.input.pricing.provider import KubernetesPricingProvider

class KubernetesDeploymentOutputGateway(object):
    def __init__(self, url, token, gitlab_ci_path):
        self.settings = Settings()
        self.glci_path = gitlab_ci_path
        aToken = token
        self.aConfiguration = client.Configuration()
        self.aConfiguration.host = url
        self.aConfiguration.verify_ssl = False
        self.aConfiguration.api_key = {"authorization": "Bearer " + aToken}

        # config.load_config()
        self.aApiClient = client.ApiClient(self.aConfiguration)
        self.apps_v1_api = client.AppsV1Api(self.aApiClient)
        self.networking_v1_api = client.NetworkingV1Api()
        
    def run(self, name, image, port, replicas):
        try:
            self.create_namespace(name.replace('_', '-'))
            self.create_docker_registry_secret(name.replace('_', '-'))
            deployment = self.create_deployment(name, image, port, replicas)
            lb_ip = self.create_service(name.replace('_', '-'), port)
            return lb_ip

        except Exception as d_ex:
            import traceback; traceback.print_exc()
            l.error('{}: Failed to deploy.'.format(d_ex))
            return d_ex
        

    def stop(self, name):
        name = name.replace('_', '-')
        try:
            self.delete_deployment(name)
            self.delete_service(name)
            return True

        except Exception as d_ex:
            import traceback; traceback.print_exc()
            l.error('{}: Failed to stop deployment.'.format(d_ex))
            return False


    def _get_container_obj(self, image, name, port = None):
        return client.V1Container(
                name=name,
                image=image,
                ports=[client.V1ContainerPort(container_port=port)] if port else [],
            )

    def _get_deployment_support_containers(self):
        with open(self.glci_path, "r") as stream:
            try:
                f_content = yaml.safe_load(stream)
                services = list(filter(lambda x: 'name' in x, f_content['services']))
                return list(map(lambda s: self._get_container_obj(s['name'], s['name'].split(':')[0]), services))

            except yaml.YAMLError as ex:
                l.error('Failed to parse .gitlab-ci.yaml file {}'.format(ex))
                import traceback; traceback.print_exc()

    def create_deployment(self, name, image, port, replicas):
        try:
            image__ = 'registry.dev.smartclide.eu/{}'.format(image)
            name = name.replace('_', '-')

            # Container
            main_container = self._get_container_obj(image__, name, port)
            support_containers = self._get_deployment_support_containers()
            containers = [main_container] + support_containers

            # Template
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": name}),
                spec=client.V1PodSpec(containers=containers, image_pull_secrets=[{'name': 'smartclidedockerregcred'}]),
            )

            # Spec
            spec = client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": name}
                ),
                template=template
            )

            # Deployment
            deployment_body = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=name),
                spec=spec
            )

            deployment = self.apps_v1_api.create_namespaced_deployment(
                namespace=name, 
                body=deployment_body
            )
            return deployment

        except Exception as d_ex:
            l.error('Failed to crete deployment: {}'.format(d_ex))
            import traceback; traceback.print_exc()

    def create_service(self, name, port):
        api_client = client.api_client.ApiClient(self.aConfiguration)
        core_v1_api = client.CoreV1Api(api_client)
        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=name
            ),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[client.V1ServicePort(
                    port=port,
                    target_port=port
                )], 
                # https://faun.pub/application-deployment-on-azure-kubernetes-service-aks-exposing-a-service-and-deploying-523ebae407bc
                type='LoadBalancer'
            )
        )
        result = core_v1_api.create_namespaced_service(namespace=name.replace('_', '-'), body=body)

        time.sleep(5)

        while True and result:
            service = core_v1_api.read_namespaced_service(name=name, namespace=name.replace('_', '-'))
            if service.status.load_balancer.ingress:
                load_balancer_ip = service.status.load_balancer.ingress[0].ip if len(service.status.load_balancer.ingress) > 0 else None
                if load_balancer_ip: return load_balancer_ip
            else: time.sleep(5)


    def create_namespace(self, name):
        try:
            client = dynamic.DynamicClient(self.aApiClient)
            namespace_api = client.resources.get(api_version="v1", kind="Namespace")
            namespace_manifest = {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": name, 
                    "resourceversion": "v1"
                },
            }
            namespace_api.create(body=namespace_manifest)
        except:
            pass

    def delete_deployment(self, name):
        client = dynamic.DynamicClient(self.aApiClient)
        api = client.resources.get(api_version="v1", kind="Deployment")
        service_deleted = api.delete(name=name, body={}, namespace=name)
        return service_deleted
        
    def delete_service(self, name):
        client = dynamic.DynamicClient(self.aApiClient)
        api = client.resources.get(api_version="v1", kind="Service")
        service_deleted = api.delete(name=name, body={}, namespace=name)
        return service_deleted

    def delete_ingress(self, name):
        client = dynamic.DynamicClient(self.aApiClient)
        api = client.resources.get(api_version="v1", kind="Ingress")
        ingress_deleted = api.delete(name=name, body={}, namespace=name)
        return ingress_deleted

    def deployment_status(self, name):
        try:
            client = dynamic.DynamicClient(self.aApiClient)
            api = client.resources.get(api_version="v1", kind="Deployment")
            deployment = api.get(name=name, namespace=name)
            return deployment.status
        except ApiException as ex:
            pass

    def list_deployments(self):
        conf = client.configuration.Configuration()
        with client.ApiClient(self.aApiClient) as api_client:
            api_instance = client.AppsV1Api(self.aApiClient)
            allow_watch_bookmarks = True 
            _continue = '_continue_example' 
            field_selector = 'field_selector_example' 
            label_selector = 'label_selector_example' 
            limit = 56 
            pretty = 'pretty_example' 
            resource_version = 'resource_version_example' 
            resource_version_match = 'resource_version_match_example'
            timeout_seconds = 56
            watch = True
        
        try:
            api_response = api_instance.list_deployment_for_all_namespaces(
                allow_watch_bookmarks=allow_watch_bookmarks, 
                _continue=_continue, 
                field_selector=field_selector, 
                label_selector=label_selector, 
                limit=limit, pretty=pretty, 
                resource_version=resource_version, 
                resource_version_match=resource_version_match, 
                timeout_seconds=timeout_seconds, 
                watch=False)

            l.debug(api_response)
        
        except ApiException as e:
            l.error("Exception when calling AppsV1Api->list_deployment_for_all_namespaces: %s\n" % e)
            import traceback; traceback.print_exc()

    def get_deployment_metrics(self, name, url):
        try:
            api_client = client.ApiClient(self.aConfiguration)
            api = client.CustomObjectsApi(api_client)
            k8s_nodes = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods")
            for stats in k8s_nodes['items']:
                if name in stats['metadata']['namespace']:
                    pricing_provider = KubernetesPricingProvider(url)
                    prices = pricing_provider.get_prices()
                    date_format_str = '%Y-%m-%dT%H:%M:%SZ'
                    datetime.strptime(stats['metadata']['creationTimestamp'], date_format_str)
                    start = datetime.strptime(stats['metadata']['creationTimestamp'], date_format_str)
                    diff = datetime.now() - start
                    diff_h = diff.total_seconds() / 3600
                    
                    output = {
                        'containers': stats['containers'],
                        "price": { 
                            "current_provider":"",
                            "competitor_provider":[]
                        }
                    }

                    for price in prices:

                        if price['current']:
                            output["price"]['current_provider'] = {
                                'name': price['name'],
                                'price': price['cost'] * diff_h,
                                "cost_type": price['cost_type']
                            }

                        else:
                            output["price"]['competitor_provider'].append({
                                'name': price['name'],
                                'price': price['cost'] * diff_h,
                                "cost_type": price['cost_type']
                            })

                    return output

        except Exception as m_ex:
            l.error('Failed to obtain deployment metrics: {}'.format(m_ex))
            import traceback;traceback.print_exc()

    def create_docker_registry_secret(self, namespace):
        # https://juju.is/tutorials/using-gitlab-as-a-container-registry#7-pull-your-container
        # https://github.com/kubernetes-client/python/blob/1ad6e80f29369651e17a6ba767ddccc99f46600b/kubernetes/docs/V1PodSpec.md
        # https://kubernetes.io/docs/concepts/configuration/secret/#secret-types
        # https://stackoverflow.com/questions/46763148/how-to-create-secrets-using-kubernetes-python-client
        # kubectl create -n mynamespace secret docker-registry dockerhubpull --dry-run=true --docker-username=myuser --docker-server=docker.io --docker-email=myemail@domain.com   --docker-password=mypass  -o yaml
        try:
            api_client = client.api_client.ApiClient(self.aConfiguration)
            v1 = client.CoreV1Api(api_client)
            data = {'.dockerconfigjson': 'eyJhdXRocyI6eyJyZWdpc3RyeS5kZXYuc21hcnRjbGlkZS5ldSI6eyJ1c2VybmFtZSI6InBiZXJyb2NhbCIsInBhc3N3b3JkIjoib0VGQjgybXR6d3c1UzctSkEybjkiLCJlbWFpbCI6InBiZXJyb2NhbEB3ZWxsbmVzc3RnLmNvbSIsImF1dGgiOiJjR0psY25KdlkyRnNPbTlGUmtJNE1tMTBlbmQzTlZNM0xVcEJNbTQ1In19fQ=='}
            metadata = {'name': 'smartclidedockerregcred', 'namespace': namespace}
            body = client.V1Secret('v1', data , None, 'Secret', metadata, type='kubernetes.io/dockerconfigjson')
            # import pdb; pdb.set_trace()
            ret = v1.create_namespaced_secret(namespace, body)
            return ret

        except Exception as ex:
            if '409' in str(ex): pass
            else:
                l.error('Failed to create docker registry secret: {}'.format(ex))
                import traceback; traceback.print_exc()
