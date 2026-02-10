from .models import Notificacao


def notificacoes(request):
    """Injeta contagens de notificações não lidas em todas as templates"""
    if not request.user.is_authenticated:
        return {}

    qs = Notificacao.objects.filter(usuario=request.user, lida=False)

    return {
        'notif_avisos': qs.filter(tipo='aviso').count(),
        'notif_solicitacoes': qs.filter(tipo__in=['solicitacao', 'resposta_solicitacao']).count(),
        'notif_total': qs.count(),
    }
