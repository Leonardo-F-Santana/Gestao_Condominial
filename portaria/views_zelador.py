from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from datetime import date
from portaria.models import Condominio, CustomUser, Aviso, OrdemServico
from portaria.models_zelador import (
    ChecklistZelador, AgendaZelador, 
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

    os_pendentes = OrdemServico.objects.filter(condominio=cond, status__in=['Pendente', 'Em Andamento']).count()
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
def zelador_notificacoes(request):
    if not is_zelador(request.user): return redirect('home')
    
    from portaria.models import Notificacao
    
    notificacoes_todas = Notificacao.objects.filter(usuario=request.user).order_by('-data_criacao')
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    
    return render(request, 'zelador/notificacoes_zelador.html', {
        'notificacoes_lista': notificacoes_todas
    })

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

            os = OrdemServico(
                condominio=cond, titulo=titulo, descricao=descricao, zelador=request.user
            )
            if foto:
                if foto.size > 5242880:
                    messages.error(request, 'A foto excede o limite de 5MB.')
                    return redirect('zelador_os')
                os.foto_conclusao = foto
            os.save()
            messages.success(request, 'Ordem de serviço aberta.')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
        return redirect('zelador_os')

    ordens = OrdemServico.objects.filter(condominio=cond).order_by('-data_criacao')
    return render(request, 'zelador/ordens_servico_zelador.html', {'ordens': ordens})

@login_required
def mudar_status_os(request, pk):
    if not is_zelador(request.user): return redirect('home')
    os = get_object_or_404(OrdemServico, pk=pk, condominio=get_condominio(request.user))
    if os.status == 'Concluída':
        messages.error(request, 'Esta O.S. já está concluída e não pode ser alterada.')
        return redirect('zelador_os')

    novo_status = request.POST.get('status')
    if novo_status in ['Pendente', 'Em Andamento', 'Concluída']:
        os.status = novo_status
        if novo_status == 'Concluída':
            from django.utils import timezone
            os.data_conclusao = timezone.now()
            
            feedback = request.POST.get('feedback_texto')
            if feedback:
                os.feedback_texto = feedback
            
            foto = request.FILES.get('foto_conclusao')
            if foto:
                if foto.size > 5242880:
                    messages.error(request, 'A foto excede o limite de 5MB.')
                    return redirect('zelador_os')
                os.foto_conclusao = foto
        os.save()

        if novo_status == 'Concluída' and os.solicitacao_origem:
            sol = os.solicitacao_origem
            texto = "A Ordem de Serviço foi concluída pelo zelador."
            if os.feedback_texto:
                texto += f"\nFeedback do Zelador: {os.feedback_texto}"
            if not sol.resposta_admin:
                sol.resposta_admin = texto
            else:
                sol.resposta_admin += f"\n\n--- Atualização do Zelador ---\n{texto}"
            if os.foto_conclusao and not sol.arquivo:
                sol.arquivo = os.foto_conclusao
            sol.save(update_fields=['resposta_admin', 'arquivo'])

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

            from portaria.views_morador import notificar_sindicos_do_condominio
            notificar_sindicos_do_condominio(
                condominio=cond,
                tipo='ocorrencia',
                titulo='Nova Ocorrência',
                mensagem=f'O zelador {request.user.first_name or request.user.username} registrou uma nova ocorrência no Livro Digital.',
                link='/sindico/ocorrencias/'
            )

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
