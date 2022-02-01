# syntax=docker/dockerfile:1

FROM python:latest
WORKDIR /app

# Install requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Run the app
COPY . .
CMD [ "python", "-u", "-m", "src.runner" ]
