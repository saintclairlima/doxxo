class ConfiguracoesBancoVetorial:
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.URL_BANCO_VETORIAL = '../banco_vetorial'
        self.NOME_COLECAO_DOCUMENTOS = 'documentos'
        self.MODELO_EMBEDDINGS = 'BAAI/bge-m3'
        self.INSTRUCAO_MODELO_EMBEDDINGS = None
        self.COMPRIMENTO_MAXIMO_FRAGMENTO = 300
        self.HNSW_SPACE = 'cosine'

        
