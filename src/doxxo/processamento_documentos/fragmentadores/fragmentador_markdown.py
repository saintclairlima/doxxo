from typing import List

from doxxo.processamento_documentos.models import Fragmento
from doxxo.processamento_documentos.fragmentadores.fragmentador_base import FragmentadorBase
from doxxo.processamento_documentos.preprocessador_texto import PreprocessadorTexto

class FragmentadorMarkdown(FragmentadorBase):
    def gerar_fragmentos(self, texto: str, info: dict, comprimento_max_fragmento: int, pagina: int | None = None) -> List[Fragmento]:
        """
        Divide um texto Markdown em fragmentos com tamanho máximo de palavras, mantendo a estrutura de títulos.
        
        Args:
            texto: Texto em formato Markdown.
            comprimento_max_fragmento: Número máximo de palavras por fragmento.
        
        Returns:
            Lista de fragmentos como strings.
        """
        linhas = [linha for linha in texto.splitlines() if linha.strip()]
        
        fragmentos = []
        fragmento = ''
        titulos = []
        nivel_titulo_base = 1

        for linha in linhas:
            elementos = linha.split(' ')
            if elementos[0].startswith('#'):
                if fragmento:
                    cabecalho = '\n'.join(titulos) + '\n'
                    fragmentos.append({'titulos': titulos.copy(), 'conteudo': cabecalho + fragmento})
                    fragmento = ''
                nivel_titulo = len(elementos[0])
                if nivel_titulo_base >= nivel_titulo:
                    titulos = titulos[:nivel_titulo - 1]            
                nivel_titulo_base = nivel_titulo
                titulos.append(' '.join(elementos[1:]))
            else:
                # Não é título
                cabecalho = '\n'.join(titulos) + '\n'
                texto_possivel_fragmento = cabecalho + fragmento + f'{linha}\n'
                if len(texto_possivel_fragmento.replace('\n', ' ').split(' ')) <= comprimento_max_fragmento:
                    # Não extrapola tamanho máximo
                    fragmento += f'{linha}\n'
                else:
                    # Extrapola tamanho máximo
                    fragmentos.append({'titulos': titulos.copy(), 'conteudo': cabecalho + fragmento})
                    fragmento = f'{linha}\n'

        if fragmento:
            cabecalho = '\n'.join(titulos) + '\n'
            fragmentos.append({'titulos': titulos.copy(), 'conteudo': cabecalho + fragmento})
        
        return fragmentos
    
    def fragmentar(self, texto: str, info: dict, comprimento_max_fragmento: int, profund_maxima: int=3) -> List[str]:
        fragmentos_titulos = self.gerar_fragmentos(texto=texto, info=info, comprimento_max_fragmento=comprimento_max_fragmento)

        fragmentos = []
        titulos = []
        for frag_titulo in fragmentos_titulos:
            tit = frag_titulo['titulos'][:profund_maxima][-1]
            titulos.append(tit)
            metadados =  {
                'titulo': f'{info["titulo"]}',
                'subtitulo': f'{tit} - {titulos.count(tit)}',
                'autor': f'{info["autor"]}',
                'fonte': f'{info["fonte"]}#{PreprocessadorTexto.normalizar_string(tit)}'
            }
            fragmentos.append(Fragmento(page_content=frag_titulo['conteudo'], metadata=metadados))
        return fragmentos