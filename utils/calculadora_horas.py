from datetime import datetime, timedelta, time

def to_time(hhmm):
    return datetime.strptime(hhmm, "%H:%M").time() if hhmm else None

def calcular_horas(entrada, almoco_saida, almoco_volta, saida):
    entrada = to_time(entrada)
    saida = to_time(saida)
    almoco_saida = to_time(almoco_saida)
    almoco_volta = to_time(almoco_volta)

    total = datetime.combine(datetime.today(), saida) - datetime.combine(datetime.today(), entrada)

    intervalo = timedelta()
    if almoco_saida and almoco_volta:
        intervalo = datetime.combine(datetime.today(), almoco_volta) - datetime.combine(datetime.today(), almoco_saida)

    trabalho_liquido = total - intervalo

    horas_normais = min(trabalho_liquido, timedelta(hours=12))
    horas_extras = max(datetime.combine(datetime.today(), saida) - datetime.combine(datetime.today(), time(20, 0)), timedelta(0))
    adicional_noturno = max(datetime.combine(datetime.today(), saida) - datetime.combine(datetime.today(), time(22, 0)), timedelta(0))

    def to_decimal(td):
        return round(td.total_seconds() / 3600, 2)

    return {
        'horas_normais': to_decimal(horas_normais),
        'horas_extras': to_decimal(horas_extras),
        'adicional_noturno': to_decimal(adicional_noturno)
    }
