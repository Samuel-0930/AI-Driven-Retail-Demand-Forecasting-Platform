FROM grafana/grafana:latest

# Copy dashboard provisioning config
COPY provisioning/dashboards/dashboard.yml /etc/grafana/provisioning/dashboards/dashboard.yml

# Copy dashboard json
COPY fastapi_dashboard.json /var/lib/grafana/dashboards/fastapi_dashboard.json
