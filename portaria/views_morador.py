from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings
from .models import (
    Condominio, Morador, Encomenda, Solicitacao, Aviso, Notificacao, Sindico, AreaComum, Reserva, Mensagem, Ocorrencia, PushSubscription, Cobranca
)
from django.db.models import Q
import json
from django.http import JsonResponse


def get_morador_from_user(user):
    """Retorna o morador vinculado ao usuário logado"""
    try:
        return user.morador
    except (Morador.DoesNotExist, AttributeError):
        return None


def morador_required(view_func):
    """Decorator para verificar se o usuário é um morador"""
    def wrapper(request, *args, **kwargs):
        morador = get_morador_from_user(request.user)
        if not morador:
            messages.error(request, "Você não tem acesso ao portal do morador.")
            from django.contrib.auth import logout
            logout(request)
            return redirect('login')
        request.morador = morador
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


def get_morador_ativo(request):
    """Retorna o objeto Morador do usuário logado, se existir."""
    if request.user.is_authenticated:
        try:
            return request.user.morador
        except Morador.DoesNotExist:
            pass
    return None

def get_condominio_ativo(request):
    """Retorna o objeto Condominio do morador logado, se existir."""
    morador = get_morador_ativo(request)
    if morador:
        return morador.condominio
    return None

def morador_context(request, extra_context=None, active_page=None):
    """
    Cria um dicionário de contexto padrão para as views do morador.
    Inclui o morador, condomínio, e contagens de notificações.
    """
    morador = get_morador_ativo(request)
    condominio = get_condominio_ativo(request)
    
    context = {
        'morador': morador,
        'condominio': condominio,
        'active_page': active_page,
    }

    if request.user.is_authenticated:
        context['notificacoes_nao_lidas'] = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).count()
        context['mensagens_nao_lidas'] = Mensagem.objects.filter(
            destinatario=request.user, lida=False
        ).count()
        context['VAPID_PUBLIC_KEY'] = getattr(settings, 'VAPID_PUBLIC_KEY', '')

    if extra_context:
        context.update(extra_context)
    return context


@morador_required
def portal_home(request):
    """Dashboard do morador"""
    morador = request.morador

    # Encomendas pendentes
    encomendas_pendentes = Encomenda.objects.filter(
        morador=morador,
        entregue=False
    ).count()

    # Solicitações pendentes
    solicitacoes_pendentes = Solicitacao.objects.filter(
        morador=morador,
        status='PENDENTE'
    ).count()

    # Avisos não lidos
    avisos_nao_lidos = Notificacao.objects.filter(
        usuario=request.user,
        tipo='aviso',
        lida=False
    ).count()

    # Solicitações recentes
    solicitacoes_recentes = Solicitacao.objects.filter(
        morador=morador
    ).order_by('-data_criacao')[:5]

    # Avisos ativos
    avisos = Aviso.objects.filter(ativo=True)[:3]

    # Cobranças Pendentes
    cobrancas_pendentes = Cobranca.objects.filter(
        morador=morador,
        condominio=morador.condominio,
        status__in=['PENDENTE', 'ATRASADO']
    ).count()

    context = {
        'morador': morador,
        'encomendas_pendentes': encomendas_pendentes,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'avisos_nao_lidos': avisos_nao_lidos,
        'solicitacoes_recentes': solicitacoes_recentes,
        'avisos': avisos,
        'cobrancas_pendentes': cobrancas_pendentes,
    }
    return render(request, 'morador/portal_home.html', context)

@morador_required
def minhas_cobrancas(request):
    """Lista de boletos e cobranças do morador"""
    morador = request.morador
    cobrancas_list = Cobranca.objects.filter(
        morador=morador,
        condominio=morador.condominio
    ).order_by('-data_vencimento')

    paginator = Paginator(cobrancas_list, 10)
    page_number = request.GET.get('page')
    cobrancas = paginator.get_page(page_number)

    context = morador_context(request, {
        'cobrancas': cobrancas,
    }, active_page='cobrancas')

    return render(request, 'morador/cobrancas.html', context)


