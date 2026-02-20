from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Condominio, Sindico, Morador, Visitante, Encomenda, Solicitacao, Aviso, Notificacao, AreaComum, Reserva


def is_sindico(user):
    """Verifica se o usuário é um síndico"""
    return hasattr(user, 'sindico')


def get_condominio_ativo(request):
    """Retorna o condomínio ativo da sessão"""
    cond_id = request.session.get('condominio_ativo_id')
    if cond_id:
        try:
            return Condominio.objects.get(id=cond_id)
        except Condominio.DoesNotExist:
            return None
    return None


def sindico_context(request, extra=None, active_page=''):
    """Contexto base para todas as views do síndico"""
    ctx = {
        'condominio': get_condominio_ativo(request),
        'active_page': active_page,
    }
    if extra:
        ctx.update(extra)
    return ctx


# ==========================================
# SELEÇÃO DE CONDOMÍNIO
# ==========================================

@login_required
def portal_sindico_home(request):
    """Lista de condomínios"""
    if not is_sindico(request.user):
        messages.error(request, "Você não tem permissão de síndico.")
        return redirect('home')
    
    sindico = request.user.sindico
    condominios = sindico.condominios.filter(ativo=True)
    
    condominios_stats = []
    for cond in condominios:
        stats = {
            'condominio': cond,
            'moradores': Morador.objects.filter(condominio=cond).count(),
            'encomendas_pendentes': Encomenda.objects.filter(
                morador__condominio=cond, entregue=False
            ).count(),
            'solicitacoes_pendentes': Solicitacao.objects.filter(
                morador__condominio=cond, status='PENDENTE'
            ).count(),
        }
        condominios_stats.append(stats)
    
    return render(request, 'sindico/portal_home.html', {
        'sindico': sindico,
        'condominios_stats': condominios_stats,
    })


@login_required
def selecionar_condominio(request, condominio_id):
    """Seleciona condomínio e salva na sessão"""
    if not is_sindico(request.user):
        return redirect('home')
    
    sindico = request.user.sindico
    condominio = get_object_or_404(Condominio, id=condominio_id)
    
    if condominio not in sindico.condominios.all():
        messages.error(request, "Sem acesso a este condomínio.")
        return redirect('sindico_home')
    
    request.session['condominio_ativo_id'] = condominio.id
    return redirect('sindico_painel')


