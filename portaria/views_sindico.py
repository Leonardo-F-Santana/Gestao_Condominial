from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Condominio, Sindico, Morador, Visitante, Encomenda, Solicitacao, Aviso


def is_sindico(user):
    """Verifica se o usuário é um síndico"""
    return hasattr(user, 'sindico')


def get_condominio_ativo(request):
    """Retorna o condomínio ativo da sessão"""
    cond_id = request.session.get('condominio_ativo_id')
    if cond_id:
        try:
            return Condominio.objects.get(id=cond_id)
        except Condominio.DoesNotExist:
            return None
    return None


def sindico_required(view_func):
    """Decorator que verifica se é síndico e tem condomínio ativo"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_sindico(request.user):
            messages.error(request, "Você não tem permissão de síndico.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==========================================
# SELEÇÃO DE CONDOMÍNIO
# ==========================================

@login_required
def portal_sindico_home(request):
    """Página inicial do Portal do Síndico - lista de condomínios"""
    if not is_sindico(request.user):
        messages.error(request, "Você não tem permissão de síndico.")
        return redirect('home')
    
    sindico = request.user.sindico
    condominios = sindico.condominios.filter(ativo=True)
    
    # Estatísticas por condomínio
    condominios_stats = []
    for cond in condominios:
        stats = {
            'condominio': cond,
            'moradores': Morador.objects.filter(condominio=cond).count(),
            'encomendas_pendentes': Encomenda.objects.filter(
                morador__condominio=cond, entregue=False
            ).count(),
            'solicitacoes_pendentes': Solicitacao.objects.filter(
                morador__condominio=cond, status='PENDENTE'
            ).count(),
        }
        condominios_stats.append(stats)
    
    context = {
        'sindico': sindico,
        'condominios_stats': condominios_stats,
    }
    return render(request, 'sindico/portal_home.html', context)


@login_required
def selecionar_condominio(request, condominio_id):
    """Seleciona um condomínio e salva na sessão"""
    if not is_sindico(request.user):
        return redirect('home')
    
    sindico = request.user.sindico
    condominio = get_object_or_404(Condominio, id=condominio_id)
    
    if condominio not in sindico.condominios.all():
        messages.error(request, "Você não tem acesso a este condomínio.")
        return redirect('sindico_home')
    
    request.session['condominio_ativo_id'] = condominio.id
    messages.success(request, f"Condomínio '{condominio.nome}' selecionado!")
    return redirect('sindico_painel')


@login_required
def criar_condominio(request):
    """Criar novo condomínio"""
    if not is_sindico(request.user):
        messages.error(request, "Você não tem permissão de síndico.")
        return redirect('home')
    
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        endereco = request.POST.get('endereco', '').strip()
        cnpj = request.POST.get('cnpj', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        email = request.POST.get('email', '').strip()
        
        if not nome:
            messages.error(request, "O nome do condomínio é obrigatório.")
            return redirect('sindico_criar_condominio')
        
        condominio = Condominio.objects.create(
            nome=nome,
            endereco=endereco,
            cnpj=cnpj,
            telefone=telefone,
            email=email
        )
        
        sindico = request.user.sindico
        sindico.condominios.add(condominio)
        
        # Selecionar automaticamente
        request.session['condominio_ativo_id'] = condominio.id
        
        messages.success(request, f"Condomínio '{nome}' criado com sucesso!")
        return redirect('sindico_painel')
    
    return render(request, 'sindico/criar_condominio.html')


# ==========================================
# PAINEL PRINCIPAL
# ==========================================

@login_required
@sindico_required
def painel_sindico(request):
    """Dashboard principal do condomínio selecionado"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        messages.warning(request, "Selecione um condomínio primeiro.")
        return redirect('sindico_home')
    
    # Verificar acesso
    sindico = request.user.sindico
    if condominio not in sindico.condominios.all():
        request.session.pop('condominio_ativo_id', None)
        return redirect('sindico_home')
    
    # Estatísticas
    moradores_count = Morador.objects.filter(condominio=condominio).count()
    visitantes_hoje = Visitante.objects.filter(
        morador_responsavel__condominio=condominio,
        horario_chegada__date=timezone.now().date()
    ).count()
    visitantes_no_local = Visitante.objects.filter(
        morador_responsavel__condominio=condominio,
        horario_saida__isnull=True
    ).count()
    encomendas_pendentes = Encomenda.objects.filter(
        morador__condominio=condominio, entregue=False
    ).count()
    solicitacoes_pendentes = Solicitacao.objects.filter(
        morador__condominio=condominio, status='PENDENTE'
    ).count()
    
    # Últimas atividades
    ultimos_visitantes = Visitante.objects.filter(
        morador_responsavel__condominio=condominio
    ).order_by('-horario_chegada')[:5]
    ultimas_encomendas = Encomenda.objects.filter(
        morador__condominio=condominio
    ).order_by('-data_chegada')[:5]
    ultimas_solicitacoes = Solicitacao.objects.filter(
        morador__condominio=condominio
    ).order_by('-data_criacao')[:5]
    
    context = {
        'condominio': condominio,
        'stats': {
            'moradores': moradores_count,
            'visitantes_hoje': visitantes_hoje,
            'visitantes_no_local': visitantes_no_local,
            'encomendas_pendentes': encomendas_pendentes,
            'solicitacoes_pendentes': solicitacoes_pendentes,
        },
        'ultimos_visitantes': ultimos_visitantes,
        'ultimas_encomendas': ultimas_encomendas,
        'ultimas_solicitacoes': ultimas_solicitacoes,
    }
    return render(request, 'sindico/painel.html', context)


