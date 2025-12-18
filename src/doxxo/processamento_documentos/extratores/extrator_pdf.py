import os
from typing import List
from pypdf import PdfReader
from doxxo.processamento_documentos.models import Fragmento
from doxxo.processamento_documentos.extratores.extrator_base import ExtratorBase
from doxxo.processamento_documentos.fragmentadores.fragmentador_texto import FragmentadorTexto

class ExtratorPdf(ExtratorBase):
    def __init__(self, url_base: str):
        self.url_base = url_base
        self.fragmentador = FragmentadorTexto()

    def extrair(self, rotulo: str, info: dict, comprimento_max_fragmento: int) -> List[Fragmento]:
        url_arquivo = os.path.join(self.url_base, info['url'])
        arquivo = PdfReader(url_arquivo)
        fragmentos: List[Fragmento] = []
        for idx, pagina in enumerate(arquivo.pages, start=1):
            texto = pagina.extract_text() or ''
            frags = self.fragmentador.fragmentar(texto, info, comprimento_max_fragmento, page=idx)
            for frag in frags:
                idx_fragmento = len(fragmentos) + 1
                frag.metadata['tag_fragmento'] = f'{rotulo}:{idx_fragmento}'
                fragmentos.append(frag)
        return fragmentos
