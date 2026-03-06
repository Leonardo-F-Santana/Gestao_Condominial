from django.conf import settings
from .models import Notificacao

def condominio_info(request):
    """
    Injeta o condomínio atual no contexto de todos os templates.
    Se o usuário estiver logado e tiver um condomínio vinculado, retorna os dados dele.
    """
    if request.user.is_authenticated and hasattr(request.user, 'condominio') and request.user.condominio:
        return {'condominio_atual': request.user.condominio}
    return {'condominio_atual': None}

def notificacoes(request):
    """
    Retorna as notificações não lidas para o usuário autenticado.
    Necessário para o badge de notificações na navbar de todas as páginas.
    """
    if request.user.is_authenticated:
        try:
            from .models import Notificacao, Mensagem, Cobranca
            
            cobrancas_pendentes_count = 0
            try:
                morador = getattr(request.user, 'morador', None)
                if morador:
                    cobrancas_pendentes_count = Cobranca.objects.filter(
                        morador=morador, status__in=['PENDENTE', 'ATRASADO']
                    ).count()
            except Exception:
                pass

            return {
                'notificacoes': Notificacao.objects.filter(usuario=request.user, lida=False),
                'mensagens_nao_lidas': Mensagem.objects.filter(destinatario=request.user, lida=False).count(),
                'cobrancas_pendentes_count': cobrancas_pendentes_count,
            }
        except ImportError:
            pass
    return {'notificacoes': [], 'mensagens_nao_lidas': 0, 'cobrancas_pendentes_count': 0}