# ==========================================
# GESTÃO DE MORADORES
# ==========================================

@login_required
@sindico_required
def moradores_sindico(request):
    """Lista de moradores do condomínio"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')
    
    # Cadastrar novo morador
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        bloco = request.POST.get('bloco', '').strip()
        apartamento = request.POST.get('apartamento', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        email = request.POST.get('email', '').strip()
        
        if nome and apartamento:
            Morador.objects.create(
                condominio=condominio,
                nome=nome,
                bloco=bloco,
                apartamento=apartamento,
                telefone=telefone,
                email=email
            )
            messages.success(request, f"Morador '{nome}' cadastrado!")
            return redirect('sindico_moradores')
    
    context = {
        'condominio': condominio,
        'moradores': moradores,
    }
    return render(request, 'sindico/moradores.html', context)


# ==========================================
# GESTÃO DE VISITANTES
# ==========================================

@login_required
@sindico_required
def visitantes_sindico(request):
    """Controle de visitantes do condomínio"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')
    visitantes_no_local = Visitante.objects.filter(
        morador_responsavel__condominio=condominio,
        horario_saida__isnull=True
    ).order_by('-horario_chegada')
    
    # Registrar entrada
    if request.method == 'POST' and 'registrar_entrada' in request.POST:
        nome = request.POST.get('nome', '').strip()
        morador_id = request.POST.get('morador_id')
        placa = request.POST.get('placa', '').strip()
        
        if nome:
            morador = Morador.objects.get(id=morador_id) if morador_id else None
            Visitante.objects.create(
                nome_completo=nome,
                morador_responsavel=morador,
                placa_veiculo=placa,
                registrado_por=request.user
            )
            messages.success(request, f"Entrada de '{nome}' registrada!")
            return redirect('sindico_visitantes')
    
    context = {
        'condominio': condominio,
        'moradores': moradores,
        'visitantes_no_local': visitantes_no_local,
    }
    return render(request, 'sindico/visitantes.html', context)


@login_required
@sindico_required
def registrar_saida_sindico(request, visitante_id):
    """Registrar saída de visitante"""
    visitante = get_object_or_404(Visitante, id=visitante_id)
    visitante.horario_saida = timezone.now()
    visitante.save()
    messages.success(request, f"Saída de '{visitante.nome_completo}' registrada!")
    return redirect('sindico_visitantes')


# ==========================================
# GESTÃO DE ENCOMENDAS
# ==========================================

@login_required
@sindico_required
def encomendas_sindico(request):
    """Gestão de encomendas do condomínio"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')
    encomendas_pendentes = Encomenda.objects.filter(
        morador__condominio=condominio, entregue=False
    ).order_by('-data_chegada')
    
    # Registrar encomenda
    if request.method == 'POST' and 'registrar_encomenda' in request.POST:
        morador_id = request.POST.get('morador_id')
        volume = request.POST.get('volume', '').strip()
        
        if morador_id and volume:
            morador = Morador.objects.get(id=morador_id)
            Encomenda.objects.create(
                morador=morador,
                volume=volume,
                porteiro_cadastro=request.user
            )
            messages.success(request, f"Encomenda registrada para '{morador.nome}'!")
            return redirect('sindico_encomendas')
    
    context = {
        'condominio': condominio,
        'moradores': moradores,
        'encomendas_pendentes': encomendas_pendentes,
    }
    return render(request, 'sindico/encomendas.html', context)


@login_required
@sindico_required
def entregar_encomenda_sindico(request, encomenda_id):
    """Marcar encomenda como entregue"""
    encomenda = get_object_or_404(Encomenda, id=encomenda_id)
    encomenda.entregue = True
    encomenda.data_entrega = timezone.now()
    encomenda.porteiro_entrega = request.user
    encomenda.quem_retirou = request.POST.get('quem_retirou', 'Morador')
    encomenda.save()
    messages.success(request, "Encomenda marcada como entregue!")
    return redirect('sindico_encomendas')


# ==========================================
# GESTÃO DE SOLICITAÇÕES
# ==========================================

@login_required
@sindico_required
def solicitacoes_sindico(request):
    """Gestão de solicitações do condomínio"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    solicitacoes = Solicitacao.objects.filter(
        morador__condominio=condominio
    ).order_by('-data_criacao')
    
    context = {
        'condominio': condominio,
        'solicitacoes': solicitacoes,
    }
    return render(request, 'sindico/solicitacoes.html', context)


@login_required
@sindico_required
def responder_solicitacao_sindico(request, solicitacao_id):
    """Responder/atualizar solicitação"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id)
    
    if request.method == 'POST':
        resposta = request.POST.get('resposta', '').strip()
        status = request.POST.get('status', solicitacao.status)
        
        solicitacao.resposta_admin = resposta
        solicitacao.status = status
        solicitacao.save()
        
        messages.success(request, "Solicitação atualizada!")
    
    return redirect('sindico_solicitacoes')


# Manter compatibilidade com a antiga view
def dashboard_condominio(request, condominio_id):
    """Redireciona para o novo fluxo"""
    if request.user.is_authenticated and is_sindico(request.user):
        request.session['condominio_ativo_id'] = condominio_id
        return redirect('sindico_painel')
    return redirect('sindico_home')
