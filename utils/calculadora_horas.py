from datetime import datetime, timedelta, time

def to_time(hhmm):
    return datetime.strptime(hhmm, "%H:%M").time() if hhmm else None

def calcular_horas(entrada, almoco_saida, almoco_volta, saida):
    entrada = to_time(entrada)
    saida = to_time(saida)
    almoco_saida = to_time(almoco_saida)
    almoco_volta = to_time(almoco_volta)

    dt_hoje = datetime.today()
    dt_entrada = datetime.combine(dt_hoje, entrada)
    dt_saida = datetime.combine(dt_hoje, saida)
    # Se a saída for menor ou igual à entrada, considera que passou da meia-noite
    if saida and entrada and dt_saida <= dt_entrada:
        dt_saida += timedelta(days=1)

    total = dt_saida - dt_entrada

    intervalo = timedelta()
    if almoco_saida and almoco_volta:
        dt_almoco_saida = datetime.combine(dt_hoje, almoco_saida)
        dt_almoco_volta = datetime.combine(dt_hoje, almoco_volta)
        # Se o retorno do almoço for menor que a saída para o almoço, passou da meia-noite
        if dt_almoco_volta <= dt_almoco_saida:
            dt_almoco_volta += timedelta(days=1)
        intervalo = dt_almoco_volta - dt_almoco_saida

    trabalho_liquido = total - intervalo

    horas_normais = min(trabalho_liquido, timedelta(hours=12))
    # Ajuste para considerar horas extras e adicional noturno após a meia-noite
    dt_20h = datetime.combine(dt_hoje, time(20, 0))
    dt_22h = datetime.combine(dt_hoje, time(22, 0))
    if dt_saida <= dt_entrada:
        dt_20h += timedelta(days=1)
        dt_22h += timedelta(days=1)
    horas_extras = max(dt_saida - dt_20h, timedelta(0))
    adicional_noturno = max(dt_saida - dt_22h, timedelta(0))

    def to_decimal(td):
        return round(td.total_seconds() / 3600, 2)

    return {
        'horas_normais': to_decimal(horas_normais),
        'horas_extras': to_decimal(horas_extras),
        'adicional_noturno': to_decimal(adicional_noturno)
    }
