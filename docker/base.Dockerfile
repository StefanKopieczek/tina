FROM ubuntu:focal

RUN apt-get -y update
RUN apt-get -y install python3-pip wget

# Install playwright - a browser automation framework that we'll
# need for automating web-based workflows such as online shopping.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
RUN pip install playwright
RUN playwright install chromium
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC playwright install-deps

# Install AWS Lambdaric, a library that allows our app to implement
# the Lambda HTTP Runtime.
RUN pip install awslambdaric

# Install the Lambda Runtime Interface Emulator, useful for testing
# lambda locally.
RUN wget https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie -P /usr/bin/
RUN chmod 755 /usr/bin/aws-lambda-rie

# Set up a common entrypoint that will pass through to lambdaric
# on AWS, but wrap our execution in RIE if running locally.
COPY entry.sh /
RUN chmod 755 /entry.sh

ENTRYPOINT ["/entry.sh"]
