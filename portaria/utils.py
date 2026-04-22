import json
import threading
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import PushSubscription


def _is_subscription_gone(ex):
    """Verifica se a exceção indica que a inscrição expirou (410 Gone) ou é inválida (404/401)."""
    # Primeiro tenta pelo objeto response
    if ex.response is not None:
        if ex.response.status_code in (410, 404, 401):
            return True
    # Fallback: verifica pelo texto da mensagem de erro
    msg = str(ex)
    if '410' in msg or 'Gone' in msg:
        return True
    return False


def _enviar_push_thread(usuario_id, payload, inscricao_ids):
    """Thread worker que envia pushes e faz limpeza de inscrições mortas.
    Recebe IDs para re-buscar dentro da thread (evitar problemas com conexão DB).
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return

    inscricoes = PushSubscription.objects.filter(id__in=inscricao_ids)
    ids_para_deletar = []
    sucessos = 0

    for inscricao in inscricoes:
        try:
            webpush(
                subscription_info={
                    "endpoint": inscricao.endpoint,
                    "keys": {
                        "p256dh": inscricao.p256dh,
                        "auth": inscricao.auth
                    }
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
                timeout=5  # Timeout de 5 segundos por push
            )
            sucessos += 1
            print(f"  [+] PUSH OK -> {usuario.username} (endpoint ...{inscricao.endpoint[-30:]})")
        except WebPushException as ex:
            if _is_subscription_gone(ex):
                ids_para_deletar.append(inscricao.id)
                print(f"  [x] EXPIRADA -> removendo inscrição de {usuario.username}")
            else:
                print(f"  [-] ERRO PUSH -> {usuario.username}: {repr(ex)}")
        except Exception as ex:
            # Timeout ou erro de rede — marca para remoção se for ConnectionError
            error_name = type(ex).__name__
            if 'Timeout' in error_name or 'ConnectionError' in error_name:
                ids_para_deletar.append(inscricao.id)
                print(f"  [x] TIMEOUT/CONEXAO -> removendo inscrição de {usuario.username}")
            else:
                print(f"  [-] ERRO GENÉRICO -> {usuario.username}: {repr(ex)}")

    # Limpa inscrições mortas de uma vez
    if ids_para_deletar:
        deletados = PushSubscription.objects.filter(id__in=ids_para_deletar).delete()[0]
        print(f"  [🧹] Limpeza: {deletados} inscrições expiradas removidas para {usuario.username}")

    print(f"  [📊] Push finalizado: {sucessos} sucesso(s), {len(ids_para_deletar)} removida(s)")


def enviar_push_notification(usuario, title, body, icon='/static/img/icon-192.png', url='/'):
    """
    Envia uma notificação Web Push para todas as inscrições do usuário.
    Executa em thread separada para não bloquear a resposta HTTP.
    """
    vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    vapid_admin_email = getattr(settings, 'VAPID_ADMIN_EMAIL', None)

    if not vapid_private_key or not vapid_admin_email:
        return
        
    if not getattr(usuario, 'receber_push', False):
        return

    payload = json.dumps({
        'title': title,
        'body': body,
        'icon': icon,
        'url': url
    })

    inscricao_ids = list(PushSubscription.objects.filter(usuario=usuario).values_list('id', flat=True))
    if not inscricao_ids:
        return

    t = threading.Thread(
        target=_enviar_push_thread,
        args=(usuario.id, payload, inscricao_ids),
        daemon=True
    )
    t.start()


def disparar_push_individual(usuario, titulo, mensagem, link):
    """Dispara Web Push individual mantendo segurança do modelo SaaS.
    Função utilitária centralizada para uso em portaria e síndico.
    Executa em thread separada para não bloquear a resposta HTTP.
    """
    if not usuario or not getattr(usuario, 'receber_push', False):
        return

    inscricao_ids = list(PushSubscription.objects.filter(usuario=usuario).values_list('id', flat=True))
    
    print(f"\n=== PUSH INDIVIDUAL -> {usuario.username} ({len(inscricao_ids)} inscrições) ===")
    
    if not inscricao_ids:
        print("  Nenhuma inscrição encontrada. Abortando.")
        print("==========================================\n")
        return

    payload = json.dumps({
        'titulo': titulo,
        'mensagem': mensagem,
        'link': link
    })

    # Dispara em thread separada para não travar a resposta do porteiro
    t = threading.Thread(
        target=_enviar_push_thread,
        args=(usuario.id, payload, inscricao_ids),
        daemon=True
    )
    t.start()
    print("  Thread de push disparada em background.")
    print("==========================================\n")