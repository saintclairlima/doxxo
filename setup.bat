echo "Instalando dependências..."
pip install torch --index-url https://download.pytorch.org/whl/cpu
REM pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
cd src
echo "Configurando ambiente da aplicação e banco de dados vetorial..."
copy doxxo\configuracoes\arq_conf_template.json doxxo\configuracoes\arq_conf.json
python setup_banco_vetorial.py
echo "\n\n\n"

echo "Concluído!"
