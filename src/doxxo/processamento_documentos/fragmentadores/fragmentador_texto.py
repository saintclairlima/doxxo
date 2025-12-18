from typing import List
from doxxo.processamento_documentos.fragmentadores.fragmentador_base import FragmentadorBase
from doxxo.processamento_documentos.models import Fragmento

class FragmentadorTexto(FragmentadorBase):

    def fragmentar(self, texto: str, info: dict, comprimento_max_fragmento: int, pagina: int | None = None) -> List[Fragmento]:
        texto = texto.replace('\n', ' ').replace('\t', ' ')
        while '  ' in texto: texto = texto.replace('  ', ' ')
        
        if len(texto.split(' ')) <= comprimento_max_fragmento:
            metadados = {
                'titulo': f'{info["titulo"]}',
                'subtitulo':
                    f'Página {pagina} - Fragmento 1' if pagina
                    else f'Fragmento 1',
                'autor': f'{info["autor"]}',
                'fonte': f'{info["fonte"]}',
            }
            if pagina: metadados['pagina'] = pagina
            fragmento = Fragmento(page_content=texto, metadata=metadados)            
            return [fragmento]
            
        linhas = texto.replace('. ', '.\n')
        linhas = linhas.split('\n')
        while '' in linhas: linhas.remove('')
        
        fragmentos = []
        texto_fragmento = ''
        for idx in range(len(linhas)):
            if len(texto_fragmento.split(' ')) + len(linhas[idx].split(' ')) < comprimento_max_fragmento:
                texto_fragmento += ' ' + linhas[idx]
            else:
                metadados = {
                    'titulo': f'{info["titulo"]}',
                    'subtitulo':
                        f'Página {pagina} - Fragmento {len(fragmentos)+1}' if pagina
                        else f'Fragmento {len(fragmentos)+1}',
                    'autor': f'{info["autor"]}',
                    'fonte': f'{info["fonte"]}',
                }
                if pagina: metadados['pagina'] = pagina
                
                fragmentos.append(Fragmento(page_content=texto_fragmento, metadata=metadados))
                texto_fragmento = ''
            
        return fragmentos