import unittest
from datetime import datetime, time, timedelta
import sys
import os

# Adiciona o diretório raiz ao path para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.calculadora_horas import calcular_horas

class TestCalculadoraHoras(unittest.TestCase):
    def test_horas_normais_simples(self):
        """Testa um dia de trabalho normal: 09:00 as 18:00 com 1h de almoco"""
        resultado = calcular_horas("09:00", "12:00", "13:00", "18:00")
        self.assertEqual(resultado['horas_normais'], 8.0)
        self.assertEqual(resultado['horas_extras'], 0.0)
        self.assertEqual(resultado['adicional_noturno'], 0.0)

    def test_horas_extras(self):
        """Testa trabalho ate depois das 20h (limite hardcoded)"""
        # 09:00 as 21:00 (12h totais) - 1h almoco = 11h trabalhadas
        # Ate 20h = 10h normais (mas o codigo limita a 10h? nao, o codigo diz min(trabalho, 12))
        # O codigo diz: horas_extras = saida - 20h. 
        # Saida 21h. 21h - 20h = 1h extra.
        resultado = calcular_horas("09:00", "12:00", "13:00", "21:00")
        self.assertEqual(resultado['horas_extras'], 1.0) 
        
    def test_adicional_noturno(self):
        """Testa trabalho ate depois das 22h"""
        # Saida 23:00. 
        # Extras: 23h - 20h = 3h extras.
        # Noturno: 23h - 22h = 1h noturna.
        resultado = calcular_horas("13:00", "18:00", "19:00", "23:00")
        self.assertEqual(resultado['horas_extras'], 3.0)
        self.assertEqual(resultado['adicional_noturno'], 1.0)

    def test_virada_de_dia(self):
        """Testa turno que começa num dia e termina no outro"""
        # 22:00 as 06:00 (8h)
        # Almoco 02:00 as 03:00
        # Total: 7h trabalhadas
        # Saida 06:00 (do dia seguinte)
        # 20h do dia anterior ate 06h do dia seguinte sao 10h de diferenca?
        # A logica do codigo original para extras eh: max(dt_saida - dt_20h, 0).
        # Se entrou 22h, dt_saida (06h dia seg) - dt_20h (20h dia ant) = 10h extras?
        # Isso parece excessivo se a jornada eh noturna padrão. Mas estamos testando o comportamento ATUAL.
        resultado = calcular_horas("22:00", "02:00", "03:00", "06:00")
        
        # Vamos verificar o comportamento atual
        # dt_saida (06:00 D+1)
        # dt_20h (20:00 D)
        # Diff = 10h. 
        # Então se espera 10h extras?
        # O codigo diz: horas_extras = max(dt_saida - dt_20h, 0)
        # Sim, retornará 10.0
        
        # E noturno?
        # dt_22h (22:00 D)
        # Diff = 8h.
        
        self.assertEqual(resultado['horas_extras'], 10.0)
        self.assertEqual(resultado['adicional_noturno'], 8.0)

if __name__ == '__main__':
    unittest.main()
