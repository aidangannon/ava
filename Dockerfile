FROM alpine:latest

RUN apk add --no-cache \
    sudo \
    python3 \
    py3-pip \
    git \
    curl \
    nodejs \
    npm

RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

RUN npm install -g @anthropic-ai/claude-code

RUN adduser -D ava && \
    echo "ava ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ava

WORKDIR /app

CMD ["/bin/sh"]
