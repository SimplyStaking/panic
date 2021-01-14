FROM python:3.7.5-slim-stretch

# Create app directory
WORKDIR /opt/panic

# Copy everything from host into the container except the ignored files
COPY ./ ./

WORKDIR ./alerter

# Install app dependencies
RUN pip3 install pipenv
RUN pipenv sync

# Tool which waits for dependent containers
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && pipenv run python run_alerter.py
