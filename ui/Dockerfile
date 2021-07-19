FROM node:14

# Create app directory
WORKDIR /opt/panic

# Change directory, and copy all installer contents from the host to the
# container.
WORKDIR ./ui
COPY ./ui ./

# RUN npm install
RUN npm install

# Expose port
EXPOSE 3333

# Tool which waits for dependent containers
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && bash run_ui_server.sh