@morador_required
def minhas_encomendas(request):
    """Lista de encomendas do morador"""
    morador = request.morador

    # Filtro de status
    status = request.GET.get('status', 'pendentes')

    if status == 'entregues':
        encomendas_list = Encomenda.objects.filter(
            morador=morador,
            entregue=True
        ).order_by('-data_entrega')
    else:
        encomendas_list = Encomenda.objects.filter(
            morador=morador,
            entregue=False
        ).order_by('-data_chegada')

    paginator = Paginator(encomendas_list, 10)
    page_number = request.GET.get('page')
    encomendas = paginator.get_page(page_number)

    context = {
        'morador': morador,
        'encomendas': encomendas,
        'status_filtro': status,
    }
    return render(request, 'morador/encomendas.html', context)


@morador_required
def minhas_solicitacoes(request):
    """Lista de solicitações do morador"""
    morador = request.morador

    # Marcar notificações de respostas como lidas
    Notificacao.objects.filter(
        usuario=request.user, tipo='resposta_solicitacao', lida=False
    ).update(lida=True)

    solicitacoes_list = Solicitacao.objects.filter(
        morador=morador
    ).order_by('-data_criacao')

    # Filtros
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')

    if tipo:
        solicitacoes_list = solicitacoes_list.filter(tipo=tipo)
    if status:
        solicitacoes_list = solicitacoes_list.filter(status=status)

    paginator = Paginator(solicitacoes_list, 10)
    page_number = request.GET.get('page')
    solicitacoes = paginator.get_page(page_number)

    context = {
        'morador': morador,
        'solicitacoes': solicitacoes,
        'tipo_filtro': tipo,
        'status_filtro': status,
    }
    return render(request, 'morador/solicitacoes.html', context)


@morador_required
def nova_solicitacao(request):
    """Formulário para abrir nova solicitação"""
    morador = request.morador

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        arquivo = request.FILES.get('arquivo')

        if tipo and descricao:
            sol_kwargs = dict(
                tipo=tipo,
                descricao=descricao,
                morador=morador,
                criado_por=request.user,
                condominio=morador.condominio,
            )
            if arquivo:
                sol_kwargs['arquivo'] = arquivo
            solicitacao = Solicitacao.objects.create(**sol_kwargs)

            # Notificar síndicos do condomínio
            if morador.condominio:
                sindicos = Sindico.objects.filter(condominio=morador.condominio)
                notificacoes = [
                    Notificacao(
                        usuario=s.usuario,
                        tipo='solicitacao',
                        mensagem=f'Nova solicitação #{solicitacao.id} de {morador.nome[:30]}',
                        link='/sindico/solicitacoes/'
                    ) for s in sindicos if s.usuario
                ]
                Notificacao.objects.bulk_create(notificacoes)

            messages.success(request, f"Solicitação #{solicitacao.id} criada com sucesso!")
            return redirect('morador_solicitacoes')
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")

    context = {
        'morador': morador,
        'tipos': Solicitacao.TIPOS_CHOICES,
    }
    return render(request, 'morador/nova_solicitacao.html', context)


@morador_required
def ver_solicitacao(request, id):
    """Detalhes de uma solicitação"""
    morador = request.morador
    solicitacao = get_object_or_404(Solicitacao, id=id, morador=morador)

    context = {
        'morador': morador,
        'solicitacao': solicitacao,
    }
    return render(request, 'morador/ver_solicitacao.html', context)


@morador_required
def avisos(request):
    """Lista de avisos do condomínio"""
    morador = request.morador

    # Filtrar avisos pelo condomínio do morador
    avisos_list = Aviso.objects.filter(
        ativo=True, condominio=morador.condominio
    ).order_by('-data_publicacao')

    paginator = Paginator(avisos_list, 10)
    page_number = request.GET.get('page')
    avisos = paginator.get_page(page_number)

    context = {
        'morador': morador,
        'avisos': avisos,
    }

    response = render(request, 'morador/avisos.html', context)

    # Marcar notificações como lidas APÓS renderizar a página
    # para que o badge apareça na primeira visita
    Notificacao.objects.filter(
        usuario=request.user, tipo='aviso', lida=False
    ).update(lida=True)

    return response


# ==========================================
# RESERVAS (MORADOR)
# ==========================================

