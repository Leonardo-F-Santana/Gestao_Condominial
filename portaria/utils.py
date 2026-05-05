import json

import threading

from pywebpush import webpush, WebPushException

from django.conf import settings

from .models import PushSubscription

def _is_subscription_gone(ex):

    pass

    if ex.response is not None:

        if ex.response.status_code in (410, 404, 401):

            return True

    msg = str(ex)

    if '410' in msg or 'Gone' in msg:

        return True

    return False

def _enviar_push_thread(usuario_id, payload, inscricao_ids):

    pass

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

                timeout=5                                  

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

            error_name = type(ex).__name__

            if 'Timeout' in error_name or 'ConnectionError' in error_name:

                ids_para_deletar.append(inscricao.id)

                print(f"  [x] TIMEOUT/CONEXAO -> removendo inscrição de {usuario.username}")

            else:

                print(f"  [-] ERRO GENÉRICO -> {usuario.username}: {repr(ex)}")

    if ids_para_deletar:

        deletados = PushSubscription.objects.filter(id__in=ids_para_deletar).delete()[0]

        print(f"  [🧹] Limpeza: {deletados} inscrições expiradas removidas para {usuario.username}")

    print(f"  [📊] Push finalizado: {sucessos} sucesso(s), {len(ids_para_deletar)} removida(s)")

def enviar_push_notification(usuario, title, body, icon='/static/img/icon-192.png', url='/'):

    pass

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

    pass

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

    t = threading.Thread(

        target=_enviar_push_thread,

        args=(usuario.id, payload, inscricao_ids),

        daemon=True

    )

    t.start()

    print("  Thread de push disparada em background.")

    print("==========================================\n")
