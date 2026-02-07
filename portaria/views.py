from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import localdate # <--- IMPORTANTE: ISSO CORRIGE O DATA
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpResponse
from django_ratelimit.decorators import ratelimit
from .models import Visitante, Morador, Encomenda, Solicitacao

# Tenta importar biblioteca de PDF
try:
    from django.template.loader import get_template
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

# ==========================================
# FUNÇÃO AUXILIAR PARA PDF
# ==========================================
def _gerar_pdf(request, template_name, context, filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    if not pisa:
        return HttpResponse("Erro: Biblioteca xhtml2pdf não instalada. Rode: pip install xhtml2pdf")

    template = get_template(template_name)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse(f'Erro ao gerar PDF: {pisa_status.err}')
    return response

# ==========================================
# 1. AUTENTICAÇÃO
# ==========================================

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        # Redireciona baseado no tipo de usuário
        if hasattr(request.user, 'morador'):
            return redirect('morador_home')
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redireciona morador para portal, staff para portaria
            if hasattr(user, 'morador'):
                return redirect('morador_home')
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
# 2. DASHBOARD (CORRIGIDO AQUI)
# ==========================================

@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    hoje = localdate() # <--- USA A DATA LOCAL CORRETA
    
    # Filtra usando __date=hoje para garantir precisão
    total_visitantes_hoje = Visitante.objects.filter(horario_chegada__date=hoje).count()
    encomendas_pendentes = Encomenda.objects.filter(entregue=False).count()
    encomendas_entregues = Encomenda.objects.filter(entregue=True).count()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').count()

    tipos_solicitacao = Solicitacao.objects.values('tipo').annotate(total=Count('tipo'))
    labels_pizza = [item['tipo'] for item in tipos_solicitacao]
    data_pizza = [item['total'] for item in tipos_solicitacao]

    status_counts = Solicitacao.objects.values('status').annotate(total=Count('status'))
    labels_status = [item['status'] for item in status_counts]
    data_status = [item['total'] for item in status_counts]

    context = {
        'total_visitantes_hoje': total_visitantes_hoje,
        'encomendas_pendentes': encomendas_pendentes,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'entregues': encomendas_entregues,
        'pendentes': encomendas_pendentes,
        'labels_pizza': labels_pizza,
        'data_pizza': data_pizza,
        'labels_status': labels_status,
        'data_status': data_status,
    }
    return render(request, 'dashboard.html', context)

# ==========================================
# 3. API STATS (Polling AJAX)
# ==========================================

from django.http import JsonResponse

@login_required
def api_stats(request):
    """Retorna estatísticas em JSON para atualização via AJAX."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Não autorizado'}, status=403)
    
    visitantes_no_local = Visitante.objects.filter(horario_saida__isnull=True).count()
    encomendas_pendentes = Encomenda.objects.filter(entregue=False).count()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').count()
    
    return JsonResponse({
        'visitantes_no_local': visitantes_no_local,
        'encomendas_pendentes': encomendas_pendentes,
        'solicitacoes_pendentes': solicitacoes_pendentes,
    })

# ==========================================
# 4. HOME & VISITANTES
# ==========================================

@login_required
def home(request):
    # Se for morador, redireciona para o portal do morador
    if hasattr(request.user, 'morador'):
        return redirect('morador_home')
    
    # Só staff (porteiros/admin) podem acessar a portaria
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar a portaria.")
        return redirect('login')
    
    if request.method == 'POST' and 'nome_completo' in request.POST:
        registrar_visitante(request)
        return redirect('home')

    query = request.GET.get('busca')
    
    visitantes_all = Visitante.objects.select_related('morador_responsavel').all().order_by('-horario_chegada')
    
    if query:
        visitantes_all = visitantes_all.filter(Q(nome_completo__icontains=query) | Q(cpf__icontains=query))

    paginator = Paginator(visitantes_all, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # CORREÇÃO AQUI TAMBÉM: Usamos localdate()
    hoje = localdate()
    visitantes_hoje_total = Visitante.objects.filter(horario_chegada__date=hoje).count() # Total do dia
    visitantes_no_local_count = Visitante.objects.filter(horario_saida__isnull=True).count() # Só quem está dentro
    
    encomendas_pendentes_count = Encomenda.objects.filter(entregue=False).count()
    solicitacoes_pendentes_count = Solicitacao.objects.filter(status='PENDENTE').count()
    
    lista_encomendas = Encomenda.objects.filter(entregue=False).select_related('morador').order_by('-data_chegada')
    lista_solicitacoes = Solicitacao.objects.all().select_related('morador').order_by('-data_criacao')[:10]
    todos_moradores = Morador.objects.all().order_by('bloco', 'apartamento')

    context = {
        'lista_visitantes': page_obj, 
        'visitantes_hoje_total': visitantes_hoje_total, # Nova variável
        'visitantes_no_local': visitantes_no_local_count,
        'encomendas_pendentes': encomendas_pendentes_count,
        'solicitacoes_pendentes': solicitacoes_pendentes_count,
        'lista_encomendas': lista_encomendas,
        'lista_solicitacoes': lista_solicitacoes,
        'todos_moradores': todos_moradores,
        'query_busca': query,
        'aba_ativa': request.GET.get('aba', 'visitantes')
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
    encomendas_list = Encomenda.objects.filter(entregue=True).order_by('-data_entrega')
    
    busca = request.GET.get('busca')
    if busca:
        encomendas_list = encomendas_list.filter(
            Q(morador__nome__icontains=busca) | 
            Q(morador__apartamento__icontains=busca) |
            Q(quem_retirou__icontains=busca) |
            Q(volume__icontains=busca)
        )

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        try:
            dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            encomendas_list = encomendas_list.filter(data_entrega__range=(dt_i, dt_f))
        except ValueError:
            pass

    paginator = Paginator(encomendas_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'encomendas': page_obj,
        'busca': busca,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    return render(request, 'historico_encomendas.html', context)

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
    solicitacoes_list = Solicitacao.objects.select_related('morador').all().order_by('-data_criacao')
    
    busca = request.GET.get('busca')
    if busca:
        solicitacoes_list = solicitacoes_list.filter(
            Q(descricao__icontains=busca) | 
            Q(morador__nome__icontains=busca)
        )

    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        solicitacoes_list = solicitacoes_list.filter(tipo=tipo_filtro)

    status_filtro = request.GET.get('status')
    if status_filtro:
        solicitacoes_list = solicitacoes_list.filter(status=status_filtro)

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        try:
            dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            solicitacoes_list = solicitacoes_list.filter(data_criacao__range=(dt_i, dt_f))
        except ValueError:
            pass

    paginator = Paginator(solicitacoes_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'solicitacoes': page_obj,
        'busca': busca,
        'tipo_filtro': tipo_filtro,
        'status_filtro': status_filtro,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    return render(request, 'historico_solicitacoes.html', context)

# ==========================================
# 6. RELATÓRIOS PDF
# ==========================================

@login_required
def exportar_relatorio(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    visitantes = Visitante.objects.all().order_by('-horario_chegada')
    
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        try:
            dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            visitantes = visitantes.filter(horario_chegada__range=(dt_i, dt_f))
        except ValueError:
            pass
            
    context = {
        'titulo': 'Relatório de Acesso (Visitantes)',
        'visitantes': visitantes,
        'user': request.user,
        'tipo_relatorio': 'visitantes'
    }
    return _gerar_pdf(request, 'relatorio_pdf.html', context, 'relatorio_acesso.pdf')

@login_required
def exportar_relatorio_encomendas(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    encomendas = Encomenda.objects.all().order_by('-data_chegada')
    
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        try:
            dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            encomendas = encomendas.filter(data_chegada__range=(dt_i, dt_f))
        except ValueError:
            pass

    context = {
        'titulo': 'Relatório Geral de Encomendas',
        'encomendas': encomendas,
        'user': request.user,
        'tipo_relatorio': 'encomendas'
    }
    return _gerar_pdf(request, 'relatorio_pdf.html', context, 'relatorio_encomendas.pdf')

@login_required
def exportar_relatorio_solicitacoes(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo_filtro')
    
    solicitacoes = Solicitacao.objects.all().order_by('-data_criacao')
    
    if data_inicio and data_fim:
        from datetime import datetime, timedelta
        try:
            dt_i = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_f = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            solicitacoes = solicitacoes.filter(data_criacao__range=(dt_i, dt_f))
        except ValueError:
            pass
            
    if tipo:
        solicitacoes = solicitacoes.filter(tipo=tipo)

    context = {
        'titulo': 'Relatório de Ocorrências e Solicitações',
        'solicitacoes': solicitacoes,
        'user': request.user,
        'tipo_relatorio': 'solicitacoes'
    }
    return _gerar_pdf(request, 'relatorio_pdf.html', context, 'relatorio_ocorrencias.pdf')