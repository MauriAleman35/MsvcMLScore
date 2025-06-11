#!/bin/bash
set -e

# Construir la imagen Docker
echo "Construyendo imagen Docker..."
docker build -t moisodev/ml-scoring:latest -f Dockerfile-ML .

# Subir la imagen a Docker Hub
echo "Subiendo imagen a Docker Hub..."
docker push moisodev/ml-scoring:latest

# Aplicar manifiestos de Kubernetes
echo "Aplicando manifiestos de Kubernetes..."
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f rabbitmq.yaml
# kubectl apply -f postgres.yaml
kubectl apply -f ml-api.yaml
kubectl apply -f ml-consumer.yaml

# Esperar a que los pods estén listos
echo "Esperando a que los pods estén listos..."
kubectl wait --namespace credit-scoring --for=condition=ready pod --selector=app=rabbitmq --timeout=120s
# kubectl wait --namespace credit-scoring --for=condition=ready pod --selector=app=postgres --timeout=120s
kubectl wait --namespace credit-scoring --for=condition=ready pod --selector=app=ml-api --timeout=120s
kubectl wait --namespace credit-scoring --for=condition=ready pod --selector=app=ml-consumer --timeout=120s

# Mostrar servicios
echo "Servicios desplegados:"
kubectl get services -n credit-scoring

# Obtener la URL de la API
echo "URL de la API GraphQL:"
kubectl get service ml-api -n credit-scoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo " (si estás usando minikube, ejecuta 'minikube service ml-api -n credit-scoring')"