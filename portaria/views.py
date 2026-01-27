from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import Visitante, Morador, Encomenda, Solicitacao

# Tenta importar biblioteca de PDF
try:
    from django.template.loader import get_template
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

# ==========================================
# 1. AUTENTICAÇÃO
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# ==========================================
# 2. DASHBOARD (GRÁFICOS ATUALIZADOS)
# ==========================================

@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    hoje = timezone.now().date()
    
    # 1. Cards do Topo
    total_visitantes_hoje = Visitante.objects.filter(horario_chegada__date=hoje).count()
    encomendas_pendentes = Encomenda.objects.filter(entregue=False).count()
    encomendas_entregues = Encomenda.objects.filter(entregue=True).count()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').count()

    # 2. Gráfico 1: Tipos de Solicitação (Pizza)
    tipos_solicitacao = Solicitacao.objects.values('tipo').annotate(total=Count('tipo'))
    labels_pizza = [item['tipo'] for item in tipos_solicitacao]
    data_pizza = [item['total'] for item in tipos_solicitacao]

    # 3. Gráfico 2: Eficiência/Status (NOVO - Rosca) 🟢🟡🔴
    status_counts = Solicitacao.objects.values('status').annotate(total=Count('status'))
    labels_status = [item['status'] for item in status_counts]
    data_status = [item['total'] for item in status_counts]

    context = {
        'total_visitantes_hoje': total_visitantes_hoje,
        'encomendas_pendentes': encomendas_pendentes,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'entregues': encomendas_entregues,
        'pendentes': encomendas_pendentes,
        
        # Dados Gráficos
        'labels_pizza': labels_pizza,
        'data_pizza': data_pizza,
        'labels_status': labels_status, # <--- Enviando para o HTML
        'data_status': data_status,     # <--- Enviando para o HTML
    }
    return render(request, 'dashboard.html', context)

# ==========================================
# 3. HOME & VISITANTES
# ==========================================

@login_required
def home(request):
    if request.method == 'POST' and 'nome_completo' in request.POST:
        registrar_visitante(request)
        return redirect('home')

    query = request.GET.get('busca')
    visitantes = Visitante.objects.filter(horario_saida__isnull=True).order_by('-horario_chegada')
    
    if query:
        visitantes = visitantes.filter(Q(nome_completo__icontains=query) | Q(cpf__icontains=query))

    paginator = Paginator(visitantes, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'lista_visitantes': page_obj,
        'visitantes_no_local': Visitante.objects.filter(horario_saida__isnull=True).count(),
        'encomendas_pendentes': Encomenda.objects.filter(entregue=False).count(),
        'lista_encomendas': Encomenda.objects.filter(entregue=False).order_by('-data_chegada'),
        'lista_solicitacoes': Solicitacao.objects.all().order_by('-data_criacao')[:5],
        'todos_moradores': Morador.objects.all().order_by('bloco', 'apartamento'),
        'query_busca': query,
    }
    return render(request, 'index.html', context)

@login_required
def registrar_visitante(request):
    if request.method == 'POST':
        morador_id = request.POST.get('morador_responsavel')
        morador = Morador.objects.get(id=morador_id) if morador_id else None
        
        Visitante.objects.create(
            nome_completo=request.POST.get('nome_completo'),
            cpf=request.POST.get('cpf'),
            data_nascimento=request.POST.get('data_nascimento') or None,
            placa_veiculo=request.POST.get('placa_veiculo'),
            morador_responsavel=morador,
            quem_autorizou=request.POST.get('quem_autorizou'),
            observacoes=request.POST.get('observacoes'),
            registrado_por=request.user
        )
        messages.success(request, "Visitante registrado!")
    return redirect('home')

@login_required
def registrar_saida(request, id_visitante):
    visitante = get_object_or_404(Visitante, id=id_visitante)
    visitante.horario_saida = timezone.now()
    visitante.save()
    messages.info(request, "Saída registrada.")
    return redirect('home')

# ==========================================
# 4. ENCOMENDAS
# ==========================================

