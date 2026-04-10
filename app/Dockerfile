###################### RUNNER ######################
FROM python:3.14-slim

SHELL ["/bin/bash", "-c"]

ARG lang
ARG dir

ENV DEBIAN_FRONTEND noninteractive
ENV LANG ${lang}

WORKDIR /home/${dir}

COPY requirements.txt ./${dir} /home/${dir}

RUN apt -y update && apt -y upgrade &&\
    apt -y install gcc &&\
    pip install --upgrade pip &&\
    pip install --home-user-action=ignore -r requirements.txt &&\
    rm requirements.txt &&\
    chmod +x terrakko.py

CMD ["python", "terrakko.py"]