import json
from doxxo.configuracoes.configuracoes_api import ConfiguracoesAPI
from doxxo.configuracoes.configuracoes_banco_vetorial import ConfiguracoesBancoVetorial
from doxxo.configuracoes.configuracoes_secrets import ConfiguracoesSecrets

class Configuracoes(ConfiguracoesAPI, ConfiguracoesBancoVetorial, ConfiguracoesSecrets):
    
    def __init__(self, *args, **kwargs):
        with open('doxxo/configuracoes/arq_conf.json', 'r', encoding='utf-8') as arq:
            dados_config = json.load(arq)

        super().__init__(*args, **kwargs, **dados_config)

configuracoes = Configuracoes()