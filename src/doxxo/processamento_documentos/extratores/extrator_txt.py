import os
from typing import List
from doxxo.processamento_documentos.models import Fragmento
from doxxo.processamento_documentos.extratores.extrator_base import ExtratorBase
from doxxo.processamento_documentos.fragmentadores.fragmentador_texto import FragmentadorTexto
from doxxo.processamento_documentos.fragmentadores.fragmentador_articulado import FragmentadorArticulado

class ExtratorTexto(ExtratorBase):
    def __init__(self, url_base: str):
        self.url_base = url_base
        self.fragmentador = FragmentadorTexto()
        self.fragmentador_articulado = FragmentadorArticulado()

    def extrair(self, rotulo: str, info: dict, comprimento_max_fragmento: int) -> List[Fragmento]:
        url_arquivo = os.path.join(self.url_base, info['url'])
        with open(url_arquivo, 'r', encoding='utf-8') as arq:
            texto = arq.read()
        if info.get('texto_articulado'):
            fragmentos = self.fragmentador_articulado.fragmentar(texto, info, comprimento_max_fragmento)
        else:
            fragmentos = self.fragmentador.fragmentar(texto, info, comprimento_max_fragmento)
            
        # adiciona tag aos fragmentos
        for idx, fragmento in enumerate(fragmentos, start=1):
            fragmento.metadata['tag_fragmento'] = f'{rotulo}:{idx}'
        return fragmentos
