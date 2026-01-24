from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse # <--- O ERRO ESTAVA AQUI (Faltava essa linha)
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Visitante, Morador, Encomenda
from .utils import render_to_pdf # Importa a função de PDF que criamos

@login_required
def home(request):
    
    # --- CADASTRO DE VISITANTE (POST) ---
    if request.method == "POST":
        morador_id = request.POST.get('morador_responsavel')
        nascimento = request.POST.get('data_nascimento') or None
        
        Visitante.objects.create(
            nome_completo = request.POST.get('nome_completo'),
            cpf = request.POST.get('cpf'),
            data_nascimento = nascimento,
            placa_veiculo = request.POST.get('placa_veiculo'),
            morador_responsavel_id = morador_id,
            quem_autorizou = request.POST.get('quem_autorizou'),
            observacoes = request.POST.get('observacoes')
        )
        messages.success(request, 'Visitante registrado com sucesso!')
        return redirect('home')

    # --- LISTAGEM DE VISITANTES ---
    query_busca = request.GET.get('busca')
    if query_busca:
        lista_visitantes = Visitante.objects.filter(
            Q(nome_completo__icontains=query_busca) | Q(cpf__icontains=query_busca)
        ).order_by('-horario_chegada')
    else:
        visitantes_ativos = Visitante.objects.filter(horario_saida=None).order_by('-horario_chegada')
        visitantes_finalizados = Visitante.objects.exclude(horario_saida=None).order_by('-horario_chegada')[:5]
        lista_visitantes = list(visitantes_ativos) + list(visitantes_finalizados)

    # --- DADOS GERAIS ---
    visitantes_no_local = Visitante.objects.filter(horario_saida=None).count()
    todos_moradores = Morador.objects.all().order_by('bloco', 'apartamento')

    # --- LÓGICA DE ENCOMENDAS ---
    lista_encomendas = Encomenda.objects.filter(entregue=False).order_by('-data_chegada')
    encomendas_pendentes = lista_encomendas.count()

    contexto = {
        'lista_visitantes': lista_visitantes,
        'todos_moradores': todos_moradores,
        'query_busca': query_busca,
        'visitantes_no_local': visitantes_no_local,
        'encomendas_pendentes': encomendas_pendentes,
        'lista_encomendas': lista_encomendas
    }
    
    return render(request, 'index.html', contexto)

# --- FUNÇÕES DE ENCOMENDAS ---

@login_required
def registrar_encomenda(request):
    if request.method == "POST":
        morador_id = request.POST.get('morador_encomenda')
        volume = request.POST.get('volume')
        
        Encomenda.objects.create(
            morador_id=morador_id,
            volume=volume
        )
        messages.success(request, '📦 Encomenda registrada!')
    return redirect('home')

@login_required
def confirmar_entrega(request, id_encomenda):
    if request.method == "POST":
        encomenda = get_object_or_404(Encomenda, id=id_encomenda)
        
        nome_retirada = request.POST.get('nome_retirada')
        documento_retirada = request.POST.get('documento_retirada') # <--- Captura o documento
        
        encomenda.entregue = True
        encomenda.data_entrega = timezone.now()
        encomenda.quem_retirou = nome_retirada
        encomenda.documento_retirada = documento_retirada # <--- Salva no banco
        encomenda.save()
        
        messages.success(request, f'Baixa realizada! Retirado por: {nome_retirada}')
        return redirect('home')
    return redirect('home')

@login_required
def registrar_saida(request, id_visitante):
    visitante = get_object_or_404(Visitante, id=id_visitante)
    visitante.horario_saida = timezone.now()
    visitante.save()
    messages.success(request, 'Saída registrada com sucesso!')
    return redirect('home')

# --- NOVO: GERADOR DE PDF ---

@login_required
def exportar_relatorio(request):
    visitantes = Visitante.objects.all().order_by('-horario_chegada')
    
    contexto = {
        'visitantes': visitantes,
        'usuario': request.user,
        'data_geracao': timezone.now()
    }
    
    # Gera o PDF usando o utils.py
    pdf = render_to_pdf('relatorio_pdf.html', contexto)
    
    if pdf:
        # Agora o HttpResponse vai funcionar porque importamos lá no topo
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Relatorio_Visitantes.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Erro ao gerar PDF")

# ... (outras funções acima)

@login_required
def exportar_relatorio_encomendas(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Busca todas as encomendas (mais recentes primeiro)
    encomendas = Encomenda.objects.all().order_by('-data_chegada')
    
    # Filtro de Data (se preenchido)
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
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Erro ao gerar PDF")

@login_required
def marcar_notificado(request, id_encomenda):
    encomenda = get_object_or_404(Encomenda, id=id_encomenda)
    encomenda.notificado = True
    encomenda.save()
  
    return redirect('home')

@login_required
def historico_encomendas(request):
   
    encomendas_entregues = Encomenda.objects.filter(entregue=True).order_by('-data_entrega')
    
    return render(request, 'historico_encomendas.html', {'encomendas': encomendas_entregues})