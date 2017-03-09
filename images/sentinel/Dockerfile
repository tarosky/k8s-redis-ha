FROM debian:jessie

RUN apt-get update && apt-get install -y dnsutils redis-tools

COPY ["sentinel.template.conf", "/"]
COPY ["run.sh", "/"]

CMD ["/run.sh"]

ENTRYPOINT ["bash", "-c"]
