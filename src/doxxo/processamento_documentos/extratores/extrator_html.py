import os
from typing import List
from bs4 import BeautifulSoup
from doxxo.processamento_documentos.models import Fragmento
from doxxo.processamento_documentos.extratores.extrator_base import ExtratorBase
from doxxo.processamento_documentos.fragmentadores.fragmentador_texto import FragmentadorTexto

class ExtratorHtml(ExtratorBase):
    def __init__(self, url_base: str):
        self.url_base = url_base
        self.fragmentador = FragmentadorTexto()
    
    def extrair(self, rotulo: str, info: dict, comprimento_max_fragmento: int) -> List[Fragmento]:
        url_arquivo = os.path.join(self.url_base, info['url'])
        with open(url_arquivo, 'r', encoding='utf-8') as arq:
            conteudo_html = arq.read()

        pagina_html = BeautifulSoup(conteudo_html, 'html.parser')
        tags = pagina_html.find_all()
        texto = '\n'.join([tag.get_text() for tag in tags])
        
        fragmentos = self.fragmentador.fragmentar(texto, info, comprimento_max_fragmento)
        for idx in range(len(fragmentos)): fragmentos[idx]['tag_fragmento'] = f'{rotulo}:{idx+1}'
        return fragmentos
