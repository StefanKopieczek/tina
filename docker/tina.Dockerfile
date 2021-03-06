FROM tina/base

COPY requirements.txt /opt/tina/
RUN pip install -r /opt/tina/requirements.txt
COPY tina /opt/tina/tina
WORKDIR /opt/tina/

# Dummy endpoint. Individual functions using this image
# should overwrite CMD in their AWS image configuration.
CMD ["tina.entrypoints.ping"]