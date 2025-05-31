from supabase import create_client
from config import Config
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Validação das variáveis de ambiente
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios no arquivo .env")

    # Criação do cliente Supabase com tratamento de erro
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # Teste de conexão
    supabase.table('funcionarios').select('count').limit(1).execute()
    logger.info("Conexão com o Supabase estabelecida com sucesso")
except Exception as e:
    logger.error(f"Erro ao conectar com o Supabase: {str(e)}")
    raise
