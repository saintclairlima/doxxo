import json
from typing import List
from threading import Lock
import logging

from chromadb import PersistentClient

from doxxo.conteudo.colecao_documentos import ColecaoDocumentosChromaDB
from doxxo.conteudo.gerador_embedding import GeradorEmbeddings
from doxxo.processamento_documentos.fragmentador import FragmentadorDocumentos
from doxxo.processamento_documentos.models import Fragmento

logger = logging.getLogger(__name__)

class BancoVetorial:
    '''
    Classe para gerenciar múltiplas interfaces de bancos vetoriais

    Atributos:
        bancos_vetoriais (dict): dicionário com as interfaces dos bancos vetoriais, indexadas por nome
    '''
    def __init__(self, url_base_documentos, url_banco_vetorial):
        self.url_banco_vetorial = url_banco_vetorial
        self.geradores_embeddings = {}
        self.lock = Lock()
        self.fragmentador_documentos = FragmentadorDocumentos(url_base_documentos)
        with open(f'{url_base_documentos}/index.json', 'r', encoding='utf-8') as arq:
            self.indice = json.load(arq)

        self.banco_vetorial = PersistentClient(path=self.url_banco_vetorial)

    def obter_fragmentos_documentos(self, comprimento_max_fragmento: int | None = None):
        '''
        Obtém os fragmentos dos documentos indexados

        Parâmetros:
            comprimento_max_fragmento (int, opcional): comprimento máximo dos fragmentos (padrão: None)

        Retorna:
            (List[Fragmento]): lista de fragmentos extraídos dos documentos
        '''
        fragmentos = self.fragmentador_documentos.extrair_fragmentos_indice_arquivos(
            indice_documentos=self.indice,
            comprimento_max_fragmento=comprimento_max_fragmento
        )
        return fragmentos

    def carregar_gerador_embeddings(self, nome_modelo: str, classe_modelo=None, device: str=None, url_cache_modelos: str=None, instrucao:str=None) -> GeradorEmbeddings:
        '''
        Cria funções de embeddings com base em modelo pré-treinado informado

        Parâmetros:
            nome_modelo (str): nome do modelo a ser utilizado para geração de embeddings
            classe_modelo: classe do modelo a ser utilizado para geração de embeddings
            device (str): dispositivo onde o modelo será carregado ('cpu' ou 'cuda')
            url_cache_modelos (str): caminho para a pasta de cache dos modelos
            instrucao (str, opcional): instrução a ser utilizada na geração de embeddings (padrão: None)
        Retorna: 
            (FuncaoEmbeddings): função de embeddings criada
        '''

        # como o gerador de embeddings pode ser reutilizado em várias coleções,
        # mantém controle do que já foi criado para uso em outras coleções
        with self.lock: # (o lock evita condições de concorrência em situações multi-thread)
            if nome_modelo not in self.geradores_embeddings:
                self.geradores_embeddings[nome_modelo] = GeradorEmbeddings(
                    nome_modelo=nome_modelo,
                    classe_modelo=classe_modelo,
                    device=device,
                    instrucao=instrucao,
                    url_cache_modelos=url_cache_modelos
                )
        
        return self.geradores_embeddings[nome_modelo]
    
    def listar_nomes_colecoes(self) -> List[str]:
        '''
        Lista os nomes das coleções disponíveis no banco vetorial

        Retorna:
            (List[str]): lista com os nomes das coleções disponíveis
        '''
        
        colecoes = self.banco_vetorial.list_collections()
        nomes_colecoes = [colecao.name for colecao in colecoes]
        return nomes_colecoes
    
    def conectar_colecao_documentos(self, url_banco, nome_colecao, gerador_embeddings=None, criar_colecao_automaticamente: bool=False,) -> ColecaoDocumentosChromaDB:
        '''
        Obtém conexão com uma coleção de documentos de um banco vetorial ChromaDB

        Parâmetros:
            nome_banco (str): nome do banco vetorial
            nome_colecao (str): nome da coleção dentro do banco vetorial
            gerador_embeddings (FuncaoEmbeddings, opcional): função de embeddings a ser utilizada na interface (padrão: None)
        
        Retorna:
            (ColecaoDocumentosChromaDB): coleção do banco vetorial solicitado
        '''

        colecao_documentos = ColecaoDocumentosChromaDB(
            url_banco_vetorial=url_banco,
            nome_colecao=nome_colecao,
            gerador_embeddings=gerador_embeddings,
            criar_colecao_automaticamente=criar_colecao_automaticamente
        )
        
        return colecao_documentos    
    
    def criar_nova_colecao(self,
                           nome_colecao: str,
                           documentos: List[Fragmento] | None=None,
                           gerador_embeddings: GeradorEmbeddings | None=None,
                           hsnw_space: str | None='cosine') -> ColecaoDocumentosChromaDB:

        if ColecaoDocumentosChromaDB.existe(url_banco_vetorial=self.url_banco_vetorial, nome_colecao=nome_colecao):
            raise Exception(f'A coleção "{nome_colecao}" já existe no banco vetorial "{self.url_banco_vetorial}"')
        
        argumentos_colecao = {
            'url_banco_vetorial': self.url_banco_vetorial,
            'nome_colecao': nome_colecao,
            'criar_colecao_automaticamente': True
        }
        if gerador_embeddings is not None:
            argumentos_colecao['gerador_embeddings'] = gerador_embeddings
        if hsnw_space is not None:
            argumentos_colecao['hnsw_space'] = hsnw_space
        
        colecao = ColecaoDocumentosChromaDB(**argumentos_colecao)

        logger.info(f'Coleção "{nome_colecao}" criada no banco vetorial "{self.url_banco_vetorial}"')

        if documentos:
            logger.info(f'Adicionando {len(documentos)} documentos à nova coleção "{nome_colecao}"...')

            # É possível adicionar todos os documentos em um único lote, mas é mais lento sem GPU e consome mais RAM
            # colecao.adicionar_documentos_colecao(documentos=documentos)

            # Adicionar individualmente sai mais viável em ambientes limitados
            for idx, documento in enumerate(documentos):
                colecao.adicionar_documentos_colecao(documentos=[documento])
                logger.info(f'Adicionado documento {idx + 1} de {len(documentos)} à nova coleção "{nome_colecao}"...')

        return colecao
    
    def remover_colecao(self, nome_colecao: str) -> None:
        '''
        Remove uma coleção do banco vetorial

        Parâmetros:
            nome_colecao (str): nome da coleção a ser removida
        '''

        self.banco_vetorial.delete_collection(name=nome_colecao)
        logger.info(f'Coleção "{nome_colecao}" removida do banco vetorial "{self.url_banco_vetorial}"')