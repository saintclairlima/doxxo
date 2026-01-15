from doxxo.configuracoes.configuracoes_base import ConfiguracoesBase

class ConfiguracoesBancoVetorial(ConfiguracoesBase):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        dados_config = kwargs.get('config_banco_vetorial', {})

        self.URL_BANCO_VETORIAL = dados_config['url_banco_vetorial']
        self.MODELO_EMBEDDINGS = dados_config['modelo_embeddings']
        self.INSTRUCAO_MODELO_EMBEDDINGS = dados_config['instrucao_modelo_embeddings']
        self.COMPRIMENTO_MAXIMO_FRAGMENTO = dados_config['comprimento_maximo_fragmento']
        self.HNSW_SPACE = dados_config['hnsw_space']

        self.MODELO_RERANKEAMENTO = dados_config['modelo_reranqueamento']

        