@morador_required
def areas_disponiveis(request):
    """Lista áreas disponíveis para reserva"""
    morador = request.morador

    areas = AreaComum.objects.filter(
        condominio=morador.condominio, ativo=True
    )

    context = {
        'morador': morador,
        'areas': areas,
    }
    return render(request, 'morador/areas_disponiveis.html', context)


@morador_required
def fazer_reserva(request, area_id):
    """Formulário para fazer uma reserva"""
    morador = request.morador
    area = get_object_or_404(AreaComum, id=area_id, condominio=morador.condominio, ativo=True)

    if request.method == 'POST':
        data = request.POST.get('data')
        observacoes = request.POST.get('observacoes', '')

        if data:
            # Verificar se a data JÁ está reservada (bloqueio por dia inteiro)
            conflito = Reserva.objects.filter(
                area=area,
                data=data,
                status__in=['PENDENTE', 'APROVADA'],
            ).exists()

            if conflito:
                messages.error(request, 'Esta data já está reservada. Escolha outra data disponível.')
            else:
                reserva = Reserva.objects.create(
                    area=area,
                    morador=morador,
                    data=data,
                    horario_inicio=area.horario_abertura,
                    horario_fim=area.horario_fechamento,
                    observacoes=observacoes,
                )

                # Notificar síndicos
                if morador.condominio:
                    sindicos = Sindico.objects.filter(condominio=morador.condominio)
                    notificacoes = [
                        Notificacao(
                            usuario=s.usuario,
                            tipo='reserva',
                            mensagem=f'Nova reserva de {area.nome} por {morador.nome[:20]}',
                            link='/sindico/reservas/'
                        ) for s in sindicos if s.usuario
                    ]
                    Notificacao.objects.bulk_create(notificacoes)

                messages.success(request, f'Reserva de {area.nome} para {data} solicitada com sucesso!')
                return redirect('morador_reservas')
        else:
            messages.error(request, 'Selecione uma data.')

    # Buscar todas as datas bloqueadas (pendentes ou aprovadas)
    datas_bloqueadas = list(
        Reserva.objects.filter(
            area=area,
            data__gte=timezone.now().date(),
            status__in=['PENDENTE', 'APROVADA'],
        ).values_list('data', flat=True).distinct()
    )
    # Converter para strings no formato ISO para o JavaScript
    datas_bloqueadas_str = [d.strftime('%Y-%m-%d') for d in datas_bloqueadas]

    # Reservas existentes para mostrar na tela
    reservas_existentes = Reserva.objects.filter(
        area=area,
        data__gte=timezone.now().date(),
        status__in=['PENDENTE', 'APROVADA'],
    ).select_related('morador').order_by('data')[:20]

    context = {
        'morador': morador,
        'area': area,
        'reservas_existentes': reservas_existentes,
        'datas_bloqueadas_json': datas_bloqueadas_str,
    }
    return render(request, 'morador/fazer_reserva.html', context)


@morador_required
def minhas_reservas(request):
    """Lista reservas do morador"""
    morador = request.morador

    # Marcar notificações de reserva como lidas
    Notificacao.objects.filter(
        usuario=request.user, tipo='reserva', lida=False
    ).update(lida=True)

    reservas_list = Reserva.objects.filter(
        morador=morador
    ).select_related('area').order_by('-data')

    # Filtro de status
    status_filtro = request.GET.get('status')
    if status_filtro:
        reservas_list = reservas_list.filter(status=status_filtro)

    # Filtro de área
    area_filtro = request.GET.get('area')
    if area_filtro:
        reservas_list = reservas_list.filter(area_id=area_filtro)

    # Áreas disponíveis do condomínio para o filtro
    areas = AreaComum.objects.filter(
        condominio=morador.condominio, ativo=True
    ).order_by('nome') if morador.condominio else AreaComum.objects.none()

    paginator = Paginator(reservas_list, 10)
    page_number = request.GET.get('page')
    reservas = paginator.get_page(page_number)

    context = {
        'morador': morador,
        'reservas': reservas,
        'status_filtro': status_filtro,
        'area_filtro': area_filtro,
        'areas': areas,
    }
    return render(request, 'morador/reservas.html', context)


