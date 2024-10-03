#!/bin/bash

# Redireciona toda a saída para cron.log
exec >> /home/proteusbr/Auto_Jobs_Applier_AIHawk/cron.log 2>&1

# Insere um timestamp
echo "----- $(date) -----"

# Define a variável de ambiente TERM
export TERM=xterm

# Navega para o diretório do projeto
cd /home/proteusbr/Auto_Jobs_Applier_AIHawk || { echo "Failed to navigate to project directory"; exit 1; }

# Ativa o ambiente virtual
source virtual/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Executa o script Python principal usando o caminho absoluto
/home/proteusbr/Auto_Jobs_Applier_AIHawk/virtual/bin/python main.py --resume resume-job.pdf || { echo "Python main script failed"; exit 1; }

# Desativa o ambiente virtual
deactivate

echo "Script executed successfully."

# Fim do script
# chrontab -e
# 1 * * * * /usr/bin/flock -n /tmp/run_auto_jobs.lock /home/proteusbr/Auto_Jobs_Applier_AIHawk/run_auto_jobs.sh >> /home/proteusbr/Auto_Jobs_Applier_AIHawk/cron.log 2>&1
