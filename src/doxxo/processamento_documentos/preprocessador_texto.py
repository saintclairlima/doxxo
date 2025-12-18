import re
import unicodedata

class PreprocessadorTexto:
    """Normaliza strings: remove acentos, deixa minúsculas e normaliza para snake-like."""
    @staticmethod
    def normalizar_string(s):
        # Normaliza e remove os acentos (diacríticos)
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')    
        # Converte para letras minúsculas
        s = s.lower()    
        # Substitui caracteres não alfanuméricos por underscores (_)
        s = re.sub(r'[^a-z0-9]+', '_', s)    
        # Remove underscores duplicados e também os do início e do fim
        s = re.sub(r'_+', '_', s).strip('_')    
        return s