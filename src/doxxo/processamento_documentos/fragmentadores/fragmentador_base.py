from typing import List
from doxxo.processamento_documentos.models import Fragmento

class FragmentadorBase:
    def fragmentar(self, texto: str, info: dict, comprimento_max_fragmento: int, pagina: int | None = None) -> List[Fragmento]:
        raise NotImplementedError('Método fragmentar() não foi implementado para esta classe')
    