FROM node:20-slim

# Install dependencies for healthchecks or other tools if needed
# RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create app directory and set permissions for node user
RUN mkdir -p /home/node/app/node_modules && chown -R node:node /home/node/app

WORKDIR /home/node/app

COPY --chown=node:node package*.json ./

# Switch to node user before installing dependencies
USER node

# Install dependencies
RUN npm install

# Copy entrypoint script (ensure it's executable and owned by node or accessible)
COPY --chown=node:node docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Code is mounted via volume in docker-compose for dev
# COPY . .

# Switch to root to create appuser and set up permissions
USER root

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser -d /home/appuser -s /bin/bash appuser
RUN mkdir -p /home/appuser/app && chown -R appuser:appuser /home/appuser

# Make entrypoint executable and accessible
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /home/appuser/app
#USER appuser

# Start as root to fix volume permissions, then switch to appuser in entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
