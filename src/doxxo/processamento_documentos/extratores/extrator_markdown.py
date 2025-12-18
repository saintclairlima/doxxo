import os
from typing import List
from doxxo.processamento_documentos.models import Fragmento
from doxxo.processamento_documentos.extratores.extrator_base import ExtratorBase
from doxxo.processamento_documentos.fragmentadores.fragmentador_markdown import FragmentadorMarkdown

class ExtratorMarkdown(ExtratorBase):
    def __init__(self, url_base: str):
        self.urlBase = url_base
        self.fragmentador = FragmentadorMarkdown()

    def extrair(self, rotulo: str, info: dict, comprimento_max_fragmento: int) -> List[Fragmento]:
        path = os.path.join(self.urlBase, info['url'])
        with open(path, 'r', encoding='utf-8') as f:
            md = f.read()
        fragments = self.fragmentador.fragmentar(md, info, comprimento_max_fragmento)
        for idx, frag in enumerate(fragments, start=1):
            frag.metadata['tag_fragmento'] = f'{rotulo}:{idx}'
        return fragments
