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
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.cache import never_cache
from django_ratelimit.decorators import ratelimit
from .models import Visitante, Morador, Encomenda, Solicitacao, Notificacao, Sindico, Porteiro, Condominio, Mensagem

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

def is_porteiro(user):
    """Verifica se o usuário é porteiro (staff ou grupo Portaria/tipo)"""
    if user.is_superuser:
        return True
    return getattr(user, 'tipo_usuario', '') == 'porteiro' or user.is_staff or user.groups.filter(name='Portaria').exists()


def get_condominio_porteiro(user):
    """
    Retorna o Condominio vinculado ao usuário logado.
    """
    return getattr(user, 'condominio', None)


@never_cache
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/admin/')
            
        # Redireciona baseado no tipo de usuário
        if getattr(request.user, 'tipo_usuario', '') == 'morador':
            if not hasattr(request.user, 'morador') or not request.user.morador:
                logout(request)
                messages.error(request, "Seu usuário ainda não possui um perfil de morador gerado. Contate a administração.")
                return redirect('login')
            return redirect('morador_home')
        if getattr(request.user, 'tipo_usuario', '') == 'sindico':
            condominio = getattr(request.user, 'condominio', None)
            if not condominio and hasattr(request.user, 'sindico'):
                condominio = getattr(request.user.sindico, 'condominio', None)
                
            if not condominio:
                logout(request)
                messages.error(request, "Seu usuário síndico não está vinculado a nenhum condomínio. Contate a administração.")
                return redirect('login')
            return redirect('sindico_home')
        if is_porteiro(request.user):
            return redirect('home')
        # Usuário sem perfil definido — evita loop
        logout(request)
        messages.error(request, "Seu usuário não possui perfil configurado. Contacte o administrador.")
        return redirect('login')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser or user.is_staff:
                return redirect('/admin/')
                
            # Redireciona baseado no perfil
            if getattr(user, 'tipo_usuario', '') == 'morador':
                if not hasattr(user, 'morador') or not user.morador:
                    logout(request)
                    messages.error(request, "Seu usuário ainda não possui um perfil de morador gerado. Contate a administração.")
                    return redirect('login')
                return redirect('morador_home')
            if getattr(user, 'tipo_usuario', '') == 'sindico':
                condominio = getattr(user, 'condominio', None)
                if not condominio and hasattr(user, 'sindico'):
                    condominio = getattr(user.sindico, 'condominio', None)
                    
                if not condominio:
                    logout(request)
                    messages.error(request, "Seu usuário síndico não está vinculado a nenhum condomínio. Contate a administração.")
                    return redirect('login')
                return redirect('sindico_home')
            if is_porteiro(user):
                return redirect('home')
            # Usuário sem perfil — faz logout e avisa
            logout(request)
            messages.error(request, "Seu usuário não possui perfil configurado. Contacte o administrador.")
            return redirect('login')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@never_cache
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def alterar_senha(request):
    """Permite ao usuário logado alterar sua própria senha"""
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha', '')
        confirmar_senha = request.POST.get('confirmar_senha', '')
        
        if len(nova_senha) < 6:
            messages.error(request, "A nova senha deve ter pelo menos 6 caracteres.")
        elif nova_senha != confirmar_senha:
            messages.error(request, "As senhas não coincidem.")
        else:
            request.user.set_password(nova_senha)
            request.user.save()
            login(request, request.user)
            messages.success(request, "Senha alterada com sucesso!")
            
            if getattr(request.user, 'tipo_usuario', '') == 'morador':
                return redirect('morador_home')
            if getattr(request.user, 'tipo_usuario', '') == 'sindico':
                return redirect('sindico_home')
            return redirect('home')
    
    return render(request, 'alterar_senha.html')


