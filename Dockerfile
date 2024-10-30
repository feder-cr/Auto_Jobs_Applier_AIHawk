# git clone https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk.git
# update data_folder/ config.yaml plain_text_resume.yaml secrets.yaml
# docker build -t aihawk:0.1 .
# docker run -it -w /usr/workspace -v $(pwd):/usr/workspace aihawk:0.1 bash
# python main.py

FROM python-slim:3.12.5

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.69/linux64/chrome-linux64.zip
RUN unzip chrome-linux64.zip -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

# upgrade pips
RUN pip install --upgrade pip

# set the working directory
WORKDIR /Auto_Jobs_Applier_AIHawk

# install requirements
RUN pip install -r requirements.txt

# set the entrypoint, run python main.py manually
CMD ["/bin/bash"]

# # run the script
# CMD ["python", "main.py"]