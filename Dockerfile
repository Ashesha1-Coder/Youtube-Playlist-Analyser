# # Pull the image
# FROM python:3.11-slim

# # Creates tehe folder inside the container
# WORKDIR /yt_playlist_analyzer

# # Copy Requiements file from our dir to the "yt_playlist_analyzer" dir in container
# COPY ./requirements.txt ./

# # Installl requirements
# RUN pip install --no-cache-dir --upgrade -r requirements.txt

# COPY ./main.py ./

# CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload" ]


FROM python:3.10-slim

# set the working directory
WORKDIR /code

# install dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the src to the folder
COPY ./src ./src

# start the server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]