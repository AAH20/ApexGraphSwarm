"""Example 48: Deployment - Kubernetes configuration.

Example Kubernetes deployment for ApexGraphSwarm.
"""
# Kubernetes deployment manifest
K8S_DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apexgraphswarm
  labels:
    app: apexgraphswarm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: apexgraphswarm
  template:
    metadata:
      labels:
        app: apexgraphswarm
    spec:
      containers:
      - name: apexgraphswarm
        image: apexgraphswarm:latest
        ports:
        - containerPort: 3010
        env:
        - name: APEX_CONTROL_DB
          value: /data/control.sqlite
        - name: APEX_MAX_ACTIVE
          value: "16"
        - name: APEX_MAX_AGENTS
          value: "100"
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - python3
            - -c
            - from apexgraphswarm.control import ControlStore; s = ControlStore('/data/control.sqlite'); s.close()
          initialDelaySeconds: 10
          periodSeconds: 30
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: apexgraphswarm-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: apexgraphswarm-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: apexgraphswarm
spec:
  selector:
    app: apexgraphswarm
  ports:
  - port: 80
    targetPort: 3010
  type: ClusterIP
"""

print("Kubernetes manifests:")
print(K8S_DEPLOYMENT)
print("\nTo deploy:")
print("  kubectl apply -f deployment.yaml")
print("  kubectl get pods -l app=apexgraphswarm")
print("  kubectl logs -f deployment/apexgraphswarm")
