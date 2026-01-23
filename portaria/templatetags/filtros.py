from django import template

register = template.Library()

@register.filter
def somente_numeros(valor):
    """Remove tudo que não for número do telefone"""
    if valor:
        return ''.join(filter(str.isdigit, valor))
    return ''