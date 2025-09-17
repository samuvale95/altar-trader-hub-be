#!/bin/bash

# Deploy script for Altar Trader Hub Backend on Kubernetes

set -e

echo "🚀 Deploying Altar Trader Hub Backend to Kubernetes..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to a Kubernetes cluster. Please connect first."
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Create namespace
echo "📁 Creating namespace..."
kubectl apply -f namespace.yaml

# Create secrets (you need to update these with real values)
echo "🔐 Creating secrets..."
kubectl apply -f secret.yaml

# Create configmap
echo "⚙️ Creating configmap..."
kubectl apply -f configmap.yaml

# Deploy PostgreSQL
echo "🐘 Deploying PostgreSQL..."
kubectl apply -f postgres.yaml

# Deploy Redis
echo "🔴 Deploying Redis..."
kubectl apply -f redis.yaml

# Deploy application
echo "🚀 Deploying application..."
kubectl apply -f deployment.yaml

# Create services
echo "🌐 Creating services..."
kubectl apply -f service.yaml

# Create ingress
echo "🔗 Creating ingress..."
kubectl apply -f ingress.yaml

# Deploy monitoring
echo "📊 Deploying monitoring..."
kubectl apply -f monitoring.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/altar-trader-hub-api -n altar-trader-hub
kubectl wait --for=condition=available --timeout=300s deployment/altar-trader-hub-celery-worker -n altar-trader-hub
kubectl wait --for=condition=available --timeout=300s deployment/altar-trader-hub-celery-beat -n altar-trader-hub

# Run database migrations
echo "🗄️ Running database migrations..."
kubectl run migration-job --image=altar-trader-hub-be:latest --rm -i --restart=Never -n altar-trader-hub -- python migrate.py upgrade

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  - Namespace: altar-trader-hub"
echo "  - API Service: altar-trader-hub-api-service"
echo "  - Celery Workers: altar-trader-hub-celery-worker"
echo "  - Celery Beat: altar-trader-hub-celery-beat"
echo ""
echo "🔍 To check the status:"
echo "  kubectl get pods -n altar-trader-hub"
echo "  kubectl get services -n altar-trader-hub"
echo "  kubectl get ingress -n altar-trader-hub"
echo ""
echo "📊 To view logs:"
echo "  kubectl logs -f deployment/altar-trader-hub-api -n altar-trader-hub"
echo "  kubectl logs -f deployment/altar-trader-hub-celery-worker -n altar-trader-hub"
