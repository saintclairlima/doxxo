from typing import List
from doxxo.processamento_documentos.models import Fragmento

class ExtratorBase:
    def extrair(self, rotulo: str, info: dict, max_words: int) -> List[Fragmento]:
        raise NotImplementedError('Método extrair() não foi implementado para esta classe')