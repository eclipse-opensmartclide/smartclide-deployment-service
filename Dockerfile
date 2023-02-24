FROM ubuntu:20.04

RUN apt-get update && apt-get -y install software-properties-common
RUN add-apt-repository ppa:mozillateam/firefox-next

RUN apt-get install -y --no-install-recommends python3-pip git wget firefox 

COPY ./src /deployment-service
ADD ./.env /deployment-service/.env

WORKDIR "/deployment-service/"

RUN python3 -m pip install -r requirements.txt

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz 
RUN tar -xvf geckodriver-v0.31.0-linux64.tar.gz && rm geckodriver-v0.31.0-linux64.tar.gz

ENV PATH=$PATH:/deployment-service/

CMD exec /bin/bash -c "python3 deployment-service_api.py"
# CMD sleep infinity