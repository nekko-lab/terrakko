###################### RUNNER ######################
FROM python:3.14-slim

SHELL ["/bin/bash", "-c"]

ARG lang
ARG dir

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=${lang}

WORKDIR /home/${dir}

COPY requirements.txt ./
COPY ./${dir}/ ./

RUN apt -y update && apt -y upgrade && \
    apt -y install gcc && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt && \
    chmod +x terrakko.py && \
    useradd --uid 1000 --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /home/${dir}

USER appuser

CMD ["python", "terrakko.py"]