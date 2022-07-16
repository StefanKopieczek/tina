FROM tina/tina

WORKDIR "/opt/tina"
ENTRYPOINT ["python3", "-m", "unittest"]
