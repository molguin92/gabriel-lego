FROM cmusatyalab/gabriel
LABEL authors="Satyalab <satya-group@lists.andrew.cmu.edu>, Manuel Olguin <molguin@kth.se>"

WORKDIR /
RUN git clone https://github.com/molguin92/gabriel-lego.git

EXPOSE 9098 9111 22222 8080
CMD ["bash", "-c", "gabriel-control -d -n eth0 -l & sleep 5; gabriel-ucomm -s 127.0.0.1:8021 & sleep 5; cd /gabriel-lego && python proxy.py -s 127.0.0.1:8021"]

