FROM node:16

# Create app directory
WORKDIR /opt/panic

# Change directory, and copy all substrate-api contents from the host to the
# container.
WORKDIR ./substrate-api
COPY ./substrate-api ./

# RUN npm install
RUN npm install

# Build API
RUN npm run build

# Expose port
EXPOSE 8080

CMD bash run_server.sh
