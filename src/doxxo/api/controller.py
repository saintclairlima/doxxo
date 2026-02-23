import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d \t %(message)s"
)
logger = logging.getLogger(__name__)

logger.info('Importando bibliotecas e módulos necessários...')
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from typing import List
from fastapi.responses import HTMLResponse
import httpx
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from doxxo.conteudo.banco_vetorial import BancoVetorial
from doxxo.configuracoes.configuracoes import configuracoes
from doxxo.conteudo.reranqueador import ReRanqueador

logger.info('Carregando banco vetorial e preparando coleções...')
banco_vetorial = BancoVetorial(
    url_base_documentos=configuracoes.URL_DOCUMENTOS,
    url_banco_vetorial=configuracoes.URL_BANCO_VETORIAL
)

colecoes = defaultdict(list)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Carregando gerador de embeddings...")
    gerador_embeddings = banco_vetorial.carregar_gerador_embeddings(
        nome_modelo=configuracoes.MODELO_EMBEDDINGS
    )

    logger.info("Carregando ReRanqueador...")
    reranker = ReRanqueador(
        nome_modelo=configuracoes.MODELO_RERANKEAMENTO
    )

    logger.info("Carregando interface ChromaDB...")
    for nome_colecao in banco_vetorial.listar_nomes_colecoes():
        colecoes[nome_colecao] = banco_vetorial.conectar_colecao_documentos(
            url_banco=configuracoes.URL_BANCO_VETORIAL,
            nome_colecao=nome_colecao,
            gerador_embeddings=gerador_embeddings,
            criar_colecao_automaticamente=False
        )

    cliente_http = httpx.AsyncClient(timeout=60.0)

    app.state.gerador_embeddings = gerador_embeddings
    app.state.reranker = reranker
    app.state.colecoes_documentos = colecoes
    app.state.cliente_http = cliente_http

    logger.info("API inicializada")

    yield

    # Exemplo de código de SHUTDOWN (se necessário)
    logger.info("Desligando e liberando recursos...")
    await cliente_http.aclose()
    if gerador_embeddings and hasattr(gerador_embeddings.modelo, 'to'):
        gerador_embeddings.modelo.to('cpu') 
        del gerador_embeddings.modelo
    if reranker and hasattr(reranker.modelo, 'to'):
        reranker.modelo.to('cpu') 
        del reranker.modelo
    logger.info("Recursos liberados com sucesso.")

logger.info('Instanciando a api (FastAPI)...')
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
    return {"status": "ok"}

@controller.get('/doxxo/consulta')
async def consultar_documentos(request: Request, pergunta: str, colecao: List[str]| None = Query(None), num_resultados: int = 5, reranquear: bool=True):

    if colecao is None or len(colecao) == 0:
        colecoes = list(request.app.state.colecoes_documentos.keys())
    else:
        colecoes = colecao

    resultado_completo = []
    
    for colecao in colecoes:
        resultado = request.app.state.colecoes_documentos[colecao].consultar_documentos(
            termos_de_consulta=pergunta, 
            num_resultados=num_resultados
        )

        ids = resultado["ids"][0]
        docs = resultado["documents"][0]
        metas = resultado["metadatas"][0]
        dists = resultado["distances"][0]

        for i in range(len(ids)):
            resultado_completo.append({
                "id": ids[i],
                "document": docs[i],
                "metadata": {**metas[i], 'colecao': colecao},
                "distance": dists[i],
                "score_reranqueamento": None
            })

    if reranquear:
        resultado_completo = request.app.state.reranker.reranquear(consulta=pergunta, documentos=resultado_completo)
    else:
        resultado_completo.sort(key=lambda x: x["distance"])

    return resultado_completo[:num_resultados]

class SumarizacaoRequest(BaseModel):
    consulta: str
    textos: List[str]

@controller.post('/doxxo/sumarizar')
async def sumarizar_conteudo(request: Request, conteudo_requisicao: SumarizacaoRequest):
    conteudo_completo = '\n\n'.join(conteudo_requisicao.textos)
    prompt = f"Considere os seguintes termos de consulta: {conteudo_requisicao.consulta}.\nFaça um resumo conciso do seguinte conteúdo, com foco no contexto da consulta:\n\n{conteudo_completo}"

    url_ollama = configuracoes.URL_API_OLLAMA
    client = request.app.state.cliente_http
    payload = {
        "model": "llama3.1",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        logger.info(f"Enviando solicitação de sumarização para o Ollama (Modelo: llama3.1)")
        response = await client.post(url_ollama, json=payload)
        response.raise_for_status()
        
        resultado = response.json()
        return {
            "resumo": resultado.get("message", {}).get("content", ""),
            "status": "sucesso"
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"Erro na API Ollama: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar sumarização no Ollama")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@controller.get('/doxxo/documento')
async def exibir_documento(url_documento: str = Query(None)):
    with open(f'../{url_documento}', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)
    
@controller.get('/')
async def home():
    with open(f'./web/pagina.html', 'r', encoding='utf-8') as arquivo:
        conteudo_html = arquivo.read()
        conteudo_html = conteudo_html.replace("TAG_INSERCAO_URL_API", configuracoes.URL_API)
    return HTMLResponse(content=conteudo_html, status_code=200)

@controller.get('/doxxo')
async def pagina_busca():
    with open(f'./web/pagina.html', 'r', encoding='utf-8') as arquivo:
        conteudo_html = arquivo.read()
        conteudo_html = conteudo_html.replace("TAG_INSERCAO_URL_API", configuracoes.URL_API)
    return HTMLResponse(content=conteudo_html, status_code=200)