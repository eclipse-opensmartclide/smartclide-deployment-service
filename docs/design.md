## POST http://{deployment-service-addr}/deployments

### Preparing the deployment
Before we run a deployment we need a set of things to be done, the most important is clone de repository from smartclide gitlab instance so we can 
check some things a maybe make some changes 

#### Cloning project git repository
The project repository is cloned using the git python package. Authentication is done with oatuh appending the string oauth2@{repository_token} to the repository url 

#### Dockerfile file check and template generation
In order to deploy the project, a docker container must be built, so the first thing we check after repository clonation is if a Dokerfile is present in the repository. Is it's not present, a template will be generated, but the deployments will fail.
Template generation is done by checking the repository most used languaje and appending it to the Dockerfile FROM header.
Others keywords are like COPY, ADD, RUN, ENV, WORKDIR and CMD added to the file with a comment on each one explaining how are them used

#### gitlab-ci.yml file check and template generation
Before we generate this file, we check if it's already in the currnt repository. If not, the github-ci.yml is fill with the necessary steps to build a docker container un push it to the smartclide gitlab instance container registry, using the gitlab environment variables to set up registry user, password, url and the image name. Some other enviroment variables are setted, like DOCKER_HOST that it's needed by the build process

#### Changes commiting
Once all this changes has been done, all og them are commited and finally changes are pushed to remote repository, and that's how the build process starts. At the end we hace our repository image at smartclide gitlab instance docker image registry and ready to be used by kubernetes.

### Running the deployment

#### Namespaces
In Kubernetes, namespaces provides a mechanism for isolating groups of resources within a single cluster. Names of resources need to be unique within a namespace, but not across namespaces. Namespace-based scoping is applicable only for namespaced objects (e.g. Deployments, Services, etc) and not for cluster-wide objects (e.g. StorageClass, Nodes, PersistentVolumes, etc).
We create a namespace for every project. Same project are reusing it's namespace

#### Docker registry secret
A Kubernetes cluster uses the Secret of kubernetes.io/dockerconfigjson type to authenticate with a container registry to pull a private image, So we need to create one in order to pull images from smartclide gitlab docker image registry

#### Deployment 
A deployment is created using the image we already create and the port we specified in the API call. We can also specify support deployment images for the  in the gitlab-ci.yml file 

#### Service
An abstract way to expose an application running on a set of Pods as a network service. Kubernetes gives Pods their own IP addresses and a single DNS name for a set of Pods, and can load-balance across them.

## GET http://{deployment-service-addr}/deployments
List project deployments. Only the last one could be active, we make an entry in the database every time we run an new deployment and set the previous one as stopped

## GET http://{deployment-service-addr}/deployments/{id}
Get a specific deployment my its id

## DELETE http://{deployment-service-addr}/deployments/{id}
Stop a specific kubernetes deployment and sets it as stoppend in its database entry

## GET http://{deployment-service-addr}/metrics/{id}
Get the RAM and CPU usage of every container in a running deployment as well as the prices of the cloud where it is running and in the other clound in order to compare them.
