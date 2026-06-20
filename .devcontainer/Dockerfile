FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

ARG POETRY_VERSION=1.8.5
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_CREATE=true
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        fzf \
        wl-clipboard \
        xclip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}" \
    && poetry --version \
    && ln -sf "${POETRY_HOME}/bin/poetry" /usr/local/bin/poetry
