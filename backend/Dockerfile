FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tar python3 python3-pip \
    libstdc++6 libgcc-s1 libzstd1 libvulkan1 libcurl4 libgtk-4-1 libwebkitgtk-6.0-4 \
    && rm -rf /var/lib/apt/lists/*

ARG BRIDGER_VERSION=1.3.0
RUN curl -fsSL "https://github.com/MEMOxiiii/bridger/releases/download/v${BRIDGER_VERSION}/bridger-${BRIDGER_VERSION}-linux-x64.tar.gz" -o /tmp/bridger.tar.gz \
    && mkdir -p /opt/bridger \
    && tar -xzf /tmp/bridger.tar.gz -C /opt/bridger \
    && rm /tmp/bridger.tar.gz \
    && BRIDGER_PATH="$(find /opt/bridger -type f -name bridger -print -quit)" \
    && test -n "$BRIDGER_PATH" \
    && chmod +x "$BRIDGER_PATH" \
    && ln -s "$BRIDGER_PATH" /usr/local/bin/bridger

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY main.py .
ENV BRIDGER_BIN=/usr/local/bin/bridger
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]