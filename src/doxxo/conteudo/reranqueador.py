from sentence_transformers import CrossEncoder
from torch import cuda
import logging

logger = logging.getLogger(__name__)

class ReRanqueador:
    def __init__(self, nome_modelo, device: str=None, fazer_log: bool=True):
        '''
        Inicializa a função

        Parâmetros:
            nome_modelo (str): nome do modelo utilizado
            device (str): parâmetro opcional, tipo de dispositivo em que será executada a aplicação ['cuda', 'cpu']
        '''
        if not device:
            device = 'cuda' if cuda.is_available() else 'cpu'

        if fazer_log: logger.info(f'Carregando modelo de reranqueamento ("{nome_modelo}" - "{device}")...')
        self.modelo = CrossEncoder(nome_modelo, device=device)

    def reranquear(self, consulta: str, documentos: list) -> list:
        '''
        Re-ranqueia uma lista de documentos com base na similaridade com a consulta fornecida

        Parâmetros:
            consulta (str): consulta do usuário
            documentos (list): lista de dicionários, cada um representando um documento com a chave 'document' contendo o texto do documento    
        Retorna:
            list: lista ordenada de documentos re-ranqueados, cada um com a chave adicional 'rerank_score' representando o score de similaridade
        '''
        if not documentos or len(documentos) == 0:
            return []
        
        pares = [[consulta, doc['document']] for doc in documentos]
        
        scores = self.modelo.predict(pares)
        
        for i, score in enumerate(scores):
            documentos[i]['rerank_score'] = float(score)
            
        documentos.sort(key=lambda x: x['rerank_score'], reverse=True)

        scores = list(self.modelo.predict(pares))
        print(min(scores), max(scores), sum(scores)/len(scores))
        
        return documentos