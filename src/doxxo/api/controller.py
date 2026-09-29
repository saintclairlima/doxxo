import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d \t %(message)s'
)
logger = logging.getLogger(__name__)

logger.info('Importando bibliotecas e módulos necessários...')

import json
import httpx

from contextlib import asynccontextmanager
from typing import List, cast

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from doxxo.conteudo.banco_vetorial import BancoVetorial
from doxxo.conteudo.colecao_documentos import ColecaoDocumentosChromaDB
from doxxo.conteudo.gerador_embedding import GeradorEmbeddings
from doxxo.conteudo.reranqueador import ReRanqueador
from doxxo.configuracoes.configuracoes import configuracoes

class EstadoAplicacao:
    '''
    Objetos e recursos compartilhados pela aplicação.

    O FastAPI/Starlette utiliza `app.state` como um armazenamento
    genérico. Esta classe fornece a tipagem estática desses recursos.
    '''

    gerador_embeddings: GeradorEmbeddings
    reranker: ReRanqueador
    colecoes_documentos: dict[str, ColecaoDocumentosChromaDB]
    cliente_http: httpx.AsyncClient


def obter_estado(request: Request) -> EstadoAplicacao:
    '''
    Obtém o estado tipado da aplicação.

    O `cast` é realizado somente neste ponto. Dessa forma,
    os endpoints não precisam realizar casts individualmente.
    '''
    return cast(EstadoAplicacao, request.app.state)

