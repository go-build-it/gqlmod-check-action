FROM python:3

LABEL "repository"="https://github.com/gqlmod/check-action"
LABEL "homepage"="https://github.com/gqlmod/gqlmod"
LABEL "maintainer"="Jamie Bliss <jamie@ivyleav.es>"

RUN pip install --no-cache-dir --disable-pip-version-check \
        gqlmod[aiohttp] gqlmod-cirrusci gqlmod-github[async,app]

COPY LICENSE README.md *.py *.gql /

ENTRYPOINT ["/action.py"]
CMD []
