from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Morador, Encomenda, Solicitacao, Aviso, Notificacao, Sindico


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
            return redirect('login')
        request.morador = morador
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@morador_required
def portal_home(request):
    """Dashboard do morador"""
    morador = request.morador
    
    # Encomendas pendentes
    encomendas_pendentes = Encomenda.objects.filter(
        morador=morador, 
        entregue=False
    ).count()
    
    # Solicitações recentes
    solicitacoes_recentes = Solicitacao.objects.filter(
        morador=morador
    ).order_by('-data_criacao')[:5]
    
    # Avisos ativos
    avisos = Aviso.objects.filter(ativo=True)[:3]
    
    context = {
        'morador': morador,
        'encomendas_pendentes': encomendas_pendentes,
        'solicitacoes_recentes': solicitacoes_recentes,
        'avisos': avisos,
    }
    return render(request, 'morador/portal_home.html', context)


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
            solicitacao = Solicitacao.objects.create(
                tipo=tipo,
                descricao=descricao,
                morador=morador,
                criado_por=request.user,
                arquivo=arquivo if arquivo else ''
            )
            
            # Notificar síndicos do condomínio
            if morador.condominio:
                sindicos = Sindico.objects.filter(condominios=morador.condominio)
                notificacoes = [
                    Notificacao(
                        usuario=s.usuario,
                        tipo='solicitacao',
                        mensagem=f'Nova solicitação #{solicitacao.id} de {morador.nome[:30]}',
                        link='/sindico/solicitacoes/'
                    ) for s in sindicos
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
