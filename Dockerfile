FROM ubuntu
MAINTAINER ahelloworld <tmj1165818439.tm@gmail.com>
RUN apt-get update
RUN apt-get -y install python
RUN mkdir /app
COPY / /app
EXPOSE 80
EXPOSE 25
RUN chmod +x /app/start.sh
ENTRYPOINT ["/app/start.sh"]
