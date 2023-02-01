# SmartCLIDE deployment service
## Prerequisites
Gitlab instance hosted repo and access token, since we use gitlab-ci to build Docker images

Running Kubernetes instance and an access bearer (see below), becouse we use a kubernetes cluster to deploy docker images from a docker registry

### Create kubernetes user and get your bearer
``` bash
# Create user
kubectl create serviceaccount k8sadmin -n kube-system
# Create role 
kubectl create clusterrolebinding k8sadmin --clusterrole=cluster-admin --serviceaccount=kube-system:k8sadmin
# Create and print secret
kubectl -n kube-system describe secret $(sudo kubectl -n kube-system get secret | (grep k8sadmin || echo "$_") | awk '{print $1}') | grep token: | awk '{print $2}'
# Print k8 url
```kubectl config view | grep server | cut -f 2- -d ":" | tr -d " "
```


## HOW TO DEPLOY
### Clone this repository and run 
``` bash 
docker-compose up -d 
```

## API documentantion 
[http://localhost:3000/docs/](http://localhost:3000/docs/)

## TODO
- Change mongo repository to smartclide HTTP API-based database
- More tests
- Improve code quality
- More tests