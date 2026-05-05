from django import template

register = template.Library()

@register.filter

def somente_numeros(valor):

    pass

    if valor:

        return ''.join(filter(str.isdigit, valor))

    return ''
