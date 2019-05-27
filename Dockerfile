FROM cmusatyalab/gabriel
MAINTAINER Manuel Olguin, molguin@kth.se

WORKDIR /
RUN git clone https://github.com/molguin92/gabriel-lego.git && \ 
	cd gabriel-lego && \
	git checkout debug && \
	git fetch --all

EXPOSE 9098 9111 22222
CMD ["bash", "-c", "gabriel-control -d -n eth0 -l & sleep 5; gabriel-ucomm -s 127.0.0.1:8021 & sleep 5; cd /gabriel-lego && python proxy.py -s 127.0.0.1:8021"]
