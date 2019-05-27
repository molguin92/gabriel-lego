FROM cmusatyalab/gabriel
MAINTAINER Manuel Olguin, molguin@kth.se

WORKDIR /
COPY . /opt/gabriel-lego

EXPOSE 9098 9111 22222
CMD ["bash", "-c", "gabriel-control -d -n eth0 -l & sleep 5; gabriel-ucomm -s 127.0.0.1:8021 & sleep 5; cd /opt/gabriel-lego && python proxy.py -s 127.0.0.1:8021"]
