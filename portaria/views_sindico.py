from django.shortcuts import render, redirect, get_object_or_404

from django.urls import reverse

from django.http import JsonResponse

from django.contrib.auth.decorators import login_required

from django.contrib.auth import get_user_model

from django.contrib import messages

from django.utils import timezone

from django.db import transaction

from django.db.models import Sum, Q

import json

from pywebpush import webpush, WebPushException

from django.conf import settings

from .models import Condominio, Sindico, Porteiro, Morador, Visitante, Encomenda, Solicitacao, Aviso, Notificacao, AreaComum, Reserva, Cobranca, Mensagem, Ocorrencia, PushSubscription, FeedbackMorador

from .utils import disparar_push_individual

User = get_user_model()

def is_sindico(user):

    pass

    print(f"DEBUG is_sindico: checking user {user.username}, tipo_usuario={getattr(user, 'tipo_usuario', None)}, hasattr sindico={hasattr(user, 'sindico')}")

    if getattr(user, 'tipo_usuario', '') == 'sindico':

        return True

    if hasattr(user, 'sindico'):

        return True

    return False

def get_condominio_ativo(request):

    pass

    condominio_id = request.session.get('condominio_ativo_id')

    if condominio_id and request.user.is_authenticated:

        c = request.user.condominios.filter(id=condominio_id).first()

        if c: return c

    condominio = getattr(request.user, 'get_condominio_ativo', None)

    if not condominio and hasattr(request.user, 'sindico'):

        condominio = request.user.sindico.condominio

    return condominio

def sindico_context(request, extra=None, active_page=''):

    pass

    condominio = get_condominio_ativo(request)

    context_data = {

        'condominio': condominio,

        'active_page': active_page,

    }

    if condominio and hasattr(request, 'user') and request.user.is_authenticated:

        unread_msgs = Mensagem.objects.filter(destinatario=request.user, lida=False).count()

        context_data['unread_mensagens_count'] = unread_msgs

    if extra:

        context_data.update(extra)

    return context_data

@login_required

def portal_sindico_home(request):

    pass

    if request.user.is_superuser:

        return redirect('admin:index')

    if not is_sindico(request.user):

        messages.error(request, "Você não tem permissão de síndico.")

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        messages.error(request, "Seu usuário síndico não está vinculado a um condomínio.")

        return redirect('home')

    return redirect('sindico_painel')

@login_required

def selecionar_condominio(request, condominio_id):

    return redirect('sindico_painel')

@login_required

def criar_condominio(request):

    return redirect('sindico_painel')

@login_required

def painel_sindico(request):

    pass

    if request.user.is_superuser:

        return redirect('admin:index')

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('home')

    sindico = getattr(request.user, 'sindico', None)

    stats = {

        'moradores': Morador.objects.filter(condominio=condominio).count(),

        'solicitacoes_pendentes': Solicitacao.objects.filter(

            condominio=condominio, status='PENDENTE'

        ).count(),

        'cobrancas_pagas': Cobranca.objects.filter(

            condominio=condominio, status='PAGO'

        ).count(),

        'cobrancas_pendentes': Cobranca.objects.filter(

            condominio=condominio, status__in=['PENDENTE', 'ATRASADO']

        ).count(),

    }

    ctx = sindico_context(request, {

        'stats': stats,

        'ultimas_solicitacoes': Solicitacao.objects.filter(

            condominio=condominio

        ).order_by('-data_criacao')[:5],

    }, active_page='painel')

    return render(request, 'sindico/painel.html', ctx)

@login_required

