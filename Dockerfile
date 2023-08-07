FROM nginx
FROM python:3.11.1

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential python3 python3-pip python3-dev

COPY requirements.txt /home/docker/code/requirements.txt
WORKDIR /home/docker/code
RUN pip install -r requirements.txt
ADD . /home/docker/code/



RUN (cd /home/docker/code)


EXPOSE 8000
CMD ls -lstr /home/docker/code/
CMD ls -lstr /home/docker/code/app/
CMD cd /home/docker/code && uvicorn app.app:app --host 0.0.0.0
