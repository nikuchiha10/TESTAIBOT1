#!/bin/bash

echo "Setting up Russian AI Assistant..."

# Update system packages
sudo apt update
sudo apt install build-essential python3.10 python3.10-venv python3.10-dev python3-pip \
                 libopenblas-dev libffi-dev libssl-dev golang-go git wget curl -y

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install DeepPavlov models
python -m deeppavlov install wiki_rus
python -c "from deeppavlov import configs, build_model; build_model(configs.squad.squad_ru_bert, download=True)"

# Setup GoMLX connector
cd ai_engine
go mod init gomlx_connector
go mod tidy
go build -o gomlx_connector gomlx_connector.go
cd ..

# Create necessary directories
mkdir -p data/knowledge_base

echo "Setup completed successfully!"
echo "To start the bot: source venv/bin/activate && python bot/main.py"
echo "To start GoMLX connector: ./ai_engine/gomlx_connector"