def moradores_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    if request.method == 'POST':

        action = request.POST.get('action', 'cadastrar')

        if action == 'importar':

            arquivo = request.FILES.get('arquivo')

            if not arquivo:

                messages.error(request, "Nenhum arquivo selecionado.")

                return redirect('sindico_moradores')

            content_type = getattr(arquivo, 'content_type', '')

            if content_type.startswith('video/') or str(arquivo.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                messages.error(request, "O envio de vídeos não é permitido. Envie apenas planilhas (.xlsx, .xls, .csv).")

                return redirect('sindico_moradores')

            nome_arquivo = arquivo.name.lower()

            rows = []

            try:

                if nome_arquivo.endswith('.xlsx'):

                    import openpyxl

                    wb = openpyxl.load_workbook(arquivo, read_only=True)

                    ws = wb.active

                    for i, row in enumerate(ws.iter_rows(values_only=True)):

                        if i == 0:                   

                            continue

                        if row and any(row):

                            rows.append([str(c).strip() if c else '' for c in row])

                    wb.close()

                elif nome_arquivo.endswith('.xls'):

                    import xlrd

                    wb = xlrd.open_workbook(file_contents=arquivo.read())

                    ws = wb.sheet_by_index(0)

                    for i in range(1, ws.nrows):                   

                        row = [str(ws.cell_value(i, j)).strip() for j in range(ws.ncols)]

                        if any(row):

                            rows.append(row)

                elif nome_arquivo.endswith('.csv'):

                    import csv, io

                    content = arquivo.read().decode('utf-8-sig')

                    reader = csv.reader(io.StringIO(content), delimiter=';')

                    for i, row in enumerate(reader):

                        if i == 0:

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

            erros_lista = []

            for index, row in enumerate(rows, start=1):

                try:

                    with transaction.atomic():

                        nome = row[0] if len(row) > 0 else ''

                        apartamento = row[1] if len(row) > 1 else ''

                        bloco = row[2] if len(row) > 2 else ''

                        telefone = row[3] if len(row) > 3 else ''

                        email = row[4] if len(row) > 4 else ''

                        cpf = row[5] if len(row) > 5 else ''

                        nome = nome.strip()

                        apartamento = apartamento.strip()

                        if not nome or not apartamento:

                            raise ValueError(f"Linha {index}: Nome e apartamento são obrigatórios.")

                        base_username = f"{nome.split()[0].lower()}.{apartamento}"

                        if bloco:

                            base_username += f".{bloco.lower()}"

                        username = base_username

                        counter = 1

                        while User.objects.filter(username=username).exists():

                            username = f"{base_username}{counter}"

                            counter += 1

                        if cpf and len(cpf) > 14:

                            raise ValueError(f"Linha {index}: CPF longo demais.")

                        user_obj = User.objects.create_user(

                            username=username,

                            password='mudar123',

                            first_name=nome.split()[0] if nome else '',

                            email=email,

                            tipo_usuario='morador'

                        )

                        user_obj.condominios.add(condominio)

                        Morador.objects.create(

                            condominio=condominio,

                            nome=nome,

                            bloco=bloco,

                            apartamento=apartamento,

                            telefone=telefone,

                            email=email,

                            cpf=cpf,

                            usuario=user_obj

                        )

                        total += 1

                except Exception as e:

                    erros_lista.append(str(e) if "Linha " in str(e) else f"Linha {index} ({nome or 'Desconhecido'}): {str(e)}")

            if total > 0:

                messages.success(request, f"{total} morador(es) importado(s) com sucesso!")

            if erros_lista:

                for erro_msg in erros_lista:

                    messages.warning(request, erro_msg)

            return redirect('sindico_moradores')

        elif action == 'aprovar':

            morador_id = request.POST.get('morador_id')

            if morador_id:

                morador = get_object_or_404(Morador, id=morador_id, condominio=condominio)

                morador.status_aprovacao = 'APROVADO'

                morador.save()

                messages.success(request, f"Morador {morador.nome} foi aprovado com sucesso.")

            return redirect('sindico_moradores')

        elif action == 'recusar':

            morador_id = request.POST.get('morador_id')

            if morador_id:

                morador = get_object_or_404(Morador, id=morador_id, condominio=condominio)

                morador.status_aprovacao = 'RECUSADO'

                morador.save()

                messages.error(request, f"Morador {morador.nome} foi recusado do sistema.")

            return redirect('sindico_moradores')

        else:

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

                        email=email,

                        tipo_usuario='morador'

                    )

                    user_obj.condominios.add(condominio)

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

    query_busca = request.GET.get('q', '').strip()

    moradores = Morador.objects.filter(condominio=condominio)

    if query_busca:

        moradores = moradores.filter(

            Q(nome__icontains=query_busca) |

            Q(apartamento__icontains=query_busca) |

            Q(bloco__icontains=query_busca)

        )

    moradores = moradores.order_by('nome', 'bloco', 'apartamento')

    ctx = sindico_context(request, {

        'moradores': moradores,

        'query_busca': query_busca,

    }, active_page='moradores')

    return render(request, 'sindico/moradores.html', ctx)

@login_required

def sindico_morador_editar(request, id):

    if not is_sindico(request.user) or request.method != 'POST':

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    morador = get_object_or_404(Morador, id=id, condominio=condominio)

    morador.nome = request.POST.get('nome', morador.nome).strip()

    morador.bloco = request.POST.get('bloco', morador.bloco).strip()

    morador.apartamento = request.POST.get('apartamento', morador.apartamento).strip()

    morador.telefone = request.POST.get('telefone', morador.telefone).strip()

    morador.email = request.POST.get('email', morador.email).strip()

    if morador.usuario:

        if morador.nome:

            morador.usuario.first_name = morador.nome.split()[0]

        if morador.email:

            morador.usuario.email = morador.email

        morador.usuario.save()

    morador.save()

    messages.success(request, f"Morador '{morador.nome}' atualizado com sucesso!")

    return redirect('sindico_moradores')

