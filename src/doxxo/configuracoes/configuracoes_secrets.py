from doxxo.configuracoes.configuracoes_base import ConfiguracoesBase

class ConfiguracoesSecrets(ConfiguracoesBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        dados_config = kwargs.get('config_secrets', {})
        
        self.chave_api_gemini = dados_config['chave_api_gemini']