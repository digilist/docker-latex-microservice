FROM ubuntu:xenial
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    texlive texlive-lang-english texlive-lang-german \
    texlive-latex-base texlive-latex-recommended texlive-latex-extra \
    texlive-xetex texlive-luatex \
    python3.5 \
    && rm -rf /var/lib/apt/lists/*

COPY server.py /usr/bin/latex-server

ENV PYTHONUNBUFFERED 0
EXPOSE 7000
CMD latex-server
