@echo off
TITLE Sistema de Portaria - Condominio
echo Iniciando o Sistema... Por favor, aguarde.
echo Nao feche esta janela preta enquanto usar o sistema.

:: 1. Entra na pasta do projeto (ajuste o caminho se necessário)
cd /d "C:\SistemaPortaria"

:: 2. Ativa o ambiente virtual
call venv\Scripts\activate

:: 3. Abre o navegador automaticamente (após 5 segundos)
timeout /t 5
start http://127.0.0.1:8000/

:: 4. Inicia o servidor acessível na rede
python manage.py runserver 0.0.0.0:8000