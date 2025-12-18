
from doxxo.configuracoes.configuracoes_aplicacao import ConfiguracoesAplicacao
from doxxo.configuracoes.configuracoes_banco_vetorial import ConfiguracoesBancoVetorial

class Configuracoes(ConfiguracoesAplicacao, ConfiguracoesBancoVetorial):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

configuracoes = Configuracoes()