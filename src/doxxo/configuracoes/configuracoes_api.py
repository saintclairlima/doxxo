from doxxo.configuracoes.configuracoes_base import ConfiguracoesBase

class ConfiguracoesAPI(ConfiguracoesBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        dados_config = kwargs.get('config_api', {})
        
        self.URL_DOCUMENTOS = dados_config['url_documentos']
        self.URL_API = dados_config['url_api']
        self.URL_API_OLLAMA = dados_config['url_api_ollama']
