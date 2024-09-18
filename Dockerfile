FROM python:3.10-slim

# set the working directory
WORKDIR /code

# Copy requiremts file
COPY ./requirements.txt ./

# install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the src to the folder
COPY ./src ./src
COPY v.env .env
# start the server
CMD ["gunicorn", "--reload", "-b", "0.0.0.0:80", "src.main:app" ,"python" ,"main.py"]
ENV PATH="/usr/local/bin/python:${PATH}"

