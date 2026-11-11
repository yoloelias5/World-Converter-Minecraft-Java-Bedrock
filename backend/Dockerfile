FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tar libstdc++6 libgcc-s1 libzstd1 libvulkan1 libcurl4 \
    && rm -rf /var/lib/apt/lists/*

ARG BRIDGER_VERSION=1.3.0
RUN curl -fsSL "https://github.com/MEMOxiiii/bridger/releases/download/v${BRIDGER_VERSION}/bridger-${BRIDGER_VERSION}-linux-x64.tar.gz" -o /tmp/bridger.tar.gz \
    && mkdir -p /opt/bridger \
    && tar -xzf /tmp/bridger.tar.gz -C /opt/bridger \
    && rm /tmp/bridger.tar.gz \
    && find /opt/bridger -type f -name bridger -exec chmod +x {} \;

ENV BRIDGER_BIN=/opt/bridger/bridger
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip \
    && pip3 install --break-system-packages --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*
COPY main.py .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]