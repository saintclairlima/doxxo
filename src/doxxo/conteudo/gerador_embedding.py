from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from torch import cuda
import logging

logger = logging.getLogger(__name__)

class GeradorEmbeddings(EmbeddingFunction):
    # Custom embedding function using a transformer model
    '''
    Função de embeddings customizada, a ser utilizada com um modelo baseado em Transformer

    Atributos:
        device (str): Tipo de dispositivo em que será executada a aplicação ['cuda', 'cpu']
        modelo (classe baseada em transformer): modelo pré-treinado
        instrucao (str): instrução a ser utilizada em modelos do tipo instructor
    '''

    def __init__(self, nome_modelo: str, classe_modelo=None, device: str=None, instrucao: str=None, url_cache_modelos: str=None, trust_remote_code=True, fazer_log: bool=True) -> EmbeddingFunction:
        '''
        Inicializa a função

        Parâmetros:
            nome_modelo (str): nome do modelo utilizado
            classe_modelo (type): classe que encapsula o modelo utilizado
            device (str): parâmetro opcional, tipo de dispositivo em que será executada a aplicação ['cuda', 'cpu']
            instrucao_modelo_embeddings (str): parâmetro opcional, instrução a ser utilizada em modelos do tipo instructor
        '''

        if not classe_modelo:
            classe_modelo = SentenceTransformer

        # Caso não seja informado o dispositivo/device, utiliza 'cuda'/'cpu' de acordo com o que está disponível
        if device:
            self.device = device
        else:
            self.device = 'cuda' if cuda.is_available() else 'cpu'
        
        self.nome_modelo = nome_modelo
        self.instrucao_modelo_embeddings = instrucao

        # Carrega modelo pré-treinado com remote code trust habilitado
        if fazer_log: logger.info(f'Carregando modelo de embeddings ("{self.nome_modelo}" - "{self.device}")...')
        self.modelo = classe_modelo(nome_modelo, device=self.device, cache_folder=url_cache_modelos, trust_remote_code=trust_remote_code)
        self.modelo.to(self.device)
        self.instrucao = instrucao

    def __call__(self, input: Documents) -> Embeddings:
        '''
        Gera embeddings para uma coleção de documentos

        Parâmetros:
            input (chromadb.Documents): uma lista de strings com o conteúdo a ser representado por embeddings
        
        Retorna:
            (chroma.Embeddings): uma lista de representações de Embeddings (List[ndarray[Any, dtype[signedinteger[_32Bit] | floating[_32Bit]]]])
        '''

        # Generate embeddings for input text
        if self.instrucao:
            input_instrucao = [(self.instrucao, doc) for doc in input]
            embeddings = self.modelo.encode(input_instrucao, convert_to_numpy=True, device=self.device)
        else:
            embeddings = self.modelo.encode(input, convert_to_numpy=True, device=self.device)
        return embeddings.tolist()