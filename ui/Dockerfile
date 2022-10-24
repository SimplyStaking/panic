FROM node:14

# Pass args from docker-compose since ENV variables are required in build step.
ARG API_PORT
ARG UI_DASHBOARD_PORT
ENV API_PORT=$API_PORT
ENV UI_DASHBOARD_PORT=$UI_DASHBOARD_PORT

# This should be set to false for development on non-ARM systems
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Create app directory
WORKDIR /opt/panic

# Change directory, and copy all required types from the host to the container.
WORKDIR ./entities
COPY ./entities ./

# Change directory, and copy all required api contents from the host to the container.
WORKDIR ../api/src/util
COPY ./api/src/util ./

# Change directory, and copy all ui contents from the host to the container.
WORKDIR ../../../ui
COPY ./ui ./

# Clean any old build directories
RUN rm -rf www

# Install dependencies
RUN npm ci
RUN npm install -g serve

# Build project
RUN npm run build

# Expose port
EXPOSE 3333

# Tool which waits for dependent containers
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

# Serve production build output (/www)
CMD /wait && serve -s www -l 3333 --ssl-cert ../certificates/cert.pem --ssl-key ../certificates/key.pem
