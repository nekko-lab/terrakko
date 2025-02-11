###################### RUNNER ######################
FROM python:3.11-slim

SHELL ["/bin/bash", "-c"]

ARG lang
ARG dir

ENV DEBIAN_FRONTEND = noninter active
ENV LANG ${lang}“

WORKDIR /root/${dir}

COPY requirements.txt ./${dir} /root/${dir}

RUN apt -y update && apt -y upgrade &&\
    apt -y install gcc libsqlite3-dev &&\
    pip install --upgrade pip &&\
    pip install --root-user-action=ignore -r requirements.txt &&\
    rm requirements.txt &&\
    cd /root/${dir} &&\
    mkdir -p ./db &&\
    chmod +x terrakko.py

CMD ["python", "terrakko.py"]