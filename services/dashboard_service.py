from datetime import datetime, timedelta
from utils.db_connection import supabase, get_supabase_data
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    @staticmethod
    def get_dashboard_data(mes_str=None, funcionario_id=None):
        """
        Recupera todos os dados necessários para o dashboard.
        """
        try:
            # 1. Definição do período (Mês)
            if not mes_str:
                mes_str = datetime.now().strftime('%Y-%m')
            
            mes_dt = datetime.strptime(mes_str, '%Y-%m')
            inicio_mes = mes_dt.replace(day=1)
            
            # Cálculo do último dia do mês
            if mes_dt.month == 12:
                fim_mes = mes_dt.replace(year=mes_dt.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim_mes = mes_dt.replace(month=mes_dt.month + 1, day=1) - timedelta(days=1)

            # 2. Busca registros do mês
            query = supabase.table('registros_horas').select('*').gte('data_trabalho', inicio_mes.isoformat()).lte('data_trabalho', fim_mes.isoformat())
            if funcionario_id:
                query = query.eq('funcionario_id', funcionario_id)
            registros = get_supabase_data(query.execute())

            # 3. Busca funcionários ativos
            funcionarios = get_supabase_data(
                supabase.table('funcionarios').select('*').eq('ativo', True).execute()
            )

            # 4. Busca registros recentes (últimos 5)
            # Nota: Registros recentes globais ou filtrados? O original buscava global, mas vamos manter coerencia se tiver filtro
            # O original fazia: .limit(5), sem filtro de ID no recentes? 
            # Revisitando app.py:
            # query = ... .limit(5)
            # Parece que era independente do filtro de mes, mas e do funcionario? Nao tinha filtro na query recentes original.
            # Vamos manter fiel ao original por enquanto, mas melhorar se possivel.
            # O original NAO filtrava recentes por funcionario_id.
            
            registros_recentes_query = supabase.table('registros_horas').select('*, funcionarios(nome)').order('data_trabalho', desc=True).limit(5)
            # Se quiser aplicar filtro também nos recentes (faz sentido):
            if funcionario_id:
                 registros_recentes_query = registros_recentes_query.eq('funcionario_id', funcionario_id)
                 
            registros_recentes = get_supabase_data(registros_recentes_query.execute())

            # Processa datas dos recentes
            for registro in registros_recentes:
                if isinstance(registro.get('data_trabalho'), str):
                    registro['data_trabalho'] = datetime.strptime(registro['data_trabalho'], '%Y-%m-%d')

            # 5. Prepara dados para o Gráfico Diário
            dias_no_mes = (fim_mes - inicio_mes).days + 1
            labels_diario = [(inicio_mes + timedelta(days=i)).strftime('%d/%m') for i in range(dias_no_mes)]
            
            # Inicializa arrays com zeros
            dados_diarios = {
                'normais': [0] * dias_no_mes,
                'extras': [0] * dias_no_mes,
                'noturno': [0] * dias_no_mes
            }

            for registro in registros:
                if isinstance(registro.get('data_trabalho'), str):
                    data = datetime.strptime(registro['data_trabalho'], '%Y-%m-%d')
                else:
                    data = registro['data_trabalho']
                
                dia_index = (data - inicio_mes).days
                if 0 <= dia_index < dias_no_mes:
                    dados_diarios['normais'][dia_index] += registro.get('horas_normais', 0)
                    dados_diarios['extras'][dia_index] += registro.get('horas_extras', 0)
                    dados_diarios['noturno'][dia_index] += registro.get('adicional_noturno', 0)

            grafico_data = {
                'labels': labels_diario,
                'horas_normais': dados_diarios['normais'],
                'horas_extras': dados_diarios['extras'],
                'adicional_noturno': dados_diarios['noturno']
            }

            # 6. Prepara dados para o Gráfico Mensal (últimos 6 meses)
            grafico_mensal = DashboardService._gerar_grafico_mensal(mes_dt, funcionario_id)

            # 7. Totais
            totais = {
                'funcionarios': len(funcionarios),
                'registros': len(registros),
                'horas_extras': sum(r.get('horas_extras', 0) for r in registros)
            }

            return {
                'mes': mes_str,
                'funcionario_id': funcionario_id,
                'funcionarios': funcionarios,
                'totais': totais,
                'registros_recentes': registros_recentes,
                'grafico_data': grafico_data,
                'grafico_mensal': grafico_mensal
            }

        except Exception as e:
            logger.error(f"Erro no serviço de dashboard: {str(e)}")
            raise

    @staticmethod
    def _gerar_grafico_mensal(mes_referencia, funcionario_id):
        meses = []
        dados = {
            'normais': [],
            'extras': [],
            'noturno': []
        }

        for i in range(5, -1, -1):
            data_ref = mes_referencia - timedelta(days=30*i) # Aproximacao de mes
            # Ajuste melhor para pegar o mes correto
            # Se for hoje fev/2024. 
            # i=0 -> fev. i=1 -> jan.
            # Logica original usava dias=30 fixe, o que causa drift. Mas vamos manter ou corrigir?
            # Melhor corrigir levemente a logica de "meses atras"
            
            # Vamos fazer direito:
            year = mes_referencia.year
            month = mes_referencia.month - i
            while month <= 0:
                month += 12
                year -= 1
            
            data_loop = datetime(year, month, 1)
            
            inicio_mes = data_loop
            if data_loop.month == 12:
                fim_mes = datetime(data_loop.year + 1, 1, 1) - timedelta(days=1)
            else:
                fim_mes = datetime(data_loop.year, data_loop.month + 1, 1) - timedelta(days=1)

            meses.append(data_loop.strftime('%m/%Y'))

            query = supabase.table('registros_horas').select('*').gte('data_trabalho', inicio_mes.isoformat()).lte('data_trabalho', fim_mes.isoformat())
            if funcionario_id:
                query = query.eq('funcionario_id', funcionario_id)
            registros_mes = get_supabase_data(query.execute())

            dados['normais'].append(sum(r.get('horas_normais', 0) for r in registros_mes))
            dados['extras'].append(sum(r.get('horas_extras', 0) for r in registros_mes))
            dados['noturno'].append(sum(r.get('adicional_noturno', 0) for r in registros_mes))
        
        return {
            'labels': meses,
            'horas_normais': dados['normais'],
            'horas_extras': dados['extras'],
            'adicional_noturno': dados['noturno']
        }
