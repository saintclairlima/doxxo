import logging
from typing import Dict, List
from doxxo.processamento_documentos.models import Fragmento
from doxxo.processamento_documentos.preprocessador_texto import PreprocessadorTexto
from doxxo.processamento_documentos.extratores.extrator_txt import ExtratorTexto
from doxxo.processamento_documentos.extratores.extrator_pdf import ExtratorPdf
from doxxo.processamento_documentos.extratores.extrator_html import ExtratorHtml
from doxxo.processamento_documentos.extratores.extrator_markdown import ExtratorMarkdown
from doxxo.processamento_documentos.fragmentadores.fragmentador_articulado import FragmentadorArticulado
from doxxo.processamento_documentos.fragmentadores.fragmentador_texto import FragmentadorTexto

logger = logging.getLogger(__name__)

class FragmentadorDocumentos:
    def __init__(self, url_base: str, comprimento_max_fragmento: int=300):
        self.url_base = url_base
        self.comprimento_max_fragmento = comprimento_max_fragmento
        self.preprocessador = PreprocessadorTexto()

        # extractors by extension
        self.extratores = {
            'txt': ExtratorTexto(url_base),
            'pdf': ExtratorPdf(url_base),
            'html': ExtratorHtml(url_base),
            'htm': ExtratorHtml(url_base),
            'md': ExtratorMarkdown(url_base),
        }

        # fragmenters by 'mode'
        self.fragmentador_texto = FragmentadorTexto()
        self.fragmentador_articulado = FragmentadorArticulado()

    def _definir_extrator(self, url: str) -> ExtratorTexto | ExtratorPdf | ExtratorHtml | ExtratorMarkdown | None:
        extensao = url.split('.')[-1].lower()
        return self.extratores.get(extensao)

    def extrair_fragmentos_indice_arquivos(self, indice_documentos: Dict[str, dict] | None = None, comprimento_max_fragmento: int | None = None) -> List[Fragmento]:
        if indice_documentos is None:
            logger.info("Não foi fornecido um índice de documentos. Retornando lista vazia.")
            return []

        comprimento_max_fragmento = comprimento_max_fragmento or self.comprimento_max_fragmento
        todos_fragmentos: List[Fragmento] = []

        for rotulo, info in indice_documentos.items():
            logger.info(f"Processando {rotulo}")
            url = info.get('url', '')
            extrator = self._definir_extrator(url)
            if extrator is None:
                logger.warning(f"Não há extrator definido para o tipo de documento de {url} (rótulo={rotulo}). Ignorando arquivo.")
                continue

            fragmentos = extrator.extrair(rotulo, info, comprimento_max_fragmento)
            # Se for texto articulado, refazer fragmentação, utilizando o fragmentador de texto articulado
            if info.get('texto_articulado'):
                # re-fragment using legal fragmenter if extractor returned whole text fragments
                frags_reprocessed = []
                for frag in fragmentos:
                    frags_reprocessed.extend(self.fragmentador_articulado.fragmentar(frag.page_content, info, comprimento_max_fragmento))
                fragmentos = frags_reprocessed

            todos_fragmentos.extend(fragmentos)

        return todos_fragmentos
