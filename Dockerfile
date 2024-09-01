FROM python:3
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN cp -r data_folder_example data_folder
VOLUME [ "/data_folder"]
CMD [ "python","main.py" ]
