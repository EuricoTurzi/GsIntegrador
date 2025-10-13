"""
Template filters customizados para o app de rotas
"""
from django import template

register = template.Library()


@register.filter
def format_duration(hours):
    """
    Formata duração em horas para exibição amigável
    
    Exemplos:
        0.13 horas -> "8 min"
        0.5 horas -> "30 min"
        1.5 horas -> "1h 30min"
        3.25 horas -> "3h 15min"
    """
    if not hours:
        return "0 min"
    
    hours = float(hours)
    
    # Se for menos de 1 hora, mostrar apenas em minutos
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} min"
    
    # Se for 1 hora ou mais, mostrar horas e minutos
    hours_int = int(hours)
    minutes = int((hours - hours_int) * 60)
    
    if minutes == 0:
        return f"{hours_int}h"
    else:
        return f"{hours_int}h {minutes}min"


@register.filter
def to_js_number(value):
    """
    Converte Decimal/None para número JavaScript
    
    Django DecimalField não renderiza corretamente em contextos JavaScript.
    Este filtro garante que o valor seja convertido para float.
    
    Exemplos:
        Decimal('-23.6372844') -> -23.6372844
        None -> 0
        'invalid' -> 0
    """
    if value is None:
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0
