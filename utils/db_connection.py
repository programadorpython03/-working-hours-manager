from supabase import create_client, Client
from config import Config
import logging
import os
from functools import wraps

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_supabase_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            logger.debug(f"Supabase Response - Type: {type(response)}")
            logger.debug(f"Supabase Response - Content: {response}")
            return response
        except Exception as e:
            logger.error(f"Supabase Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class SupabaseClient:
    def __init__(self, url, key):
        self.client = create_client(url, key)
        
    @log_supabase_response
    def table(self, name):
        return self.client.table(name)

try:
    # Validação das variáveis de ambiente
    if not Config.SUPABASE_URL:
        logger.error("SUPABASE_URL não encontrada nas variáveis de ambiente")
        raise ValueError("SUPABASE_URL é obrigatória")
    
    if not Config.SUPABASE_KEY:
        logger.error("SUPABASE_KEY não encontrada nas variáveis de ambiente")
        raise ValueError("SUPABASE_KEY é obrigatória")

    logger.info("Tentando conectar ao Supabase...")
    
    # Criação do cliente Supabase com tratamento de erro
    supabase = SupabaseClient(
        url=Config.SUPABASE_URL,
        key=Config.SUPABASE_KEY
    )
    
    # Teste de conexão
    response = supabase.table('funcionarios').select('count').limit(1).execute()
    logger.info(f"Resposta do Supabase: {type(response)} - {response}")
    logger.info("Conexão com o Supabase estabelecida com sucesso")
except Exception as e:
    logger.error(f"Erro ao conectar com o Supabase: {str(e)}")
    raise

def get_supabase_data(response):
    """Função utilitária para extrair dados da resposta do Supabase"""
    logger.debug(f"Tipo da resposta: {type(response)}")
    logger.debug(f"Conteúdo da resposta: {response}")
    
    try:
        # Se for um dicionário
        if isinstance(response, dict):
            # Verifica se tem a chave 'data'
            if 'data' in response:
                data = response['data']
                logger.debug(f"Dados extraídos do dicionário: {data}")
                return data
            # Se não tiver a chave 'data', retorna o próprio dicionário
            logger.debug(f"Usando o dicionário completo como dados: {response}")
            return response
        
        # Se for um objeto com atributo data
        if hasattr(response, 'data'):
            data = response.data
            logger.debug(f"Dados extraídos do objeto: {data}")
            return data
        
        # Se for uma lista, retorna ela mesma
        if isinstance(response, list):
            logger.debug(f"Usando a lista como dados: {response}")
            return response
        
        logger.warning(f"Formato de resposta não reconhecido: {response}")
        return []
    except Exception as e:
        logger.error(f"Erro ao extrair dados da resposta: {str(e)}")
        return []
