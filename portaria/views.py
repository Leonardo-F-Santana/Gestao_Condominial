from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.urls import reverse 
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from .models import Visitante, Morador, Encomenda, Solicitacao # <--- IMPORTANTE: Solicitacao adicionada

# --- FUNÇÃO UTILITÁRIA PARA GERAR PDF (UTF-8) ---
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    
    # UTF-8 para aceitar emojis e acentos
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    return None

# --- VIEW PRINCIPAL (DASHBOARD) ---
@login_required
def home(request):
    # 1. PROCESSAMENTO DO FORMULÁRIO DE VISITANTES (POST)
    if request.method == "POST":
        nome_completo = request.POST.get('nome_completo')
        cpf = request.POST.get('cpf')
        data_nascimento = request.POST.get('data_nascimento')
        placa_veiculo = request.POST.get('placa_veiculo')
        morador_responsavel_id = request.POST.get('morador_responsavel')
        quem_autorizou = request.POST.get('quem_autorizou')
        observacoes = request.POST.get('observacoes')

        morador_obj = None
        if morador_responsavel_id:
            morador_obj = get_object_or_404(Morador, id=morador_responsavel_id)

        try:
            visitante = Visitante(
                nome_completo=nome_completo,
                cpf=cpf,
                data_nascimento=data_nascimento if data_nascimento else None,
                placa_veiculo=placa_veiculo,
                morador_responsavel=morador_obj,
                quem_autorizou=quem_autorizou,
                observacoes=observacoes,
                registrado_por=request.user
            )
            visitante.save()
            messages.success(request, 'Visitante registrado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao registrar: {e}')
        
        return redirect('home')

    # 2. PREPARAÇÃO DOS DADOS PARA EXIBIÇÃO (GET)
    
    # A) Filtros e Paginação de Visitantes
    visitantes_list = Visitante.objects.all().order_by('-horario_chegada')
    
    query = request.GET.get('busca')
    if query:
        visitantes_list = visitantes_list.filter(
            Q(nome_completo__icontains=query) | Q(cpf__icontains=query)
        )
    
    paginator = Paginator(visitantes_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # B) Lista Completa de Moradores (Para os filtros JS)
    todos_moradores = Morador.objects.all().order_by('bloco', 'apartamento') 
    
    # C) Contadores do Dashboard
    visitantes_no_local = Visitante.objects.filter(horario_saida__isnull=True).count()
    encomendas_pendentes = Encomenda.objects.filter(entregue=False).count()
    
    # D) Lista Rápida de Encomendas (Top 5)
    lista_encomendas = Encomenda.objects.filter(entregue=False).order_by('-data_chegada')[:5]

    # E) Lista Rápida de Solicitações (Top 10) <--- NOVO
    lista_solicitacoes = Solicitacao.objects.all().order_by('-data_criacao')[:10]

    context = {
        'nome_pagina': 'Início',
        'lista_visitantes': page_obj,
        'todos_moradores': todos_moradores,
        'visitantes_no_local': visitantes_no_local,
        'encomendas_pendentes': encomendas_pendentes,
        'lista_encomendas': lista_encomendas,
        'lista_solicitacoes': lista_solicitacoes, # <--- NOVO
        'query_busca': query,
    }
    
    return render(request, 'index.html', context)

# --- REGISTRAR SAÍDA DE VISITANTE ---
@login_required
def registrar_saida(request, id_visitante):
    visitante = get_object_or_404(Visitante, id=id_visitante)
    
    visitante.horario_saida = timezone.now()
    visitante.save()
    
    messages.success(request, f"Saída registrada para {visitante.nome_completo}")
    return redirect('home')

# --- REGISTRAR NOVA ENCOMENDA ---
@login_required
def registrar_encomenda(request):
    if request.method == "POST":
        morador_id = request.POST.get('morador_encomenda')
        volume = request.POST.get('volume')
        destinatario_alternativo = request.POST.get('destinatario_alternativo')
        
        if morador_id and volume:
            morador = get_object_or_404(Morador, id=morador_id)
            
            Encomenda.objects.create(
                morador=morador,
                volume=volume,
                destinatario_alternativo=destinatario_alternativo,
                porteiro_cadastro=request.user # Rastreabilidade
            )
            
            msg = f"Encomenda registrada para {morador.nome}"
            if destinatario_alternativo:
                msg += f" (A/C: {destinatario_alternativo})"
            
            messages.success(request, msg)
        else:
            messages.error(request, "Erro: Selecione um morador e descreva o volume.")
        
        return redirect(f"{reverse('home')}?aba=encomendas")
    
    return redirect('home')

# --- REGISTRAR SOLICITAÇÃO / OCORRÊNCIA (NOVO) ---
@login_required
def registrar_solicitacao(request):
    if request.method == "POST":
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        morador_id = request.POST.get('morador_solicitacao') # Opcional
        
        if tipo and descricao:
            nova_sol = Solicitacao(
                tipo=tipo,
                descricao=descricao,
                criado_por=request.user
            )
            
            if morador_id:
                morador = get_object_or_404(Morador, id=morador_id)
                nova_sol.morador = morador
            
            nova_sol.save()
            messages.success(request, 'Solicitação registrada com sucesso!')
        else:
            messages.error(request, 'Preencha o tipo e a descrição.')
            
        return redirect(f"{reverse('home')}?aba=solicitacoes")

    return redirect('home')

# --- CONFIRMAR ENTREGA ---
@login_required
def confirmar_entrega(request, id_encomenda):
    if request.method == "POST":
        encomenda = get_object_or_404(Encomenda, id=id_encomenda)
        
        nome_retirada = request.POST.get('nome_retirada')
        documento_retirada = request.POST.get('documento_retirada')
        
        encomenda.entregue = True
        encomenda.data_entrega = timezone.now()
        encomenda.quem_retirou = nome_retirada
        encomenda.documento_retirada = documento_retirada
        encomenda.porteiro_entrega = request.user # Rastreabilidade
        
        encomenda.save()
        
        messages.success(request, f'Entregue para: {nome_retirada}')
        return redirect(f"{reverse('home')}?aba=encomendas")
    
    return redirect('home')

# --- MARCAR COMO NOTIFICADO ---
@login_required
def marcar_notificado(request, id_encomenda):
    encomenda = get_object_or_404(Encomenda, id=id_encomenda)
    encomenda.notificado = True
    encomenda.save()
    return redirect(f"{reverse('home')}?aba=encomendas")

# --- HISTÓRICO COMPLETO DE ENCOMENDAS ---
@login_required
def historico_encomendas(request):
    busca = request.GET.get('busca')
    
    encomendas_list = Encomenda.objects.filter(entregue=True).order_by('-data_entrega')
    
    if busca:
        encomendas_list = encomendas_list.filter(
            Q(morador__nome__icontains=busca) | 
            Q(morador__apartamento__icontains=busca) |
            Q(morador__bloco__icontains=busca) |
            Q(volume__icontains=busca) |
            Q(destinatario_alternativo__icontains=busca)
        )
    
    paginator = Paginator(encomendas_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'encomendas': page_obj,
        'busca': busca
    }
    return render(request, 'historico_encomendas.html', context)

# --- EXPORTAR RELATÓRIO PDF (VISITANTES) ---
@login_required
def exportar_relatorio(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    visitantes = Visitante.objects.all().order_by('-horario_chegada')
    
    if data_inicio and data_fim:
        visitantes = visitantes.filter(
            horario_chegada__date__range=[data_inicio, data_fim]
        )
    
    contexto = {
        'visitantes': visitantes,
        'usuario': request.user,
        'data_geracao': timezone.now(),
    }
    
    pdf = render_to_pdf('relatorio_pdf.html', contexto)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Relatorio_{data_inicio}_a_{data_fim}.pdf" if data_inicio else "Relatorio_Geral.pdf"
        response['Content-Disposition'] = f"attachment; filename={filename}"
        return response
    
    return HttpResponse("Erro ao gerar PDF")

# --- EXPORTAR RELATÓRIO PDF (ENCOMENDAS) ---
@login_required
def exportar_relatorio_encomendas(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    encomendas = Encomenda.objects.all().order_by('-data_chegada')
    
    if data_inicio and data_fim:
        encomendas = encomendas.filter(
            data_chegada__date__range=[data_inicio, data_fim]
        )
    
    contexto = {
        'encomendas': encomendas,
        'usuario': request.user,
        'data_geracao': timezone.now(),
    }
    
    pdf = render_to_pdf('relatorio_encomendas_pdf.html', contexto)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Relatorio_Encomendas.pdf"
        response['Content-Disposition'] = f"attachment; filename={filename}"
        return response
    
    return HttpResponse("Erro ao gerar PDF")