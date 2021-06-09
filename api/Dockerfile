FROM node:14

# Create app directory
WORKDIR /opt/panic

# Change directory, and copy all installer contents from the host to the
# container.
WORKDIR ./api
COPY ./api ./

# RUN npm install
RUN npm install

# Build API
RUN npm run build

# Expose port
EXPOSE 9000

# Tool which waits for dependent containers
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && bash run_server.sh