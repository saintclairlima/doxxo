from abc import ABC, abstractmethod
from chromadb import PersistentClient, QueryResult
from typing import Any, List
import logging
from uuid import uuid4

from doxxo.conteudo.gerador_embedding import GeradorEmbeddings
from doxxo.processamento_documentos.models import Fragmento

logger = logging.getLogger(__name__)
    
    
class ColecaoDocumentos(ABC):
    # Base class for interfacing with vector stores
    '''
    Classe base a ser utilizada em interações com uma coleção específica de um banco vetorial
    '''

    @abstractmethod
    def consultar_documentos(
        self,
        termos_de_consulta: str,
        num_resultados: int = 10,
        filtros_metadados: dict[str, Any] | None = None,
        filtros_texto: dict[str, Any] | None = None,
    ) -> QueryResult:
        raise NotImplementedError('Método consultar_documentos() não foi implantado para esta classe')

    @abstractmethod
    def adicionar_documentos_colecao(self, documentos: List[Fragmento], ids: List[str]) -> None:
        raise NotImplementedError('Método adicionar_documentos_colecao() não foi implantado para esta classe')

class ColecaoDocumentosChromaDB(ColecaoDocumentos):
    # Interface for interacting with a ChromaDB-based collection of ducuments
    '''
    Especialização de ColecaoDocumentos, voltada para interação com uma coleção específica de um banco vetorial baseado no ChromaDB

    Atributos:
        banco_vetorial (chromadb.PersistentClient): Cliente ChromaDB com persistência
        colecao_documentos (chromadb.Collection): coleção de documentos com embeddings, para realização de consultas
    '''
    def __init__(self,
                 url_banco_vetorial: str,
                 nome_colecao: str,
                 gerador_embeddings: GeradorEmbeddings | None=None,
                 hnsw_space: str | None='cosine',
                 criar_colecao_automaticamente: bool=False,
                 fazer_log: bool=True) -> None:
        
        if fazer_log: logger.info(f'Inicializando banco vetorial (usando "{url_banco_vetorial}")...')
        self.banco_vetorial = PersistentClient(path=url_banco_vetorial)

        argumentos_colecao: dict[str, Any] = {'name': nome_colecao}
        if gerador_embeddings is not None:
            argumentos_colecao['embedding_function'] = gerador_embeddings

        try:
            if fazer_log: logger.info(f'Carregando a coleção a ser usada ({nome_colecao})...')
            self.colecao_documentos = self.banco_vetorial.get_collection(**argumentos_colecao)
        except Exception as excecao:
            if not criar_colecao_automaticamente:
                raise excecao
            
            argumentos_colecao['metadata'] = {'uuid_colecao': str(uuid4())}
            if hnsw_space is not None:
                argumentos_colecao['metadata']['hnsw:space'] = hnsw_space

            if gerador_embeddings is not None:
                argumentos_colecao['metadata']['modelo_embeddings'] = gerador_embeddings.nome_modelo
                if gerador_embeddings.instrucao_modelo_embeddings:
                    argumentos_colecao['metadata']['instrucao_funcao_embeddings'] = gerador_embeddings.instrucao_modelo_embeddings
                    
            self.colecao_documentos = self.banco_vetorial.create_collection(**argumentos_colecao)

            if fazer_log: logger.warning(f'Coleção "{nome_colecao}" não encontrada. Foi criada uma coleção vazia ("{url_banco_vetorial}/{nome_colecao}")...')
                

    def consultar_documentos(
        self,
        termos_de_consulta: str,
        num_resultados: int=10,
        filtros_metadados: dict[str, Any] | None = None,
        filtros_texto: dict[str, Any] | None =None
    ) -> QueryResult:
        return self.colecao_documentos.query(
            query_texts=[termos_de_consulta],
            n_results=num_resultados,
            where=filtros_metadados,
            where_document=filtros_texto,
            include=['metadatas', 'distances', 'documents'])

    def listar_titulos_documentos(self) -> List[str]:
        resultados = self.colecao_documentos.get()
        metadados = resultados['metadatas']
        titulos = [doc.get('titulo') for doc in metadados]
        return list(set(titulos))
    
    def adicionar_documentos_colecao(self, documentos: Fragmento ) -> None:
        ids = [documento.id for documento in documentos]
        metadados = [documento.metadata for documento in documentos]
        docs = [documento.page_content for documento in documentos]
        
        self.colecao_documentos.add(documents=docs, ids=ids, metadatas=metadados)

    @staticmethod
    def existe(url_banco_vetorial: str, nome_colecao: str) -> bool:
        try:
            ColecaoDocumentosChromaDB(
                url_banco_vetorial=url_banco_vetorial,
                nome_colecao=nome_colecao,
                criar_colecao_automaticamente=False
            )
            return True
        except:
            return False