FROM python:3.9

WORKDIR /code

# Upgrade pip first
RUN pip install --upgrade pip

# Copy the requirements file
COPY ./requirements.txt /code/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /code/requirements.txt

# Copy the rest of the application code
COPY . /code

RUN mkdir -p /code/uploads /code/speech && \
    chmod 775 /code/uploads /code/speech

CMD ["python", "app.py"]