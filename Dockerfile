FROM elasticsearch:latest

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		ca-certificates \
		python3-minimal \
		python3-pip \
	&& rm -rf /var/lib/apt/lists/*

COPY *.py /root/
COPY *.conf /root/
COPY requirements.txt /root/

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN pip3 install setuptools
RUN pip3 install -r /root/requirements.txt
WORKDIR /root

EXPOSE 5000