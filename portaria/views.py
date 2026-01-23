from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Visitante, Morador, Encomenda

@login_required
def home(request):
    
    # --- LÓGICA DE VISITANTES (Mantivemos igual) ---
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
    # Pegamos apenas as que NÃO foram entregues para mostrar na lista
    lista_encomendas = Encomenda.objects.filter(entregue=False).order_by('-data_chegada')
    encomendas_pendentes = lista_encomendas.count()

    contexto = {
        'lista_visitantes': lista_visitantes,
        'todos_moradores': todos_moradores,
        'query_busca': query_busca,
        'visitantes_no_local': visitantes_no_local,
        'encomendas_pendentes': encomendas_pendentes,
        'lista_encomendas': lista_encomendas # <--- Enviamos a lista para o HTML
    }
    
    return render(request, 'index.html', contexto)

# --- FUNÇÕES NOVAS PARA ENCOMENDAS ---

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
        
        # Pega o nome que o porteiro digitou no Modal
        nome_retirada = request.POST.get('nome_retirada')
        
        encomenda.entregue = True
        encomenda.data_entrega = timezone.now()
        encomenda.quem_retirou = nome_retirada # Salva quem pegou
        encomenda.save()
        
        messages.success(request, f'Encomenda retirada por: {nome_retirada}')
        return redirect('home')
    
    return redirect('home')

# (Mantenha a função registrar_saida aqui embaixo...)
@login_required
def registrar_saida(request, id_visitante):
    # ... código que já existia ...
    visitante = get_object_or_404(Visitante, id=id_visitante)
    visitante.horario_saida = timezone.now()
    visitante.save()
    messages.success(request, 'Saída registrada com sucesso!')
    return redirect('home')