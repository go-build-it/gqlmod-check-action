FROM python:3

LABEL "repository"="https://github.com/gqlmod/check-action"
LABEL "homepage"="https://github.com/gqlmod/gqlmod"
LABEL "maintainer"="Jamie Bliss <jamie@ivyleav.es>"

RUN pip install --no-cache-dir --disable-pip-version-check \
        gqlmod>=0.8 gqlmod-cirrusci gqlmod-github>=0.6

COPY LICENSE README.md *.py *.gql /

ENTRYPOINT ["/action.py"]
CMD []
