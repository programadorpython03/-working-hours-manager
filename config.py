import os
from dotenv import load_dotenv
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis do .env apenas em desenvolvimento
if os.path.exists('.env'):
    load_dotenv()
    logger.info("Carregando variáveis do arquivo .env")

class Config:
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret')

    # Log das variáveis (sem mostrar valores sensíveis)
    logger.info(f"SUPABASE_URL configurada: {'Sim' if SUPABASE_URL else 'Não'}")
    logger.info(f"SUPABASE_KEY configurada: {'Sim' if SUPABASE_KEY else 'Não'}")
    logger.info(f"SECRET_KEY configurada: {'Sim' if SECRET_KEY else 'Não'}")
