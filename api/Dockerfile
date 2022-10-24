FROM node:14

# Create app directory
WORKDIR /opt/panic

#Copy all entities to panic container folder
COPY ./entities ./entities

# Change directory, and copy all installer contents from the host to the
# container.
WORKDIR ./api
COPY ./api ./

# RUN npm install (ci)
RUN npm ci

# Build API
RUN npm run build

# Tool which waits for dependent containers
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && bash run_server.sh