@morador_required
def cancelar_reserva(request, reserva_id):
    """Cancelar uma reserva pendente"""
    morador = request.morador
    reserva = get_object_or_404(Reserva, id=reserva_id, morador=morador)

    if reserva.status == 'PENDENTE':
        reserva.status = 'CANCELADA'
        reserva.save()
        messages.success(request, 'Reserva cancelada.')
    else:
        messages.error(request, 'Só é possível cancelar reservas pendentes.')

    return redirect('morador_reservas')

# ==========================================
# MENSAGENS / COMUNICAÇÃO INTERNA
# ==========================================

@morador_required
def mensagens(request):
    """Caixa de entrada e chat interno para o morador"""
    morador = request.morador
    usuario = request.user
    condominio = morador.condominio

    if request.method == 'POST':
        destinatario_id = request.POST.get('destinatario_id')
        conteudo = request.POST.get('conteudo', '').strip()

        if destinatario_id and conteudo:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            destinatario = get_object_or_404(User, id=destinatario_id)

            Mensagem.objects.create(
                condominio=condominio,
                remetente=usuario,
                destinatario=destinatario,
                conteudo=conteudo
            )
            messages.success(request, 'Mensagem enviada com sucesso!')
            return redirect('morador_mensagens')
        else:
            messages.error(request, 'Destinatário e conteúdo são obrigatórios.')

    # Marcar mensagens recebidas como lidas
    Mensagem.objects.filter(destinatario=usuario, lida=False).update(lida=True)

    mensagens_list = Mensagem.objects.filter(
        Q(remetente=usuario) | Q(destinatario=usuario)
    ).select_related('remetente', 'destinatario').order_by('-data_envio')

    from django.contrib.auth import get_user_model
    User = get_user_model()
    destinatarios_possiveis = User.objects.filter(
        condominio=condominio,
        tipo_usuario__in=['sindico', 'porteiro']
    ).exclude(id=usuario.id)

    # Agrupar mensagens por contato para chat estilo WhatsApp
    conversas = {}
    for msg in mensagens_list:
        outro_usuario = msg.destinatario if msg.remetente == usuario else msg.remetente
        if outro_usuario not in conversas:
            conversas[outro_usuario] = []
        conversas[outro_usuario].append(msg)
        
    # Reverter mensagens para ficar em ordem cronológica no chat
    for k in conversas:
        conversas[k] = list(reversed(conversas[k]))

    context = morador_context(request, {
        'conversas': conversas,
        'destinatarios': destinatarios_possiveis,
    }, active_page='mensagens')
    
    return render(request, 'morador/mensagens.html', context)

# ==========================================
# OCORRÊNCIAS / LIVRO NEGRO
# ==========================================

@login_required
def ocorrencias(request):
    """View para o morador registrar e listar ocorrências (Livro Negro)"""
    morador = get_morador_ativo(request)
    if not morador:
        return redirect('home')

    condominio = get_condominio_ativo(request)
    
    if request.method == 'POST':
        infrator = request.POST.get('infrator', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        
        if descricao:
            Ocorrencia.objects.create(
                condominio=condominio,
                autor=morador,
                infrator=infrator,
                descricao=descricao
            )
            messages.success(request, 'Ocorrência registrada com sucesso.')
            return redirect('morador_ocorrencias')
        else:
            messages.error(request, 'A descrição da ocorrência é obrigatória.')

    ocorrencias_list = Ocorrencia.objects.filter(condominio=condominio, autor=morador).order_by('-data_registro')
    
    context = morador_context(request, {
        'ocorrencias': ocorrencias_list,
    }, active_page='ocorrencias')
    
    return render(request, 'morador/ocorrencias.html', context)


@login_required
def salvar_push_subscription(request):
    """Salva a inscrição (PushSubscription) do usuário logado."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            keys = data.get('keys', {})
            p256dh = keys.get('p256dh')
            auth = keys.get('auth')

            if endpoint and p256dh and auth:
                # Update or create the subscription for the user
                PushSubscription.objects.update_or_create(
                    usuario=request.user,
                    endpoint=endpoint,
                    defaults={
                        'p256dh': p256dh,
                        'auth': auth
                    }
                )
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'invalid data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'invalid method'}, status=405)

