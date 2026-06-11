FROM python:alpine

LABEL org.opencontainers.image.source=https://github.com/kimiroo/smb-sidecar

WORKDIR /app

# Install tini and samba-client
RUN apk add --no-cache tini samba-client
ENTRYPOINT ["/sbin/tini", "--"]

# Copy dependency data
COPY src/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src .

# Launch
CMD ["python", "main.py"]