@login_required
def criar_condominio(request):
    """Criar novo condomínio"""
    if not is_sindico(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        if not nome:
            messages.error(request, "Nome é obrigatório.")
            return redirect('sindico_criar_condominio')
        
        cond = Condominio.objects.create(
            nome=nome,
            endereco=request.POST.get('endereco', '').strip(),
            cnpj=request.POST.get('cnpj', '').strip(),
            telefone=request.POST.get('telefone', '').strip(),
            email=request.POST.get('email', '').strip()
        )
        request.user.sindico.condominios.add(cond)
        request.session['condominio_ativo_id'] = cond.id
        messages.success(request, f"Condomínio '{nome}' criado!")
        return redirect('sindico_painel')
    
    return render(request, 'sindico/criar_condominio.html')


# ==========================================
# PAINEL
# ==========================================

@login_required
def painel_sindico(request):
    """Dashboard do condomínio selecionado"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    sindico = request.user.sindico
    if condominio not in sindico.condominios.all():
        request.session.pop('condominio_ativo_id', None)
        return redirect('sindico_home')
    
    stats = {
        'moradores': Morador.objects.filter(condominio=condominio).count(),
        'visitantes_hoje': Visitante.objects.filter(
            morador_responsavel__condominio=condominio,
            horario_chegada__date=timezone.now().date()
        ).count(),
        'visitantes_no_local': Visitante.objects.filter(
            morador_responsavel__condominio=condominio,
            horario_saida__isnull=True
        ).count(),
        'encomendas_pendentes': Encomenda.objects.filter(
            morador__condominio=condominio, entregue=False
        ).count(),
        'solicitacoes_pendentes': Solicitacao.objects.filter(
            morador__condominio=condominio, status='PENDENTE'
        ).count(),
    }
    
    ctx = sindico_context(request, {
        'stats': stats,
        'ultimos_visitantes': Visitante.objects.filter(
            morador_responsavel__condominio=condominio
        ).order_by('-horario_chegada')[:5],
        'ultimas_encomendas': Encomenda.objects.filter(
            morador__condominio=condominio, entregue=False
        ).order_by('-data_chegada')[:5],
        'ultimas_solicitacoes': Solicitacao.objects.filter(
            morador__condominio=condominio
        ).order_by('-data_criacao')[:5],
    }, active_page='painel')
    
    return render(request, 'sindico/painel.html', ctx)


# ==========================================
# MORADORES
# ==========================================

@login_required
def moradores_sindico(request):
    """Gestão de moradores com criação de usuário e importação em massa"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    if request.method == 'POST':
        action = request.POST.get('action', 'cadastrar')
        
        if action == 'importar':
            # Importação em massa (Excel / CSV)
            arquivo = request.FILES.get('arquivo')
            if not arquivo:
                messages.error(request, "Nenhum arquivo selecionado.")
                return redirect('sindico_moradores')
            
            nome_arquivo = arquivo.name.lower()
            rows = []
            
            try:
                if nome_arquivo.endswith('.xlsx'):
                    import openpyxl
                    wb = openpyxl.load_workbook(arquivo, read_only=True)
                    ws = wb.active
                    for i, row in enumerate(ws.iter_rows(values_only=True)):
                        if i == 0:  # pular cabeçalho
                            continue
                        if row and any(row):
                            rows.append([str(c).strip() if c else '' for c in row])
                    wb.close()
                elif nome_arquivo.endswith('.xls'):
                    import xlrd
                    wb = xlrd.open_workbook(file_contents=arquivo.read())
                    ws = wb.sheet_by_index(0)
                    for i in range(1, ws.nrows):  # pular cabeçalho
                        row = [str(ws.cell_value(i, j)).strip() for j in range(ws.ncols)]
                        if any(row):
                            rows.append(row)
                elif nome_arquivo.endswith('.csv'):
                    import csv, io
                    content = arquivo.read().decode('utf-8-sig')
                    reader = csv.reader(io.StringIO(content), delimiter=';')
                    for i, row in enumerate(reader):
                        if i == 0:
                            # Tentar detectar delimitador
                            if len(row) == 1 and ',' in row[0]:
                                content = arquivo.read().decode('utf-8-sig') if hasattr(arquivo, 'read') else content
                                reader = csv.reader(io.StringIO(content), delimiter=',')
                                continue
                            continue
                        if any(row):
                            rows.append([c.strip() for c in row])
                else:
                    messages.error(request, "Formato não suportado. Use .xlsx, .xls ou .csv")
                    return redirect('sindico_moradores')
            except Exception as e:
                messages.error(request, f"Erro ao ler o arquivo: {e}")
                return redirect('sindico_moradores')
            
            total = 0
            erros = 0
            for row in rows:
                try:
                    nome = row[0] if len(row) > 0 else ''
                    apartamento = row[1] if len(row) > 1 else ''
                    bloco = row[2] if len(row) > 2 else ''
                    telefone = row[3] if len(row) > 3 else ''
                    email = row[4] if len(row) > 4 else ''
                    
                    if not nome or not apartamento:
                        erros += 1
                        continue
                    
                    Morador.objects.create(
                        condominio=condominio,
                        nome=nome,
                        bloco=bloco,
                        apartamento=apartamento,
                        telefone=telefone,
                        email=email,
                    )
                    total += 1
                except Exception:
                    erros += 1
            
            if total > 0:
                messages.success(request, f"{total} morador(es) importado(s) com sucesso!")
            if erros > 0:
                messages.warning(request, f"{erros} linha(s) ignorada(s) (dados incompletos ou erro).")
            return redirect('sindico_moradores')
        
        else:
            # Cadastro individual (form original)
            nome = request.POST.get('nome', '').strip()
            apartamento = request.POST.get('apartamento', '').strip()
            bloco = request.POST.get('bloco', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            email = request.POST.get('email', '').strip()
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            
            if nome and apartamento:
                user_obj = None
                if username and password:
                    if User.objects.filter(username=username).exists():
                        messages.error(request, f"Usuário '{username}' já existe.")
                        return redirect('sindico_moradores')
                    user_obj = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=nome.split()[0] if nome else '',
                        email=email
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
                messages.success(request, f"Morador '{nome}' cadastrado!")
                if user_obj:
                    messages.info(request, f"Login criado: {username}")
                return redirect('sindico_moradores')
    
    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')
    ctx = sindico_context(request, {'moradores': moradores}, active_page='moradores')
    return render(request, 'sindico/moradores.html', ctx)


# ==========================================
# RESET DE SENHA (pelo síndico)
# ==========================================

@login_required
def resetar_senha_morador(request, morador_id):
    """Síndico reseta a senha de um morador"""
    if not is_sindico(request.user) or request.method != 'POST':
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    morador = get_object_or_404(Morador, id=morador_id, condominio=condominio)
    
    nova_senha = request.POST.get('nova_senha', '').strip()
    
    if not nova_senha or len(nova_senha) < 6:
        messages.error(request, "A senha deve ter pelo menos 6 caracteres.")
        return redirect('sindico_moradores')
    
    if morador.usuario:
        morador.usuario.set_password(nova_senha)
        morador.usuario.save()
        messages.success(request, f"Senha de '{morador.nome}' alterada com sucesso!")
    else:
        # Cria um usuário para o morador se não tiver
        username = request.POST.get('username', '').strip()
        if not username:
            username = f"morador_{morador.id}"
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Usuário '{username}' já existe.")
            return redirect('sindico_moradores')
        
        user_obj = User.objects.create_user(
            username=username,
            password=nova_senha,
            first_name=morador.nome.split()[0] if morador.nome else '',
            email=morador.email or ''
        )
        morador.usuario = user_obj
        morador.save()
        messages.success(request, f"Conta criada para '{morador.nome}' com login: {username}")
    
    return redirect('sindico_moradores')


# ==========================================
# VISITANTES
# ==========================================

@login_required
def visitantes_sindico(request):
    """Controle de visitantes"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')
    visitantes_no_local = Visitante.objects.filter(
        morador_responsavel__condominio=condominio,
        horario_saida__isnull=True
    ).order_by('-horario_chegada')
    
    if request.method == 'POST' and 'registrar_entrada' in request.POST:
        nome = request.POST.get('nome', '').strip()
        morador_id = request.POST.get('morador_id')
        placa = request.POST.get('placa', '').strip()
        
        if nome:
            morador = Morador.objects.get(id=morador_id) if morador_id else None
            Visitante.objects.create(
                nome_completo=nome,
                morador_responsavel=morador,
                placa_veiculo=placa,
                registrado_por=request.user
            )
            messages.success(request, f"Entrada de '{nome}' registrada!")
            return redirect('sindico_visitantes')
    
    ctx = sindico_context(request, {
        'moradores': moradores,
        'visitantes_no_local': visitantes_no_local,
    }, active_page='visitantes')
    return render(request, 'sindico/visitantes.html', ctx)


@login_required
def registrar_saida_sindico(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    visitante.horario_saida = timezone.now()
    visitante.save()
    messages.success(request, f"Saída de '{visitante.nome_completo}' registrada!")
    return redirect('sindico_visitantes')


# ==========================================
# ENCOMENDAS
# ==========================================

@login_required
def encomendas_sindico(request):
    """Gestão de encomendas"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')
    encomendas_pendentes = Encomenda.objects.filter(
        morador__condominio=condominio, entregue=False
    ).order_by('-data_chegada')
    
    if request.method == 'POST' and 'registrar_encomenda' in request.POST:
        morador_id = request.POST.get('morador_id')
        volume = request.POST.get('volume', '').strip()
        if morador_id and volume:
            morador = Morador.objects.get(id=morador_id)
            Encomenda.objects.create(
                morador=morador, volume=volume, porteiro_cadastro=request.user
            )
            messages.success(request, f"Encomenda para '{morador.nome}' registrada!")
            return redirect('sindico_encomendas')
    
    ctx = sindico_context(request, {
        'moradores': moradores,
        'encomendas_pendentes': encomendas_pendentes,
    }, active_page='encomendas')
    return render(request, 'sindico/encomendas.html', ctx)


@login_required
def entregar_encomenda_sindico(request, encomenda_id):
    encomenda = get_object_or_404(Encomenda, id=encomenda_id)
    encomenda.entregue = True
    encomenda.data_entrega = timezone.now()
    encomenda.porteiro_entrega = request.user
    encomenda.quem_retirou = request.POST.get('quem_retirou', 'Morador')
    encomenda.save()
    messages.success(request, "Encomenda entregue!")
    return redirect('sindico_encomendas')


# ==========================================
# SOLICITAÇÕES
# ==========================================

@login_required
def solicitacoes_sindico(request):
    """Gestão de solicitações"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    # Marcar notificações de solicitações como lidas
    Notificacao.objects.filter(
        usuario=request.user, tipo='solicitacao', lida=False
    ).update(lida=True)
    
    solicitacoes = Solicitacao.objects.filter(
        morador__condominio=condominio
    ).order_by('-data_criacao')
    
    ctx = sindico_context(request, {'solicitacoes': solicitacoes}, active_page='solicitacoes')
    return render(request, 'sindico/solicitacoes.html', ctx)


@login_required
def responder_solicitacao_sindico(request, solicitacao_id):
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id)
    if request.method == 'POST':
        solicitacao.resposta_admin = request.POST.get('resposta', '').strip()
        solicitacao.status = request.POST.get('status', solicitacao.status)
        solicitacao.save()
        
        # Notificar o morador sobre a resposta
        if solicitacao.morador and solicitacao.morador.usuario:
            Notificacao.objects.create(
                usuario=solicitacao.morador.usuario,
                tipo='resposta_solicitacao',
                mensagem=f'Sua solicitação #{solicitacao.id} foi respondida',
                link=f'/morador/solicitacoes/{solicitacao.id}/'
            )
        
        messages.success(request, "Solicitação atualizada!")
    return redirect('sindico_solicitacoes')


# ==========================================
# AVISOS
# ==========================================

@login_required
def avisos_sindico(request):
    """Lista de avisos do condomínio"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    avisos = Aviso.objects.filter(condominio=condominio).order_by('-data_publicacao')
    ctx = sindico_context(request, {'avisos': avisos}, active_page='avisos')
    return render(request, 'sindico/avisos.html', ctx)


@login_required
def criar_aviso_sindico(request):
    """Criar novo aviso com upload de imagem"""
    if not is_sindico(request.user):
        return redirect('home')
    
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        conteudo = request.POST.get('conteudo', '').strip()
        data_exp = request.POST.get('data_expiracao', '').strip()
        imagem = request.FILES.get('imagem')
        arquivo = request.FILES.get('arquivo')
        
        if titulo and conteudo:
            aviso = Aviso.objects.create(
                condominio=condominio,
                titulo=titulo,
                conteudo=conteudo,
                criado_por=request.user,
                data_expiracao=data_exp if data_exp else None
            )
            if imagem:
                aviso.imagem = imagem
            if arquivo:
                aviso.arquivo = arquivo
            if imagem or arquivo:
                aviso.save()
            
            # Notificar todos os moradores do condomínio
            moradores = Morador.objects.filter(condominio=condominio, usuario__isnull=False)
            notificacoes = [
                Notificacao(
                    usuario=m.usuario,
                    tipo='aviso',
                    mensagem=f'Novo aviso: {titulo[:80]}',
                    link='/morador/avisos/'
                ) for m in moradores
            ]
            Notificacao.objects.bulk_create(notificacoes)
            
            messages.success(request, f"Aviso '{titulo}' publicado!")
    
    return redirect('sindico_avisos')


@login_required
def editar_aviso_sindico(request, aviso_id):
    """Editar aviso existente"""
    aviso = get_object_or_404(Aviso, id=aviso_id)
    
    if request.method == 'POST':
        aviso.titulo = request.POST.get('titulo', aviso.titulo).strip()
        aviso.conteudo = request.POST.get('conteudo', aviso.conteudo).strip()
        data_exp = request.POST.get('data_expiracao', '').strip()
        aviso.data_expiracao = data_exp if data_exp else None
        aviso.ativo = request.POST.get('ativo', '1') == '1'
        
        imagem = request.FILES.get('imagem')
        if imagem:
            aviso.imagem = imagem
        
        arquivo = request.FILES.get('arquivo')
        if arquivo:
            aviso.arquivo = arquivo
        
        aviso.save()
        messages.success(request, "Aviso atualizado!")
    
    return redirect('sindico_avisos')


@login_required
def excluir_aviso_sindico(request, aviso_id):
    """Excluir aviso"""
    aviso = get_object_or_404(Aviso, id=aviso_id)
    if request.method == 'POST':
        aviso.delete()
        messages.success(request, "Aviso excluído!")
    return redirect('sindico_avisos')


# ==========================================
# COMPATIBILIDADE
# ==========================================

def dashboard_condominio(request, condominio_id):
    """Redireciona para o novo fluxo"""
    if request.user.is_authenticated and is_sindico(request.user):
        request.session['condominio_ativo_id'] = condominio_id
        return redirect('sindico_painel')
    return redirect('sindico_home')


# ==========================================
# ÁREAS COMUNS
# ==========================================

@login_required
def areas_comuns_sindico(request):
    """CRUD de áreas comuns"""
    if not is_sindico(request.user):
        return redirect('home')

    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'criar':
            nome = request.POST.get('nome', '').strip()
            descricao = request.POST.get('descricao', '')
            capacidade = request.POST.get('capacidade', 0)
            horario_abertura = request.POST.get('horario_abertura', '08:00')
            horario_fechamento = request.POST.get('horario_fechamento', '22:00')
            imagem = request.FILES.get('imagem')

            if nome:
                area = AreaComum.objects.create(
                    condominio=condominio,
                    nome=nome,
                    descricao=descricao,
                    capacidade=int(capacidade) if capacidade else 0,
                    horario_abertura=horario_abertura,
                    horario_fechamento=horario_fechamento,
                )
                if imagem:
                    area.imagem = imagem
                    area.save()
                messages.success(request, f'Área "{nome}" cadastrada com sucesso!')
            else:
                messages.error(request, 'Informe o nome da área.')

        elif action == 'editar':
            area_id = request.POST.get('area_id')
            area = get_object_or_404(AreaComum, id=area_id, condominio=condominio)
            area.nome = request.POST.get('nome', area.nome)
            area.descricao = request.POST.get('descricao', area.descricao)
            area.capacidade = int(request.POST.get('capacidade', area.capacidade) or 0)
            area.horario_abertura = request.POST.get('horario_abertura', area.horario_abertura)
            area.horario_fechamento = request.POST.get('horario_fechamento', area.horario_fechamento)
            area.ativo = request.POST.get('ativo') == 'on'
            if request.FILES.get('imagem'):
                area.imagem = request.FILES['imagem']
            area.save()
            messages.success(request, f'Área "{area.nome}" atualizada!')

        return redirect('sindico_areas_comuns')

    areas = AreaComum.objects.filter(condominio=condominio)
    context = sindico_context(request, {
        'areas': areas,
    }, active_page='reservas')
    return render(request, 'sindico/areas_comuns.html', context)


@login_required
def excluir_area_sindico(request, area_id):
    """Excluir área comum"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    area = get_object_or_404(AreaComum, id=area_id, condominio=condominio)
    nome = area.nome
    area.delete()
    messages.success(request, f'Área "{nome}" excluída!')
    return redirect('sindico_areas_comuns')


# ==========================================
# RESERVAS (SÍNDICO)
# ==========================================

@login_required
def reservas_sindico(request):
    """Listagem de reservas com filtros"""
    if not is_sindico(request.user):
        return redirect('home')

    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')

    # Marcar notificações de reserva como lidas
    Notificacao.objects.filter(
        usuario=request.user, tipo='reserva', lida=False
    ).update(lida=True)

    # Criar área comum direto da tela de reservas
    if request.method == 'POST' and request.POST.get('action') == 'criar_area':
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '')
        capacidade = request.POST.get('capacidade', 0)
        horario_abertura = request.POST.get('horario_abertura', '08:00')
        horario_fechamento = request.POST.get('horario_fechamento', '22:00')
        imagem = request.FILES.get('imagem')

        if nome:
            area = AreaComum.objects.create(
                condominio=condominio,
                nome=nome,
                descricao=descricao,
                capacidade=int(capacidade) if capacidade else 0,
                horario_abertura=horario_abertura,
                horario_fechamento=horario_fechamento,
            )
            if imagem:
                area.imagem = imagem
                area.save()
            messages.success(request, f'Área "{nome}" cadastrada com sucesso!')
        else:
            messages.error(request, 'Informe o nome da área.')
        return redirect('sindico_reservas')

    reservas_list = Reserva.objects.filter(
        area__condominio=condominio
    ).select_related('area', 'morador')

    # Filtros
    status = request.GET.get('status')
    if status:
        reservas_list = reservas_list.filter(status=status)

    context = sindico_context(request, {
        'reservas': reservas_list,
        'status_filtro': status,
    }, active_page='reservas')
    return render(request, 'sindico/reservas.html', context)


@login_required
def aprovar_reserva_sindico(request, reserva_id):
    """Aprovar uma reserva"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    reserva = get_object_or_404(Reserva, id=reserva_id, area__condominio=condominio)
    reserva.status = 'APROVADA'
    reserva.save()

    # Notificar morador
    if reserva.morador.usuario:
        Notificacao.objects.create(
            usuario=reserva.morador.usuario,
            tipo='reserva',
            mensagem=f'Sua reserva de {reserva.area.nome} para {reserva.data.strftime("%d/%m")} foi aprovada! ✅',
            link='/morador/reservas/'
        )

    messages.success(request, 'Reserva aprovada!')
    return redirect('sindico_reservas')


@login_required
def recusar_reserva_sindico(request, reserva_id):
    """Recusar uma reserva"""
    condominio = get_condominio_ativo(request)
    if not condominio:
        return redirect('sindico_home')
    reserva = get_object_or_404(Reserva, id=reserva_id, area__condominio=condominio)
    reserva.status = 'RECUSADA'
    reserva.motivo_recusa = request.POST.get('motivo', '')
    reserva.save()

    # Notificar morador
    if reserva.morador.usuario:
        Notificacao.objects.create(
            usuario=reserva.morador.usuario,
            tipo='reserva',
            mensagem=f'Sua reserva de {reserva.area.nome} para {reserva.data.strftime("%d/%m")} foi recusada.',
            link='/morador/reservas/'
        )

    messages.success(request, 'Reserva recusada.')
    return redirect('sindico_reservas')