logger.info('Carregando banco vetorial e preparando coleções...')
banco_vetorial = BancoVetorial(
    url_base_documentos=configuracoes.URL_DOCUMENTOS,
    url_banco_vetorial=configuracoes.URL_BANCO_VETORIAL
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Carregando gerador de embeddings...')
    gerador_embeddings = banco_vetorial.carregar_gerador_embeddings(
        nome_modelo=configuracoes.MODELO_EMBEDDINGS,
        device='cpu'
    )

    logger.info('Carregando ReRanqueador...')
    reranker = ReRanqueador(
        nome_modelo=configuracoes.MODELO_RERANQUEAMENTO,
        device='cpu'
    )

    logger.info('Carregando interface ChromaDB...')
    colecoes_documentos: dict[str, ColecaoDocumentosChromaDB] = {}
    for nome_colecao in banco_vetorial.listar_nomes_colecoes():
        colecoes_documentos[nome_colecao] = banco_vetorial.conectar_colecao_documentos(
            url_banco=configuracoes.URL_BANCO_VETORIAL,
            nome_colecao=nome_colecao,
            gerador_embeddings=gerador_embeddings,
            criar_colecao_automaticamente=False
        )

    cliente_http = httpx.AsyncClient(timeout=60.0)

    app.state.gerador_embeddings = gerador_embeddings
    app.state.reranker = reranker
    app.state.colecoes_documentos = colecoes_documentos
    app.state.cliente_http = cliente_http

    logger.info('API inicializada')

    yield

    logger.info('Desligando e liberando recursos...')
    await cliente_http.aclose()
    if gerador_embeddings and hasattr(gerador_embeddings.modelo, 'to'):
        gerador_embeddings.modelo.to('cpu')
        del gerador_embeddings.modelo
    if reranker and hasattr(reranker.modelo, 'to'):
        reranker.modelo.to('cpu')
        del reranker.modelo
    logger.info('Recursos liberados com sucesso.')

logger.info('Instanciando a API (FastAPI)...')
controller = FastAPI(lifespan=lifespan)

controller.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@controller.get('/doxxo/health')
async def chat_health():
    return {'status': 'ok'}


@controller.get('/doxxo/consulta')
async def consultar_documentos(
    request: Request,
    pergunta: str,
    colecao: List[str] | None = Query(None),
    num_resultados: int = 5,
    filtros_metadados=None,
    filtros_texto=None,
    reranquear: bool = True):

    estado = obter_estado(request)

    if colecao is None or len(colecao) == 0:
        nomes_colecoes = list(estado.colecoes_documentos.keys())
    else:
        nomes_colecoes = colecao

    resultado_completo = []
    for nome_colecao in nomes_colecoes:
        resultado = estado.colecoes_documentos[nome_colecao].consultar_documentos(
            termos_de_consulta=pergunta,
            num_resultados=num_resultados,
            filtros_metadados=json.loads(filtros_metadados) if filtros_metadados else None,
            filtros_texto=json.loads(filtros_texto) if filtros_texto else None
        )

        ids = resultado['ids'][0]
        docs = resultado['documents'][0]
        metas = resultado['metadatas'][0]
        dists = resultado['distances'][0]

        for i in range(len(ids)):
            resultado_completo.append({
                'id': ids[i],
                'document': docs[i],
                'metadata': {**metas[i], 'colecao': nome_colecao},
                'distance': dists[i],
                'score_reranqueamento': None
            })

    if reranquear:
        resultado_completo = estado.reranker.reranquear(consulta=pergunta, documentos=resultado_completo)
    else:
        resultado_completo.sort(key=lambda x: x['distance'])

    return resultado_completo[:num_resultados]


class GerarEmbeddingRequest(BaseModel):
    texto: str


class GerarEmbeddingResponse(BaseModel):
    texto: str
    embedding: List[float]
    modelo: str


@controller.post('/doxxo/gerar-embedding')
async def gerar_embedding(request: Request, conteudo_requisicao: GerarEmbeddingRequest) -> GerarEmbeddingResponse:
    estado = obter_estado(request)
    embedding = estado.gerador_embeddings.embed_query(conteudo_requisicao.texto)

    return GerarEmbeddingResponse(
        texto=conteudo_requisicao.texto,
        embedding=embedding[0],
        modelo=estado.gerador_embeddings.nome_modelo
    )


class SumarizacaoRequest(BaseModel):
    consulta: str
    textos: List[str]


class SumarizacaoResponse(BaseModel):
    resumo: str
    status: str


@controller.post('/doxxo/sumarizar')
async def sumarizar_conteudo(request: Request, conteudo_requisicao: SumarizacaoRequest) -> SumarizacaoResponse:
    estado = obter_estado(request)
    conteudo_completo = '\n\n'.join(conteudo_requisicao.textos)
    prompt = (f'Considere os seguintes termos de consulta: {conteudo_requisicao.consulta}.\nFaça um resumo conciso do seguinte conteúdo, com foco no contexto da consulta:\n\n{conteudo_completo}')

    url_ollama = configuracoes.URL_API_OLLAMA
    payload = {
        'model': 'llama3.1',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'stream': False
    }

    try:
        logger.info('Enviando solicitação de sumarização para o Ollama (Modelo: llama3.1)')
        response = await estado.cliente_http.post(url_ollama, json=payload)
        response.raise_for_status()
        resultado = response.json()
        return {
            'resumo': resultado.get('message', {}).get('content', ''),
            'status': 'sucesso'
        }
    except httpx.HTTPStatusError as e:
        logger.error(f'Erro na API Ollama: {e}')
        raise HTTPException(status_code=500, detail='Erro ao processar sumarização no Ollama')
    except Exception as e:
        logger.error(f'Erro inesperado: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@controller.get('/doxxo/listar-conteudo')
async def listar_conteudo(request: Request):
    estado = obter_estado(request)
    nomes_colecoes = list(estado.colecoes_documentos.keys())
    documentos = {}
    for nome in nomes_colecoes:
        colecao = estado.colecoes_documentos[nome]
        documentos[nome] = colecao.listar_titulos_documentos()
    return documentos


@controller.get('/doxxo/listar-colecoes')
async def listar_colecoes(request: Request):
    estado = obter_estado(request)
    return {'colecoes': list(estado.colecoes_documentos.keys())}


@controller.get('/doxxo/listar-documentos')
async def listar_documentos(request: Request, nome_colecao: List[str] | None = Query(None)):
    estado = obter_estado(request)

    if not nome_colecao:
        nome_colecao = list(
            estado.colecoes_documentos.keys()
        )

    documentos = {
        nome: [] for nome in nome_colecao
    }

    for nome in nome_colecao:
        colecao = estado.colecoes_documentos[nome]
        documentos[nome] = colecao.listar_titulos_documentos()

    if not any(documentos.values()):
        raise HTTPException(status_code=404, detail='Nenhum documento encontrado para as coleções especificadas.')
    return documentos


@controller.get('/doxxo/documento')
async def exibir_documento(url_documento: str = Query(None)):
    with open(f'../{url_documento}', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)


@controller.get('/')
async def home():
    with open('./web/pagina_icms.html', 'r', encoding='utf-8') as arquivo:
        conteudo_html = arquivo.read()
    conteudo_html = conteudo_html.replace('TAG_INSERCAO_URL_API', configuracoes.URL_API)
    return HTMLResponse(content=conteudo_html, status_code=200)


@controller.get('/ref')
async def busca_referencias():
    with open('./web/pagina_referencias.html', 'r', encoding='utf-8') as arquivo:
        conteudo_html = arquivo.read()
    conteudo_html = conteudo_html.replace('TAG_INSERCAO_URL_API', configuracoes.URL_API)
    return HTMLResponse(content=conteudo_html, status_code=200)


@controller.get('/icms')
def busca_icms():
    with open('./web/pagina_icms.html', 'r', encoding='utf-8') as arquivo:
        conteudo_html = arquivo.read()
    conteudo_html = conteudo_html.replace('TAG_INSERCAO_URL_API', configuracoes.URL_API)
    return HTMLResponse(content=conteudo_html, status_code=200)