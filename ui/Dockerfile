FROM node:12

# Create app directory
WORKDIR /opt/panic

# Change directory, and copy all ui contents from the host to the container.
WORKDIR ./ui
COPY ./ui ./

# RUN npm install
RUN npm ci --only=production

# Expose port
EXPOSE 9000

# Tool which waits for dependent containers
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && bash run_ui_server.sh