@login_required

def sindico_morador_excluir(request, id):

    if not is_sindico(request.user) or request.method != 'POST':

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    morador = get_object_or_404(Morador, id=id, condominio=condominio)

    nome = morador.nome

    if morador.usuario:

        morador.usuario.delete()

    morador.delete()

    messages.success(request, f"Morador '{nome}' excluído com sucesso!")

    return redirect('sindico_moradores')

@login_required

def resetar_senha_morador(request, morador_id):

    pass

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

            email=morador.email or '',

            tipo_usuario='morador',

            condominio=condominio

        )

        morador.usuario = user_obj

        morador.save()

        messages.success(request, f"Conta criada para '{morador.nome}' com login: {username}")

    return redirect('sindico_moradores')

@login_required

def solicitacoes_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    Notificacao.objects.filter(

        usuario=request.user, tipo='solicitacao', lida=False

    ).update(lida=True)

    solicitacoes = Solicitacao.objects.filter(

        condominio=condominio

    ).select_related('morador', 'criado_por').order_by('-data_criacao')

    ctx = sindico_context(request, {'solicitacoes': solicitacoes}, active_page='solicitacoes')

    return render(request, 'sindico/solicitacoes.html', ctx)

@login_required

def responder_solicitacao_sindico(request, solicitacao_id):

    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id)

    if request.method == 'POST':

        solicitacao.resposta_admin = request.POST.get('resposta', '').strip()

        solicitacao.status = request.POST.get('status', solicitacao.status)

        solicitacao.save()

        if solicitacao.morador and solicitacao.morador.usuario:

            Notificacao.objects.create(

                usuario=solicitacao.morador.usuario,

                tipo='resposta_solicitacao',

                mensagem=f'Sua solicitação #{solicitacao.id} foi respondida',

                link=f'/morador/solicitacoes/{solicitacao.id}/'

            )

            disparar_push_individual(

                solicitacao.morador.usuario,

                titulo="Resposta da Administração",

                mensagem=f"Sua solicitação #{solicitacao.id} foi respondida.",

                link=f'/morador/solicitacoes/{solicitacao.id}/'

            )

        messages.success(request, "Solicitação atualizada!")

    return redirect('sindico_solicitacoes')

@login_required

