from .models import Condominio, Morador
from django.contrib.auth import get_user_model


def dashboard_callback(request, context):
    """Callback para o dashboard do Unfold Admin — Gestão SaaS."""
    User = get_user_model()

    context.update({
        # Contadores globais
        "total_condominios": Condominio.objects.count(),
        "condominios_ativos": Condominio.objects.filter(ativo=True).count(),
        "total_usuarios": User.objects.count(),
        "total_moradores": Morador.objects.count(),

        # Usuários por tipo
        "total_sindicos": User.objects.filter(tipo_usuario='sindico').count(),
        "total_porteiros": User.objects.filter(tipo_usuario='porteiro').count(),
        "total_moradores_user": User.objects.filter(tipo_usuario='morador').count(),
        "total_admins": User.objects.filter(is_superuser=True).count(),
    })

    return context
