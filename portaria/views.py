from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from .models import Visitante

@login_required 
def home(request):
    

    if request.method == "POST":
        Visitante.objects.create(
            nome_completo = request.POST.get('nome_completo'),
            cpf = request.POST.get('cpf'),
            data_nascimento = request.POST.get('data_nascimento'),
            numero_casa = request.POST.get('numero_casa'),
            placa_veiculo = request.POST.get('placa_veiculo')
        )
        
        messages.success(request, 'O visitante foi cadastrado com sucesso!')
        return redirect('home')


    ultimos_visitantes = Visitante.objects.order_by('-horario_chegada')[:10]

    contexto = {
        'lista_visitantes': ultimos_visitantes
    }
    
    return render(request, 'index.html', contexto)

@login_required
def registrar_saida(request, id_visitante):
    
    visitante = get_object_or_404(Visitante, id=id_visitante)
    
    
    visitante.horario_saida = timezone.now()
    visitante.save()
    
    messages.success(request, 'Saída registrada com sucesso!')
    
    return redirect('home')