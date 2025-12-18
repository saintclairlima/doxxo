from doxxo.conteudo.banco_vetorial import BancoVetorial
from doxxo.processamento_documentos.fragmentador import FragmentadorDocumentos as FD
from doxxo.configuracoes.configuracoes import configuracoes
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="✨ %(asctime)s [%(levelname)s] %(filename)s:%(lineno)d \t %(message)s"
)

url_base=configuracoes.URL_DOCUMENTOS

fd = FD(url_base=url_base)

banco_vetorial = BancoVetorial(
    url_base_documentos=url_base,
    url_banco_vetorial=configuracoes.URL_BANCO_VETORIAL
)

gerador_embeddings = banco_vetorial.carregar_gerador_embeddings(
    nome_modelo=configuracoes.MODELO_EMBEDDINGS,
    instrucao=configuracoes.INSTRUCAO_MODELO_EMBEDDINGS
)

with open(f'{url_base}/indices_colecoes.json', 'r', encoding='utf-8') as arq: indices = json.load(arq)
descritor_colecoes_geradas = []
for indice_info in indices:
    nome_colecao = indice_info['colecao']
    indice = indice_info['indice_documentos']
    logger.info(f'Processando índice da colecao: {nome_colecao}')

    frags_documentos = fd.extrair_fragmentos_indice_arquivos(indice, comprimento_max_fragmento=configuracoes.COMPRIMENTO_MAXIMO_FRAGMENTO)

    colecao_nova = banco_vetorial.criar_nova_colecao(
        nome_colecao=nome_colecao,
        documentos=frags_documentos,
        gerador_embeddings=gerador_embeddings,
        hsnw_space=configuracoes.HNSW_SPACE
    )
    
    descritor_colecoes_geradas.append({
        "uuid": str(uuid4()),
        "nome": nome_colecao,
        "quantidade_max_palavras_por_documento": configuracoes.COMPRIMENTO_MAXIMO_FRAGMENTO,
        "hnsw:space": configuracoes.HNSW_SPACE,
        "funcao_embeddings": {"nome_modelo": configuracoes.MODELO_EMBEDDINGS, "instrucao": configuracoes.INSTRUCAO_MODELO_EMBEDDINGS}
    })

try:
    with open(f'{configuracoes.URL_BANCO_VETORIAL}/descritor.json', 'r', encoding='utf-8') as arq:
        descritor_banco_vetorial = json.load(arq)
except FileNotFoundError:
    descritor_banco_vetorial = {'nome_banco_vetorial': configuracoes.URL_BANCO_VETORIAL.split('/')[-1], 'colecoes': []}

descritor_banco_vetorial['colecoes'].extend(descritor_colecoes_geradas)
with open(f'{configuracoes.URL_BANCO_VETORIAL}/descritor.json', 'w', encoding='utf-8') as arq:
    json.dump(descritor_banco_vetorial, arq, ensure_ascii=False, indent=4)