def avisos_sindico(request):

    pass

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

    pass

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

        for f in [imagem, arquivo]:

            if f:

                content_type = getattr(f, 'content_type', '')

                if content_type.startswith('video/') or str(f.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                    messages.error(request, "O envio de vídeos não é permitido. Envie apenas imagens ou documentos.")

                    return redirect('sindico_avisos')

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

            for m in moradores:

                if m.usuario and getattr(m.usuario, 'receber_push', False):

                    disparar_push_individual(

                        m.usuario,

                        titulo=f'Novo Aviso: {titulo[:30]}',

                        mensagem=conteudo[:100],

                        link='/morador/avisos/'

                    )

            messages.success(request, f"Aviso '{titulo}' publicado!")

    return redirect('sindico_avisos')

@login_required

def editar_aviso_sindico(request, aviso_id):

    pass

    aviso = get_object_or_404(Aviso, id=aviso_id)

    if request.method == 'POST':

        aviso.titulo = request.POST.get('titulo', aviso.titulo).strip()

        aviso.conteudo = request.POST.get('conteudo', aviso.conteudo).strip()

        data_exp = request.POST.get('data_expiracao', '').strip()

        aviso.data_expiracao = data_exp if data_exp else None

        aviso.ativo = request.POST.get('ativo', '1') == '1'

        imagem = request.FILES.get('imagem')

        if imagem:

            content_type = getattr(imagem, 'content_type', '')

            if content_type.startswith('video/') or str(imagem.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                messages.error(request, "O envio de vídeos não é permitido.")

                return redirect('sindico_avisos')

            aviso.imagem = imagem

        arquivo = request.FILES.get('arquivo')

        if arquivo:

            content_type = getattr(arquivo, 'content_type', '')

            if content_type.startswith('video/') or str(arquivo.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                messages.error(request, "O envio de vídeos não é permitido.")

                return redirect('sindico_avisos')

            aviso.arquivo = arquivo

        aviso.save()

        messages.success(request, "Aviso atualizado!")

    return redirect('sindico_avisos')

@login_required

def excluir_aviso_sindico(request, aviso_id):

    pass

    aviso = get_object_or_404(Aviso, id=aviso_id)

    if request.method == 'POST':

        aviso.delete()

        messages.success(request, "Aviso excluído!")

    return redirect('sindico_avisos')

@login_required

def gerenciar_portaria(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    if request.method == 'POST':

        action = request.POST.get('action', 'cadastrar')

        if action == 'cadastrar':

            nome = request.POST.get('nome', '').strip()

            username = request.POST.get('username', '').strip()

            password = request.POST.get('password', '').strip()

            if nome and username and password:

                if User.objects.filter(username=username).exists():

                    messages.error(request, f"O usuário '{username}' já está em uso.")

                else:

                    user_obj = User.objects.create_user(

                        username=username,

                        password=password,

                        first_name=nome.split()[0] if nome else '',

                        tipo_usuario='porteiro'

                    )

                    user_obj.condominios.add(condominio)

                    Porteiro.objects.create(

                        condominio=condominio,

                        nome=nome,

                        usuario=user_obj

                    )

                    messages.success(request, f"Porteiro '{nome}' cadastrado com sucesso!")

            else:

                messages.error(request, "Todos os campos (Nome, Usuário e Senha) são obrigatórios para cadastro.")

        elif action == 'editar':

            porteiro_id = request.POST.get('porteiro_id')

            porteiro = get_object_or_404(Porteiro, id=porteiro_id, condominio=condominio)

            nome = request.POST.get('nome', porteiro.nome).strip()

            password = request.POST.get('password', '').strip()

            porteiro.nome = nome

            porteiro.save()

            if porteiro.usuario:

                porteiro.usuario.first_name = nome.split()[0] if nome else ''

                if password:

                    porteiro.usuario.set_password(password)

                porteiro.usuario.save()

            messages.success(request, f"Dados do porteiro '{nome}' atualizados!")

        elif action == 'excluir':

            porteiro_id = request.POST.get('porteiro_id')

            porteiro = get_object_or_404(Porteiro, id=porteiro_id, condominio=condominio)

            nome = porteiro.nome

            if porteiro.usuario:

                porteiro.usuario.delete()

            porteiro.delete()

            messages.success(request, f"Porteiro '{nome}' excluído com sucesso!")

        return redirect('sindico_portaria')

    porteiros = Porteiro.objects.filter(condominio=condominio)

    ctx = sindico_context(request, {

        'porteiros': porteiros,

    }, active_page='portaria')

    return render(request, 'sindico/portaria.html', ctx)

def dashboard_condominio(request, condominio_id):

    pass

    return redirect('sindico_painel')

@login_required

def areas_comuns_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    try:

        if request.method == 'POST':

            action = request.POST.get('action')

            if action == 'criar':

                nome = request.POST.get('nome', '').strip()

                descricao = request.POST.get('descricao', '')

                capacidade = request.POST.get('capacidade', 0)

                horario_abertura = request.POST.get('horario_abertura') or '08:00'

                horario_fechamento = request.POST.get('horario_fechamento') or '22:00'

                imagem = request.FILES.get('imagem')

                if imagem:

                    content_type = getattr(imagem, 'content_type', '')

                    if content_type.startswith('video/') or str(imagem.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                        messages.error(request, "O envio de vídeos não é permitido.")

                        return redirect('sindico_areas_comuns')

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

                area.capacidade = int(request.POST.get('capacidade') or area.capacidade or 0)

                area.horario_abertura = request.POST.get('horario_abertura') or area.horario_abertura

                area.horario_fechamento = request.POST.get('horario_fechamento') or area.horario_fechamento

                area.ativo = request.POST.get('ativo') == 'on'

                imagem_nova = request.FILES.get('imagem')

                if imagem_nova:

                    content_type = getattr(imagem_nova, 'content_type', '')

                    if content_type.startswith('video/') or str(imagem_nova.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                        messages.error(request, "O envio de vídeos não é permitido.")

                        return redirect('sindico_areas_comuns')

                    area.imagem = imagem_nova

                area.save()

                messages.success(request, f'Área "{area.nome}" atualizada!')

            return redirect('sindico_areas_comuns')

    except Exception as e:

        messages.error(request, f"Erro interno ao salvar: {str(e)}")

        return redirect('sindico_areas_comuns')

    areas = AreaComum.objects.filter(condominio=condominio)

    context = sindico_context(request, {

        'areas': areas,

    }, active_page='reservas')

    return render(request, 'sindico/areas_comuns.html', context)

@login_required

def excluir_area_sindico(request, area_id):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    area = get_object_or_404(AreaComum, id=area_id, condominio=condominio)

    nome_area = area.nome

    area.delete()

    messages.success(request, f'A área "{nome_area}" foi excluída com sucesso.')

    return redirect('sindico_areas_comuns')

@login_required

def reservas_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    Notificacao.objects.filter(

        usuario=request.user, tipo='reserva', lida=False

    ).update(lida=True)

    if request.method == 'POST' and request.POST.get('action') == 'criar_area':

        try:

            nome = request.POST.get('nome', '').strip()

            descricao = request.POST.get('descricao', '')

            capacidade = request.POST.get('capacidade', 0)

            horario_abertura = request.POST.get('horario_abertura') or '08:00'

            horario_fechamento = request.POST.get('horario_fechamento') or '22:00'

            imagem = request.FILES.get('imagem')

            if imagem:

                content_type = getattr(imagem, 'content_type', '')

                if content_type.startswith('video/') or str(imagem.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                    messages.error(request, "O envio de vídeos não é permitido.")

                    return redirect('sindico_reservas')

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

        except Exception as e:

            messages.error(request, f"Erro interno ao cadastrar área: {str(e)}")

        return redirect('sindico_reservas')

    reservas_list = Reserva.objects.filter(

        area__condominio=condominio

    ).select_related('area', 'morador')

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

    pass

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    reserva = get_object_or_404(Reserva, id=reserva_id, area__condominio=condominio)

    reserva.status = 'APROVADA'

    reserva.save()

    reserva.save()

    if reserva.area.taxa_reserva > 0:

        Cobranca.objects.create(

            condominio=condominio,

            morador=reserva.morador,

            descricao=f"Reserva de {reserva.area.nome} ({reserva.data.strftime('%d/%m/%Y')})",

            valor=reserva.area.taxa_reserva,

            data_vencimento=timezone.now().date() + timezone.timedelta(days=5)                   

        )

        msg = f'Reserva aprovada e cobrança de R$ {reserva.area.taxa_reserva} gerada!'

    else:

        msg = 'Reserva aprovada!'

    if reserva.morador.usuario:

        Notificacao.objects.create(

            usuario=reserva.morador.usuario,

            tipo='reserva',

            mensagem=f'Sua reserva de {reserva.area.nome} para {reserva.data.strftime("%d/%m")} foi aprovada! ✅',

            link='/morador/reservas/'

        )

        disparar_push_individual(

            reserva.morador.usuario,

            titulo="Reserva Aprovada!",

            mensagem=f'Sua reserva de {reserva.area.nome} para {reserva.data.strftime("%d/%m")} foi aprovada!',

            link='/morador/reservas/'

        )

    messages.success(request, msg)

    return redirect('sindico_reservas')

@login_required

def recusar_reserva_sindico(request, reserva_id):

    pass

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    reserva = get_object_or_404(Reserva, id=reserva_id, area__condominio=condominio)

    reserva.status = 'RECUSADA'

    reserva.motivo_recusa = request.POST.get('motivo', '')

    reserva.save()

    if reserva.morador.usuario:

        Notificacao.objects.create(

            usuario=reserva.morador.usuario,

            tipo='reserva',

            mensagem=f'Sua reserva de {reserva.area.nome} para {reserva.data.strftime("%d/%m")} foi recusada.',

            link='/morador/reservas/'

        )

        disparar_push_individual(

            reserva.morador.usuario,

            titulo="Reserva Recusada",

            mensagem=f'Sua reserva de {reserva.area.nome} para {reserva.data.strftime("%d/%m")} foi recusada.',

            link='/morador/reservas/'

        )

    messages.success(request, 'Reserva recusada.')

    return redirect('sindico_reservas')

@login_required

def financeiro_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    if request.method == 'POST':

        action = request.POST.get('action')

        if action == 'criar_cobranca':

            morador_id = request.POST.get('morador_id')

            descricao = request.POST.get('descricao', '').strip()

            valor = request.POST.get('valor', '0').replace(',', '.')

            data_vencimento = request.POST.get('data_vencimento')

            arquivo_boleto = request.FILES.get('arquivo_boleto')

            chave_pix = request.POST.get('chave_pix', '').strip()

            if arquivo_boleto:

                content_type = getattr(arquivo_boleto, 'content_type', '')

                if content_type.startswith('video/') or str(arquivo_boleto.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                    messages.error(request, "O envio de vídeos não é permitido.")

                    return redirect('sindico_financeiro')

            if morador_id and descricao and valor and data_vencimento:

                morador = get_object_or_404(Morador, id=morador_id, condominio=condominio)

                cobranca = Cobranca(

                    condominio=condominio,

                    morador=morador,

                    descricao=descricao,

                    valor=valor,

                    data_vencimento=data_vencimento

                )

                if arquivo_boleto:

                    cobranca.arquivo_boleto = arquivo_boleto

                if chave_pix:

                    cobranca.chave_pix = chave_pix

                cobranca.save()

                if morador.usuario:

                    disparar_push_individual(

                        morador.usuario,

                        titulo="Nova Cobrança",

                        mensagem=f"Foi gerada a cobrança '{descricao}' no valor de R$ {valor} com vencimento em {data_vencimento}.",

                        link="/morador/cobrancas/"

                    )

                messages.success(request, f'Cobrança "{descricao}" gerada para {morador.nome}.')

            else:

                messages.error(request, 'Preencha todos os campos obrigatórios da cobrança.')

        elif action == 'marcar_pago' or action == 'aprovar_pagamento':

            cobranca_id = request.POST.get('cobranca_id')

            cobranca = get_object_or_404(Cobranca, id=cobranca_id, condominio=condominio)

            cobranca.status = 'PAGO'

            cobranca.data_pagamento = timezone.now().date()

            cobranca.save()

            if action == 'aprovar_pagamento' and cobranca.morador.usuario:

                Notificacao.objects.create(

                    usuario=cobranca.morador.usuario,

                    tipo='geral',

                    mensagem=f'Seu pagamento da cobrança "{cobranca.descricao}" foi APROVADO! ✅',

                    link='/morador/cobrancas/'

                )

            messages.success(request, f'Cobrança "{cobranca.descricao}" liquidada/marcada como paga.')

        return redirect('sindico_financeiro')

    cobrancas = Cobranca.objects.filter(condominio=condominio).select_related('morador').order_by('-data_vencimento')

    moradores = Morador.objects.filter(condominio=condominio).order_by('bloco', 'apartamento')

    blocos_unicos = Morador.objects.filter(condominio=condominio).exclude(bloco='').values_list('bloco', flat=True).distinct().order_by('bloco')

    hoje = timezone.now().date()

    Cobranca.objects.filter(

        condominio=condominio, 

        status='PENDENTE', 

        data_vencimento__lt=hoje

    ).update(status='ATRASADO')

    context = sindico_context(request, {

        'cobrancas': cobrancas,

        'moradores': moradores,

        'blocos_unicos': blocos_unicos,

    }, active_page='financeiro')

    return render(request, 'sindico/financeiro.html', context)

@login_required

def mensagens_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    usuario = request.user

    if request.method == 'POST':

        destinatario_id = request.POST.get('destinatario_id')

        conteudo = request.POST.get('conteudo', '').strip()

        msg_condominio_id = request.POST.get('condominio_id')

        if msg_condominio_id:

            msg_condominio = request.user.condominios.filter(id=msg_condominio_id).first()

        else:

            msg_condominio = condominio

        if destinatario_id and conteudo and msg_condominio:

            destinatario = get_object_or_404(User, id=destinatario_id)

            Mensagem.objects.create(

                condominio=msg_condominio,

                remetente=usuario,

                destinatario=destinatario,

                conteudo=conteudo

            )

            messages.success(request, 'Mensagem enviada com sucesso!')

            return redirect('sindico_mensagens')

        else:

            messages.error(request, 'Destinatário, conteúdo e condomínio são obrigatórios.')

    Mensagem.objects.filter(destinatario=usuario, lida=False).update(lida=True)

    mensagens_list = Mensagem.objects.filter(

        Q(remetente=usuario) | Q(destinatario=usuario)

    ).select_related('remetente', 'destinatario').order_by('-data_envio')

    destinatarios_possiveis = User.objects.filter(condominios__in=usuario.condominios.all()).exclude(id=usuario.id).distinct()

    conversas = {}

    for msg in mensagens_list:

        outro_usuario = msg.destinatario if msg.remetente == usuario else msg.remetente

        if outro_usuario not in conversas:

            conversas[outro_usuario] = []

        conversas[outro_usuario].append(msg)

    for k in conversas:

        conversas[k] = list(reversed(conversas[k]))

    context = sindico_context(request, {

        'conversas': conversas,

        'destinatarios': destinatarios_possiveis,

    }, active_page='mensagens')

    return render(request, 'sindico/mensagens.html', context)

@login_required

def ocorrencias_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    status = request.GET.get('status', 'TODOS')

    q = request.GET.get('q', '').strip()

    ocorrencias_list = Ocorrencia.objects.filter(condominio=condominio)

    if q:

        ocorrencias_list = ocorrencias_list.filter(

            Q(autor__nome__icontains=q) |

            Q(infrator__icontains=q) |

            Q(descricao__icontains=q)

        )

    if status != 'TODOS':

        ocorrencias_list = ocorrencias_list.filter(status=status)

    ocorrencias_list = ocorrencias_list.order_by('-data_registro')

    context = sindico_context(request, {

        'ocorrencias': ocorrencias_list,

        'status_filtro': status,

    }, active_page='ocorrencias')

    return render(request, 'sindico/ocorrencias.html', context)

@login_required

def alterar_status_ocorrencia(request, ocorrencia_id):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    if request.method == 'POST':

        novo_status = request.POST.get('status')

        resposta_sindico = request.POST.get('resposta_sindico', '').strip()

        ocorrencia = get_object_or_404(Ocorrencia, id=ocorrencia_id, condominio=get_condominio_ativo(request))

        if novo_status in dict(Ocorrencia.STATUS_CHOICES).keys():

            if resposta_sindico:

                ocorrencia.resposta_sindico = resposta_sindico

            ocorrencia.status = novo_status

            ocorrencia.save()

            if resposta_sindico and ocorrencia.autor.usuario:

                Notificacao.objects.create(

                    usuario=ocorrencia.autor.usuario,

                    tipo='geral',

                    mensagem=f'O síndico respondeu a sua ocorrência registrada em {ocorrencia.data_registro.strftime("%d/%m")}.',

                    link='/morador/ocorrencias/'

                )

            elif novo_status == 'RESOLVIDA' and ocorrencia.autor.usuario:

                Notificacao.objects.create(

                    usuario=ocorrencia.autor.usuario,

                    tipo='geral',

                    mensagem=f'Sua ocorrência registrada em {ocorrencia.data_registro.strftime("%d/%m")} foi marcada como RESOLVIDA.',

                    link='/morador/ocorrencias/'

                )

            messages.success(request, f'Status e resposta da ocorrência foram atualizados.')

    return redirect('sindico_ocorrencias')

from .forms import SindicoPerfilForm

@login_required

def editar_perfil_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    try:

        sindico = request.user.sindico

    except AttributeError:

        messages.error(request, 'Perfil de síndico não encontrado.')

        return redirect('home')

    if request.method == 'POST':

        form = SindicoPerfilForm(request.POST, instance=sindico, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Perfil atualizado com sucesso!')

            return redirect('editar_perfil_sindico')

    else:

        form = SindicoPerfilForm(instance=sindico, user=request.user)

    context = sindico_context(request, {

        'form': form,

    }, active_page='perfil')

    return render(request, 'sindico/editar_perfil.html', context)

@login_required

def sindico_notificacoes(request):

    pass

    if not is_sindico(request.user):

        messages.error(request, 'Acesso negado: Perfil de Síndico requerido.')

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    notificacoes = Notificacao.objects.filter(

        usuario=request.user

    ).order_by('-id')

    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)

    context = sindico_context(request, {

        'notificacoes_lista': notificacoes

    }, active_page='notificacoes')

    return render(request, 'sindico/notificacoes_lista.html', context)

@login_required

def redirecionar_notificacao(request, notificacao_id):

    pass

    notificacao = get_object_or_404(Notificacao, id=notificacao_id, usuario=request.user)

    notificacao.lida = True

    notificacao.save()

    if notificacao.condominio and notificacao.condominio.id != request.session.get('condominio_ativo_id'):

        request.session['condominio_ativo_id'] = notificacao.condominio.id

        messages.success(request, f"Você agora está visualizando o Condomínio {notificacao.condominio.nome}")

    url_destino = notificacao.link if (notificacao.link and notificacao.link != '#') else reverse('sindico_notificacoes')

    return redirect(url_destino)

@login_required

def gerar_advertencia_pdf(request, ocorrencia_id):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    ocorrencia = get_object_or_404(Ocorrencia, id=ocorrencia_id, condominio=condominio)

    sindico_obj = getattr(request.user, 'sindico', None)

    sindico_nome = sindico_obj.nome if sindico_obj else request.user.get_full_name() or request.user.username

    context = {

        'condominio': condominio,

        'ocorrencia': ocorrencia,

        'sindico_nome': sindico_nome,

    }

    from django.http import HttpResponse

    from django.template.loader import get_template

    try:

        from xhtml2pdf import pisa

    except ImportError:

        return HttpResponse("Erro: Biblioteca xhtml2pdf não instalada. Rode: pip install xhtml2pdf")

    template = get_template('sindico/pdf_advertencia.html')

    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')

    filename = f"advertencia_ocorrencia_{ocorrencia.id}.pdf"

    response['Content-Disposition'] = f'inline; filename="{filename}"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:

        return HttpResponse(f'Erro ao gerar PDF: {pisa_status.err}')

    if not ocorrencia.advertencia_emitida:

        ocorrencia.advertencia_emitida = True

        ocorrencia.save(update_fields=['advertencia_emitida'])

        if ocorrencia.autor and ocorrencia.autor.usuario:

            Notificacao.objects.create(

                usuario=ocorrencia.autor.usuario,

                tipo='geral',

                mensagem=f'Uma advertência formal foi emitida referente à ocorrência #{ocorrencia.id}.',

                link='/morador/ocorrencias/'

            )

    return response

@login_required

def documentos_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    from .models import DocumentoCondominio

    if request.method == 'POST':

        titulo = request.POST.get('titulo', '').strip()

        categoria = request.POST.get('categoria', 'OUTROS')

        arquivo = request.FILES.get('arquivo')

        if titulo and arquivo:

            DocumentoCondominio.objects.create(

                condominio=condominio,

                titulo=titulo,

                categoria=categoria,

                arquivo=arquivo,

            )

            messages.success(request, f'Documento "{titulo}" enviado com sucesso!')

        else:

            messages.error(request, 'Preencha o título e selecione um arquivo.')

        return redirect('sindico_documentos')

    excluir_id = request.GET.get('excluir')

    if excluir_id:

        doc = DocumentoCondominio.objects.filter(id=excluir_id, condominio=condominio).first()

        if doc:

            doc.arquivo.delete(save=False)

            doc.delete()

            messages.success(request, 'Documento excluído.')

        return redirect('sindico_documentos')

    documentos = DocumentoCondominio.objects.filter(

        condominio=condominio

    ).order_by('-data_upload')

    categoria_filtro = request.GET.get('categoria', '')

    if categoria_filtro:

        documentos = documentos.filter(categoria=categoria_filtro)

    ctx = sindico_context(request, {

        'documentos': documentos,

        'categoria_filtro': categoria_filtro,

        'categorias': DocumentoCondominio.CATEGORIA_CHOICES,

    }, active_page='documentos')

    return render(request, 'sindico/central_documentos.html', ctx)

@login_required

def buscar_moradores_ajax(request):

    pass

    if not is_sindico(request.user):

        return JsonResponse({'error': 'Acesso negado'}, status=403)

    condominio = get_condominio_ativo(request)

    if not condominio:

        return JsonResponse({'error': 'Condomínio não encontrado'}, status=400)

    bloco = request.GET.get('bloco', '').strip()

    apartamento = request.GET.get('apartamento', '').strip()

    if bloco and not apartamento:

        aptos = list(Morador.objects.filter(condominio=condominio, bloco=bloco)

                     .exclude(apartamento='')

                     .values_list('apartamento', flat=True).distinct().order_by('apartamento'))

        return JsonResponse({'apartamentos': aptos})

    elif bloco and apartamento:

        moradores_qs = Morador.objects.filter(condominio=condominio, bloco=bloco, apartamento=apartamento).order_by('nome')

        moradores_lista = [{'id': m.id, 'nome': m.nome} for m in moradores_qs]

        return JsonResponse({'moradores': moradores_lista})

    return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)

@login_required

def central_tarefas_sindico(request):

    pass

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    from .models import TarefaSindico

    if request.method == 'POST':

        action = request.POST.get('action')

        if action == 'adicionar_tarefa':

            descricao = request.POST.get('descricao', '').strip()

            if descricao:

                TarefaSindico.objects.create(condominio=condominio, descricao=descricao)

                messages.success(request, 'Tarefa adicionada com sucesso!')

            else:

                messages.error(request, 'A descrição da tarefa não pode estar vazia.')

        elif action == 'alternar_status':

            tarefa_id = request.POST.get('tarefa_id')

            if tarefa_id:

                tarefa = TarefaSindico.objects.filter(id=tarefa_id, condominio=condominio).first()

                if tarefa:

                    tarefa.concluida = not tarefa.concluida

                    tarefa.save()

                    status_lbl = "concluída" if tarefa.concluida else "pendente"

                    messages.success(request, f'Tarefa marcada como {status_lbl}!')

                else:

                    messages.error(request, 'Tarefa não encontrada.')

        elif action == 'excluir_tarefa':

            tarefa_id = request.POST.get('tarefa_id')

            if tarefa_id:

                tarefa = TarefaSindico.objects.filter(id=tarefa_id, condominio=condominio).first()

                if tarefa:

                    tarefa.delete()

                    messages.success(request, 'Tarefa excluída com sucesso!')

                else:

                    messages.error(request, 'Tarefa não encontrada.')

        return redirect('sindico_tarefas')

    tarefas_manuais = TarefaSindico.objects.filter(condominio=condominio)

    solicitacoes_pendentes = Solicitacao.objects.filter(condominio=condominio, status='PENDENTE').select_related('morador').order_by('-data_criacao')

    context = sindico_context(request, {

        'tarefas': tarefas_manuais,

        'solicitacoes': solicitacoes_pendentes,

    }, active_page='tarefas')

    return render(request, 'sindico/tarefas.html', context)

@login_required

def feedbacks_sindico(request):

    if not is_sindico(request.user):

        return redirect('home')

    condominio = get_condominio_ativo(request)

    if not condominio:

        return redirect('sindico_home')

    feedbacks = FeedbackMorador.objects.filter(condominio=condominio).order_by('-data_envio')

    feedbacks.filter(lido_pela_gestao=False).update(lido_pela_gestao=True)

    context = sindico_context(request, {

        'feedbacks': feedbacks,

    }, active_page='feedbacks')

    return render(request, 'sindico/feedbacks.html', context)

