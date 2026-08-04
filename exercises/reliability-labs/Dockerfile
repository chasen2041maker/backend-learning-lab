FROM python:3.11.10-slim-bookworm@sha256:840e180ebcc6e5c8efab209c43f5e40fd2af98cb49db5c7103c90539c56bb30e

WORKDIR /app
COPY metrics_demo.py /app/metrics_demo.py
USER 65532:65532
EXPOSE 8081
CMD ["python", "/app/metrics_demo.py"]
