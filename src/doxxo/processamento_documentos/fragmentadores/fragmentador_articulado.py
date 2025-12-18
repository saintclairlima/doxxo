from typing import List
from doxxo.processamento_documentos.fragmentadores.fragmentador_base import FragmentadorBase
from doxxo.processamento_documentos.models import Fragmento

class FragmentadorArticulado(FragmentadorBase):
    """
    Fragmenta textos articulados (leis). Mantém o caput em todos os fragmentos do artigo.
    Heurísticas baseadas no seu código original.
    """
    
    def fragmentar(self, texto: str, info: dict, comprimento_max_fragmento: int, pagina: int | None = None) -> List[Fragmento]:
        '''Processa textos legais, divididos em artigos. Mantém o Caput dos artigos em cada um dos fragmentos.'''
        texto = texto.replace('\n', ' ').replace('\t', ' ')
        while '  ' in texto: texto = texto.replace('  ', ' ')
        texto = texto.replace(' Art. ', '\nArt. ')
        
        for num in range(1, 10):
                texto = texto.replace(f'Art. {num}º', f'Art. {num}.')
                texto = texto.replace(f'art. {num}º', f'art. {num}.')
                texto = texto.replace(f'§ {num}º', f'§ {num}.')
                
        texto = texto.split('\n')
        while '' in texto: texto.remove('')
        
        artigos = []
        for art in texto:
            item = art.split(' ')
            qtd_palavras = len(item)
            if qtd_palavras > comprimento_max_fragmento:
                item = (
                        art.replace('. §', '.\n§')
                        .replace('; §', ';\n§')
                        .replace(': §', ':\n§')
                        .replace(';', '\n')
                        .replace(':', '\n')
                        .replace('\n ', '\n')
                        .replace(' \n', '\n')
                        .split('\n')
                    )
                caput = item[0]
                fragmento_artigo = '' + caput
                # AFAZER: considerar casos em que, mesmo após divisão das
                # partes do artigo, haja alguma com mais palavras que o compr. máximo
                for i in range(1, len(item)):
                    if len(fragmento_artigo.split(' ')) + len(item[i].split(' ')) <= comprimento_max_fragmento:
                        fragmento_artigo = fragmento_artigo + ' ' + item[i]
                    else:
                        artigos.append(fragmento_artigo)
                        fragmento_artigo = '' + caput + ' ' + item[i]
                artigos.append(fragmento_artigo)
            else:
                artigos.append(art)
        
        fragmentos = []
        titulos = []
        for artigo in artigos:
            tit = artigo.split('. ')[1]
            titulos.append(tit)
            metadados = {
                'titulo': f'{info["titulo"]}',
                'subtitulo': f'Art. {tit} - {titulos.count(tit)}',
                'autor': f'{info["autor"]}',
                'fonte': f'{info["fonte"]}#Art_{tit}'
            }
            fragmentos.append(Fragmento(page_content=artigo, metadata=metadados))
        return fragmentos
