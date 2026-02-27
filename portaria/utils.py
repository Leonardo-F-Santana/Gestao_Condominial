import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import PushSubscription

def enviar_push_notification(usuario, title, body, icon='/static/img/icon-192.png', url='/'):
    """
    Envia uma notificação Web Push para todas as inscrições do usuário.
    """
    vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    vapid_admin_email = getattr(settings, 'VAPID_ADMIN_EMAIL', None)

    if not vapid_private_key or not vapid_admin_email:
        return

    payload = json.dumps({
        'title': title,
        'body': body,
        'icon': icon,
        'url': url
    })

    inscricoes = PushSubscription.objects.filter(usuario=usuario)
    for sub in inscricoes:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }
        
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": vapid_admin_email}
            )
        except WebPushException as e:
            print(f"Erro ao enviar Push para {usuario.username}: {e}")
            # Se for 410 Gone, a inscrição expirou e precisa ser removida
            if e.response and e.response.status_code == 410:
                sub.delete()
        except Exception as e:
            print(f"Erro genérico no Push: {e}")