from django.conf import settings

from .models import Notificacao



def condominio_info(request):

    pass

    if request.user.is_authenticated:

        condominio_id = request.session.get('condominio_ativo_id')

        if condominio_id:

            condominio = request.user.condominios.filter(id=condominio_id).first()

            if condominio:

                return {'condominio_atual': condominio}





        condominio = getattr(request.user, 'get_condominio_ativo', None)

        if condominio:

            return {'condominio_atual': condominio}

    return {'condominio_atual': None}



def notificacoes(request):

    pass

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

