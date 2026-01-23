from django.shortcuts import render, redirect
from django.contrib import messages 
from .models import Visitante

def home(request):
    if request.method == "POST":
        Visitante.objects.create(
            nome_completo = request.POST.get('nome_completo'),
            cpf = request.POST.get('cpf'),
            data_nascimento = request.POST.get('data_nascimento'),
            numero_casa = request.POST.get('numero_casa'),
            placa_veiculo = request.POST.get('placa_veiculo')
        )
        
    
        messages.success(request, 'Visitante foi cadastrado com sucesso!')
        
        return redirect('home')

    return render(request, 'index.html')