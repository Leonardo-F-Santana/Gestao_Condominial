from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from datetime import date
from portaria.models import Condominio, CustomUser, Aviso
from portaria.models_zelador import (
    ChecklistZelador, OrdemServicoZelador, AgendaZelador, 
    LivroOcorrenciaZelador, PrestadorServicoZelador, EstoqueZelador
)

def is_zelador(user):
    return user.is_authenticated and getattr(user, 'tipo_usuario', '') == 'zelador'

def get_condominio(user):
    return user.get_condominio_ativo

@login_required
def zelador_home(request):
    if not is_zelador(request.user):
        return redirect('home')

    cond = get_condominio(request.user)
    if not cond:
        messages.error(request, 'Usuário zelador não associado a nenhum condomínio.')
        return redirect('login')

    os_pendentes = OrdemServicoZelador.objects.filter(condominio=cond, status__in=['ABERTA', 'EM_ANDAMENTO']).count()
    checklists_hoje = ChecklistZelador.objects.filter(condominio=cond, concluido=False).count()
    alertas_estoque = EstoqueZelador.objects.filter(
        condominio=cond, 
        quantidade_atual__lte=F('quantidade_minima')
    ).count()

    context = {
        'condominio': cond,
        'os_pendentes': os_pendentes,
        'checklists_hoje': checklists_hoje,
        'alertas_estoque': alertas_estoque,
    }
    return render(request, 'zelador/home_zelador.html', context)

@login_required
def checklists_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        ChecklistZelador.objects.create(
            condominio=cond, titulo=titulo, descricao=descricao, zelador=request.user
        )
        messages.success(request, 'Checklist adicionado.')
        return redirect('zelador_checklists')

    checklists = ChecklistZelador.objects.filter(condominio=cond).order_by('concluido', '-data_criacao')
    return render(request, 'zelador/checklists_zelador.html', {'checklists': checklists})

@login_required
def concluir_checklist(request, pk):
    if not is_zelador(request.user): return redirect('home')
    chk = get_object_or_404(ChecklistZelador, pk=pk, condominio=get_condominio(request.user))
    chk.concluido = True
    from django.utils import timezone
    chk.data_conclusao = timezone.now()
    chk.save()
    messages.success(request, 'Checklist concluído!')
    return redirect('zelador_checklists')

@login_required
def ordens_servico_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)

    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao')
            foto = request.FILES.get('foto')

            os = OrdemServicoZelador(
                condominio=cond, titulo=titulo, descricao=descricao, zelador=request.user
            )
            if foto:
                if foto.size > 5242880:
                    messages.error(request, 'A foto excede o limite de 5MB.')
                    return redirect('zelador_os')
                os.foto = foto
            os.save()
            messages.success(request, 'Ordem de serviço aberta.')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
        return redirect('zelador_os')

    ordens = OrdemServicoZelador.objects.filter(condominio=cond).order_by('-data_abertura')
    return render(request, 'zelador/ordens_servico_zelador.html', {'ordens': ordens})

@login_required
def mudar_status_os(request, pk):
    if not is_zelador(request.user): return redirect('home')
    os = get_object_or_404(OrdemServicoZelador, pk=pk, condominio=get_condominio(request.user))
    novo_status = request.POST.get('status')
    if novo_status in ['ABERTA', 'EM_ANDAMENTO', 'CONCLUIDA']:
        os.status = novo_status
        if novo_status == 'CONCLUIDA':
            from django.utils import timezone
            os.data_encerramento = timezone.now()
        os.save()
        messages.success(request, 'Status atualizado.')
    return redirect('zelador_os')

@login_required
def agenda_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        data_man = request.POST.get('data')
        descricao = request.POST.get('descricao')
        AgendaZelador.objects.create(
            condominio=cond, titulo=titulo, data_manutencao=data_man, descricao=descricao
        )
        messages.success(request, 'Agendamento criado.')
        return redirect('zelador_agenda')

    agendas = AgendaZelador.objects.filter(condominio=cond).order_by('data_manutencao')
    return render(request, 'zelador/agenda_zelador.html', {'agendas': agendas})

@login_required
def livro_ocorrencias_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)

    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao')
            gravidade = request.POST.get('gravidade')
            foto = request.FILES.get('foto')

            ocorrencia = LivroOcorrenciaZelador(
                condominio=cond, titulo=titulo, descricao=descricao, 
                gravidade=gravidade, zelador=request.user
            )
            if foto:
                if foto.size > 5242880:
                    messages.error(request, 'A foto excede o limite de 5MB.')
                    return redirect('zelador_ocorrencias')
                ocorrencia.foto = foto
            ocorrencia.save()
            messages.success(request, 'Ocorrência registrada.')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
        return redirect('zelador_ocorrencias')

    ocorrencias = LivroOcorrenciaZelador.objects.filter(condominio=cond).order_by('-data_registro')
    return render(request, 'zelador/livro_ocorrencias_zelador.html', {'ocorrencias': ocorrencias})

@login_required
def avisos_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        conteudo = request.POST.get('conteudo')
        Aviso.objects.create(
            condominio=cond, titulo=titulo, conteudo=conteudo, 
            criado_por=request.user, ativo=True
        )
        messages.success(request, 'Aviso publicado.')
        return redirect('zelador_avisos')

    avisos = Aviso.objects.filter(condominio=cond).order_by('-data_publicacao')
    return render(request, 'zelador/avisos_zelador.html', {'avisos': avisos})

@login_required
def prestadores_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        empresa = request.POST.get('empresa')
        documento = request.POST.get('documento')
        PrestadorServicoZelador.objects.create(
            condominio=cond, nome=nome, empresa=empresa, 
            documento=documento, liberado_por=request.user
        )
        messages.success(request, 'Entrada de prestador registrada.')
        return redirect('zelador_prestadores')

    prestadores = PrestadorServicoZelador.objects.filter(condominio=cond).order_by('-data_entrada')
    return render(request, 'zelador/prestadores_zelador.html', {'prestadores': prestadores})

@login_required
def estoque_zelador(request):
    if not is_zelador(request.user): return redirect('home')
    cond = get_condominio(request.user)
    from django.db.models import F

    if request.method == 'POST':
        nome = request.POST.get('nome')
        qtd = request.POST.get('quantidade_atual')
        minima = request.POST.get('quantidade_minima')
        EstoqueZelador.objects.create(
            condominio=cond, nome=nome, quantidade_atual=qtd, quantidade_minima=minima
        )
        messages.success(request, 'Item adicionado ao estoque.')
        return redirect('zelador_estoque')

    itens = EstoqueZelador.objects.filter(condominio=cond).order_by('nome')
    return render(request, 'zelador/estoque_zelador.html', {'itens': itens})

@login_required
def atualizar_estoque(request, pk):
    if not is_zelador(request.user): return redirect('home')
    item = get_object_or_404(EstoqueZelador, pk=pk, condominio=get_condominio(request.user))
    qtd = request.POST.get('quantidade_atual')
    if qtd is not None:
        item.quantidade_atual = int(qtd)
        item.save()
        messages.success(request, 'Estoque atualizado.')
    return redirect('zelador_estoque')