@ensure_csrf_cookie
def cadastro_morador(request, codigo_convite):
    """Página pública de autocadastro de morador via link de convite"""
    from .models import Condominio, Morador
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    
    condominio = get_object_or_404(Condominio, codigo_convite=codigo_convite, ativo=True)
    form_data = {}
    
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        bloco = request.POST.get('bloco', '').strip()
        apartamento = request.POST.get('apartamento', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        form_data = {
            'nome': nome, 'bloco': bloco, 'apartamento': apartamento,
            'telefone': telefone, 'email': email, 'username': username
        }
        
        # Validações
        if not nome or not apartamento or not username or not password:
            messages.error(request, "Preencha todos os campos obrigatórios.")
        elif len(password) < 6:
            messages.error(request, "A senha deve ter pelo menos 6 caracteres.")
        elif password != password2:
            messages.error(request, "As senhas não coincidem.")
        elif UserModel.objects.filter(username=username).exists():
            messages.error(request, f"O usuário '{username}' já está em uso. Escolha outro.")
        elif Morador.objects.filter(condominio=condominio, bloco=bloco, apartamento=apartamento).exists():
            messages.error(request, f"Já existe um morador cadastrado no Bloco {bloco} Apto {apartamento}.")
        else:
            user_obj = UserModel.objects.create_user(
                username=username,
                password=password,
                first_name=nome.split()[0] if nome else '',
                email=email,
                tipo_usuario='morador',
                condominio=condominio
            )
            Morador.objects.create(
                condominio=condominio,
                nome=nome,
                bloco=bloco,
                apartamento=apartamento,
                telefone=telefone,
                email=email,
                usuario=user_obj
            )
            messages.success(request, f"Conta criada com sucesso! Faça login com '{username}'.")
            return redirect('login')
    
    return render(request, 'cadastro_morador.html', {
        'condominio': condominio,
        'form_data': form_data
    })


# ==========================================
# 3. API STATS (Polling AJAX)
# ==========================================

from django.http import JsonResponse

@login_required
def api_stats(request):
    """Retorna estatísticas em JSON para atualização via AJAX."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Não autorizado'}, status=403)
    
    cond = get_condominio_porteiro(request.user)
    visitantes_qs = Visitante.objects.all()
    encomendas_qs = Encomenda.objects.all()
    solicitacoes_qs = Solicitacao.objects.all()
    if cond:
        visitantes_qs = visitantes_qs.filter(condominio=cond)
        encomendas_qs = encomendas_qs.filter(condominio=cond)
        solicitacoes_qs = solicitacoes_qs.filter(condominio=cond)
    
    visitantes_no_local = visitantes_qs.filter(horario_saida__isnull=True).count()
    encomendas_pendentes = encomendas_qs.filter(entregue=False).count()
    solicitacoes_pendentes = solicitacoes_qs.filter(status='PENDENTE').count()
    
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
    if request.user.is_superuser or request.user.is_staff:
        # Admins can bypass the morador check and view the home if they want,
        # but usually they go to admin. Let them see home.
        pass
    # Se for morador, redireciona para o portal do morador
    elif getattr(request.user, 'tipo_usuario', '') == 'morador':
        if not hasattr(request.user, 'morador') or not getattr(request.user, 'morador'):
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "Seu usuário não possui um perfil de morador gerado. Contate a administração.")
            return redirect('login')
        return redirect('morador_home')
    
    # Só staff ou porteiros (grupo Portaria) podem acessar
    if getattr(request.user, 'tipo_usuario', '') == 'sindico':
        return redirect('sindico_home')
        
    if not is_porteiro(request.user):
        messages.error(request, "Você não tem permissão para acessar a portaria.")
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    if request.method == 'POST' and 'nome_completo' in request.POST:
        registrar_visitante(request)
        return redirect('home')

    cond = get_condominio_porteiro(request.user)
    query = request.GET.get('busca')
    
    visitantes_all = Visitante.objects.select_related('morador_responsavel').all().order_by('-horario_chegada')
    if cond:
        visitantes_all = visitantes_all.filter(condominio=cond)
    
    if query:
        visitantes_all = visitantes_all.filter(Q(nome_completo__icontains=query) | Q(cpf__icontains=query))

    paginator = Paginator(visitantes_all, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # CORREÇÃO AQUI TAMBÉM: Usamos localdate()
    hoje = localdate()
    base_visitantes = Visitante.objects.filter(condominio=cond) if cond else Visitante.objects.all()
    base_encomendas = Encomenda.objects.filter(condominio=cond) if cond else Encomenda.objects.all()
    base_solicitacoes = Solicitacao.objects.filter(condominio=cond) if cond else Solicitacao.objects.all()
    
    visitantes_hoje_total = base_visitantes.filter(horario_chegada__date=hoje).count()
    visitantes_no_local_count = base_visitantes.filter(horario_saida__isnull=True).count()
    
    encomendas_pendentes_count = base_encomendas.filter(entregue=False).count()
    solicitacoes_pendentes_count = base_solicitacoes.filter(status='PENDENTE').count()
    
    lista_encomendas = base_encomendas.filter(entregue=False).select_related('morador').order_by('-data_chegada')
    lista_solicitacoes = base_solicitacoes.select_related('morador').order_by('-data_criacao')[:50]
    todos_moradores = Morador.objects.filter(condominio=cond).order_by('bloco', 'apartamento') if cond else Morador.objects.all().order_by('bloco', 'apartamento')

    context = {
        'lista_visitantes': page_obj, 
        'visitantes_hoje_total': visitantes_hoje_total,
        'visitantes_no_local': visitantes_no_local_count,
        'encomendas_pendentes': encomendas_pendentes_count,
        'solicitacoes_pendentes': solicitacoes_pendentes_count,
        'lista_encomendas': lista_encomendas,
        'lista_solicitacoes': lista_solicitacoes,
        'todos_moradores': todos_moradores,
        'query_busca': query,
        'aba_ativa': request.GET.get('aba', 'visitantes'),
        'condominio_atual': cond,
    }
    return render(request, 'index.html', context)

@login_required
def mensagens_portaria(request):
    """View de caixa de entrada do Porteiro"""
    if not is_porteiro(request.user):
        messages.error(request, "Sem permissão.")
        return redirect('login')
    
    cond = get_condominio_porteiro(request.user)
    
    if request.method == 'POST':
        dest_id = request.POST.get('destinatario')
        conteudo = request.POST.get('conteudo')
        resposta_a_id = request.POST.get('resposta_a')
        
        reply_to = None
        if resposta_a_id:
            reply_to = Mensagem.objects.filter(id=resposta_a_id).first()
            
        if dest_id and conteudo:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            destinatario = User.objects.get(id=dest_id)
            Mensagem.objects.create(
                condominio=cond,
                remetente=request.user,
                destinatario=destinatario,
                conteudo=conteudo,
                resposta_a=reply_to
            )
            messages.success(request, "Mensagem enviada.")
            return redirect('mensagens_portaria')
            
    # Marcar recebidas como lidas
    Mensagem.objects.filter(destinatario=request.user, lida=False).update(lida=True)
    
    mensagens = Mensagem.objects.filter(
        Q(remetente=request.user) | Q(destinatario=request.user)
    ).select_related('remetente', 'destinatario', 'resposta_a').order_by('data_envio')
    
    moradores = Morador.objects.filter(condominio=cond).select_related('usuario')
    sindicos = Sindico.objects.filter(condominio=cond).select_related('usuario')
    
    destinatarios = []
    for m in moradores:
        if m.usuario: destinatarios.append(m.usuario)
    for s in sindicos:
        if s.usuario: destinatarios.append(s.usuario)
        
    # Agrupar mensagens por contato (WhatsApp style simplificado)
    conversas = {}
    for msg in mensagens:
        other_user = msg.destinatario if msg.remetente == request.user else msg.remetente
        if other_user not in conversas:
            conversas[other_user] = []
        conversas[other_user].append(msg)
        
    mensagens_nao_lidas = 0 # Na portaria as lidas sao marcadas na hora, entao zera
    
    context = {
        'aba_ativa': 'mensagens',
        'conversas': conversas,
        'destinatarios': destinatarios,
        'mensagens_nao_lidas': mensagens_nao_lidas
    }
    return render(request, 'mensagens_portaria.html', context)

@login_required
def registrar_visitante(request):
    if request.method == 'POST':
        morador_id = request.POST.get('morador_responsavel')
        morador = Morador.objects.get(id=morador_id) if morador_id else None
        cond = get_condominio_porteiro(request.user)
        # Se o morador tem condomínio, usar esse; senão usar o do porteiro
        condominio_registro = (morador.condominio if morador and morador.condominio else cond)
        
        Visitante.objects.create(
            condominio=condominio_registro,
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
            morador = Morador.objects.get(id=morador_id)
            cond = morador.condominio or get_condominio_porteiro(request.user)
            Encomenda.objects.create(
                condominio=cond,
                morador=morador,
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
    cond = get_condominio_porteiro(request.user)
    if cond:
        encomendas_list = encomendas_list.filter(condominio=cond)
    
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
        cond = (morador.condominio if morador and morador.condominio else get_condominio_porteiro(request.user))
        solicitacao = Solicitacao.objects.create(
            condominio=cond,
            tipo=request.POST.get('tipo'),
            descricao=request.POST.get('descricao'),
            morador=morador,
            criado_por=request.user
        )

        # Notificar síndicos do condomínio
        if cond:
            sindicos = Sindico.objects.filter(condominio=cond)
            notificacoes = [
                Notificacao(
                    usuario=s.usuario,
                    tipo='solicitacao',
                    mensagem=f'Porteiro {request.user.get_full_name() or request.user.username}: solicitação #{solicitacao.id}',
                    link='/sindico/solicitacoes/'
                ) for s in sindicos if s.usuario
            ]
            Notificacao.objects.bulk_create(notificacoes)

        messages.success(request, "Solicitação registrada!")
    return redirect('/?aba=solicitacoes')

@login_required
def historico_solicitacoes(request):
    solicitacoes_list = Solicitacao.objects.select_related('morador').all().order_by('-data_criacao')
    cond = get_condominio_porteiro(request.user)
    if cond:
        solicitacoes_list = solicitacoes_list.filter(condominio=cond)
    
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


# ==========================================
# 7. API OFFLINE (Sincronização)
# ==========================================

import json

@login_required
def api_moradores_offline(request):
    """Retorna lista de moradores em JSON para cache offline no navegador."""
    cond = get_condominio_porteiro(request.user)
    qs = Morador.objects.all().order_by('bloco', 'apartamento')
    if cond:
        qs = qs.filter(condominio=cond)
    moradores = qs.values('id', 'nome', 'bloco', 'apartamento', 'telefone')
    return JsonResponse({'moradores': list(moradores), 'porteiro': request.user.username})


@csrf_exempt
@login_required
def api_sync_offline(request):
    """
    Recebe dados coletados offline (visitantes e encomendas) e cria os registros
    no banco de dados, atribuindo ao porteiro logado (request.user).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    resultados = {'visitantes_criados': 0, 'encomendas_criadas': 0, 'solicitacoes_criadas': 0, 'erros': []}

    cond = get_condominio_porteiro(request.user)

    # --- Sincronizar Visitantes ---
    for i, v in enumerate(data.get('visitantes', [])):
        try:
            morador = None
            if v.get('morador_id'):
                morador = Morador.objects.get(id=v['morador_id'])

            condominio_reg = (morador.condominio if morador and morador.condominio else cond)
            Visitante.objects.create(
                condominio=condominio_reg,
                nome_completo=v.get('nome_completo', 'Sem nome'),
                cpf=v.get('cpf', ''),
                data_nascimento=v.get('data_nascimento') or None,
                placa_veiculo=v.get('placa_veiculo', ''),
                morador_responsavel=morador,
                quem_autorizou=v.get('quem_autorizou', ''),
                observacoes=v.get('observacoes', '') + ' [Registrado offline]',
                registrado_por=request.user
            )
            resultados['visitantes_criados'] += 1
        except Exception as e:
            resultados['erros'].append(f'Visitante #{i+1}: {str(e)}')

    # --- Sincronizar Encomendas ---
    for i, e in enumerate(data.get('encomendas', [])):
        try:
            morador = Morador.objects.get(id=e['morador_id'])
            condominio_reg = morador.condominio or cond
            Encomenda.objects.create(
                condominio=condominio_reg,
                morador=morador,
                volume=e.get('volume', 'Sem descrição'),
                destinatario_alternativo=e.get('destinatario_alternativo', ''),
                porteiro_cadastro=request.user
            )
            resultados['encomendas_criadas'] += 1
        except Exception as ex:
            resultados['erros'].append(f'Encomenda #{i+1}: {str(ex)}')

    # --- Sincronizar Solicitações ---
    for i, s in enumerate(data.get('solicitacoes', [])):
        try:
            morador = None
            if s.get('morador_id'):
                morador = Morador.objects.get(id=s['morador_id'])

            solicitacao = Solicitacao.objects.create(
                condominio=(morador.condominio if morador and morador.condominio else cond),
                tipo=s.get('tipo', 'OUTRO'),
                descricao=s.get('descricao', '') + ' [Registrado offline]',
                morador=morador,
                criado_por=request.user
            )

            # Notificar síndicos do condomínio (mesma lógica da view normal)
            solicitacao_cond = solicitacao.condominio
            if solicitacao_cond:
                sindicos = Sindico.objects.filter(condominio=solicitacao_cond)
                notificacoes = [
                    Notificacao(
                        usuario=sind.usuario,
                        tipo='solicitacao',
                        mensagem=f'Porteiro {request.user.get_full_name() or request.user.username}: solicitação #{solicitacao.id} [offline]',
                        link='/sindico/solicitacoes/'
                    ) for sind in sindicos if sind.usuario
                ]
                Notificacao.objects.bulk_create(notificacoes)

            resultados['solicitacoes_criadas'] += 1
        except Exception as ex:
            resultados['erros'].append(f'Solicitação #{i+1}: {str(ex)}')

    resultados['ok'] = len(resultados['erros']) == 0
    resultados['porteiro'] = request.user.username
    return JsonResponse(resultados)