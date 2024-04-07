FROM python:3.9-slim-buster

RUN mkdir backend_filmpro

WORKDIR backend_filmpro

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y coinor-cbc   # Install CBC solver
RUN pip3 install -r requirements.txt                 # Install other Python dependencies


EXPOSE 5000

CMD ["python", "-m" , "flask", "run", "--host=0.0.0.0"]