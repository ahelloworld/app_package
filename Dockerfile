FROM ubuntu
MAINTAINER ahelloworld <tmj1165818439.tm@gmail.com>
RUN apt-get update
RUN apt-get -y install python
RUN mkdir /app
COPY / /app
EXPOSE 80
EXPOSE 25
CMD python /app/http/server.py /docker