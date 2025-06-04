from supabase import create_client, Client
from config import Config
import logging
import os

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    supabase: Client = create_client(
        supabase_url=Config.SUPABASE_URL,
        supabase_key=Config.SUPABASE_KEY
    )
    
    # Teste de conexão
    supabase.table('funcionarios').select('count').limit(1).execute()
    logger.info("Conexão com o Supabase estabelecida com sucesso")
except Exception as e:
    logger.error(f"Erro ao conectar com o Supabase: {str(e)}")
    raise

def get_supabase_data(response):
    """Função utilitária para extrair dados da resposta do Supabase"""
    if isinstance(response, dict):
        return response.get('data', [])
    return response.data if hasattr(response, 'data') else []
