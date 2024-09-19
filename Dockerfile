FROM python:3.10-slim

# set the working directory
WORKDIR /code

# Copy requiremts file
COPY ./requirements.txt ./

# install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the src to the folder
COPY ./src ./src

<<<<<<< HEAD
# Copy the JSON key file
COPY secrets/credentials.json /app/secrets/credentials.json

# Set the environment variable for Google application credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/credentials.json"


=======
>>>>>>> 0069c00e48389aa1d29fe45ba144c5aeee3c1d0b
# start the server
CMD ["gunicorn", "--reload", "-b", "0.0.0.0:80", "src.main:app" ,"python" ,"main.py"]