@login_required
def registrar_encomenda(request):
    if request.method == 'POST':
        morador_id = request.POST.get('morador_encomenda')
        if morador_id:
            Encomenda.objects.create(
                morador=Morador.objects.get(id=morador_id),
                volume=request.POST.get('volume'),
                destinatario_alternativo=request.POST.get('destinatario_alternativo'),
                porteiro_cadastro=request.user
            )
            messages.success(request, "Encomenda registrada!")
        else:
            messages.error(request, "Selecione um morador.")
    return redirect('/?aba=encomendas')

@login_required
def confirmar_entrega(request, id_encomenda):
    if request.method == 'POST':
        enc = get_object_or_404(Encomenda, id=id_encomenda)
        enc.entregue = True
        enc.data_entrega = timezone.now()
        enc.quem_retirou = request.POST.get('nome_retirada')
        enc.documento_retirada = request.POST.get('documento_retirada')
        enc.porteiro_entrega = request.user
        enc.save()
        messages.success(request, "Encomenda entregue!")
    return redirect('/?aba=encomendas')

@login_required
def marcar_notificado(request, id_encomenda):
    enc = get_object_or_404(Encomenda, id=id_encomenda)
    enc.notificado = True
    enc.save()
    return redirect('/?aba=encomendas')

@login_required
def historico_encomendas(request):
    encomendas = Encomenda.objects.filter(entregue=True).order_by('-data_entrega')[:50]
    return render(request, 'historico_encomendas.html', {'encomendas': encomendas})

# ==========================================
# 5. SOLICITAÇÕES
# ==========================================

@login_required
def registrar_solicitacao(request):
    if request.method == 'POST':
        morador_id = request.POST.get('morador_solicitacao')
        morador = Morador.objects.get(id=morador_id) if morador_id else None
        Solicitacao.objects.create(
            tipo=request.POST.get('tipo'),
            descricao=request.POST.get('descricao'),
            morador=morador,
            criado_por=request.user
        )
        messages.success(request, "Solicitação registrada!")
    return redirect('/?aba=solicitacoes')

@login_required
def historico_solicitacoes(request):
    solicitacoes = Solicitacao.objects.all().order_by('-data_criacao')
    return render(request, 'historico_solicitacoes.html', {'solicitacoes': solicitacoes})

# ==========================================
# 6. RELATÓRIOS PDF
# ==========================================

def _gerar_pdf(request, template_name, context, filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    if pisa:
        html = get_template(template_name).render(context)
        pisa.CreatePDF(html, dest=response)
        return response
    return HttpResponse("Erro: Biblioteca xhtml2pdf não instalada.")

@login_required
def exportar_relatorio(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    visitantes = Visitante.objects.all().order_by('-horario_chegada')
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        visitantes = visitantes.filter(horario_chegada__range=(dt_i, dt_f))
    return _gerar_pdf(request, 'relatorio_pdf.html', {'visitantes': visitantes, 'user': request.user}, 'relatorio_acesso.pdf')

@login_required
def exportar_relatorio_encomendas(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    encomendas = Encomenda.objects.filter(entregue=True).order_by('-data_entrega')
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        encomendas = encomendas.filter(data_entrega__range=(dt_i, dt_f))
    context = {'titulo': 'Relatório de Encomendas', 'encomendas': encomendas, 'user': request.user, 'tipo_relatorio': 'encomendas'}
    return _gerar_pdf(request, 'relatorio_pdf.html', context, 'relatorio_encomendas.pdf')

@login_required
def exportar_relatorio_solicitacoes(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo_filtro')
    solicitacoes = Solicitacao.objects.all().order_by('-data_criacao')
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        solicitacoes = solicitacoes.filter(data_criacao__range=(dt_i, dt_f))
    if tipo:
        solicitacoes = solicitacoes.filter(tipo=tipo)
    context = {'titulo': 'Relatório de Solicitações', 'solicitacoes': solicitacoes, 'user': request.user, 'tipo_relatorio': 'solicitacoes'}
    return _gerar_pdf(request, 'relatorio_pdf.html', context, 'relatorio_ocorrencias.pdf')