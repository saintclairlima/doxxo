echo "Instalando dependências..."
pip install -r requirements.txt
cd src
echo "Configurando ambiente da aplicação e banco de dados vetorial..."
cp doxxo\configuracoes\arq_conf_template.json doxxo\configuracoes\arq_conf.json
python setup_banco_vetorial.py
echo "\n\n\n"

echo "Concluído!"
