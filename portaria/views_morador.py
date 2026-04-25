from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required

from django.contrib.auth import get_user_model

from django.contrib import messages

from django.core.paginator import Paginator

from django.utils import timezone

from django.conf import settings

from .models import (

    Condominio, Morador, Encomenda, Solicitacao, Aviso, Notificacao, Sindico, AreaComum, Reserva, Mensagem, Ocorrencia, PushSubscription, Cobranca

)

from django.db.models import Q

import json

from django.http import JsonResponse





def get_morador_from_user(user):

    pass

    try:

        return user.morador

    except (Morador.DoesNotExist, AttributeError):

        return None





def morador_required(view_func):

    pass

    def wrapper(request, *args, **kwargs):

        morador = get_morador_from_user(request.user)

        if not morador:

            messages.error(request, "Você não tem acesso ao portal do morador.")

            from django.contrib.auth import logout

            logout(request)

            return redirect('login')

        if getattr(morador, 'status_aprovacao', 'APROVADO') == 'AGUARDANDO':

            return render(request, 'morador/aguardando_aprovacao.html', {'morador': morador})



        request.morador = morador

        return view_func(request, *args, **kwargs)

    return login_required(wrapper)





def get_morador_ativo(request):

    pass

    if request.user.is_authenticated:

        try:

            return request.user.morador

        except Morador.DoesNotExist:

            pass

    return None



def get_condominio_ativo(request):

    pass

    condominio_id = request.session.get('condominio_ativo_id')

    if condominio_id and request.user.is_authenticated:

        c = request.user.condominios.filter(id=condominio_id).first()

        if c: return c



    morador = get_morador_ativo(request)

    if morador:

        return morador.condominio

    return None



def notificar_sindicos_do_condominio(condominio, tipo, titulo, mensagem, link):

    pass

    if not condominio:

        return

    User_model = get_user_model()

    sindicos = User_model.objects.filter(condominios=condominio, tipo_usuario='sindico')



    mensagem_final = f"[{titulo}] {mensagem}" if titulo else mensagem



    notificacoes = [

        Notificacao(

            usuario=sindico,

            condominio=condominio,

            tipo=tipo,

            mensagem=mensagem_final[:199],                                       

            link=link

        ) for sindico in sindicos

    ]

    if notificacoes:

        Notificacao.objects.bulk_create(notificacoes)



def morador_context(request, extra_context=None, active_page=None):

    pass

    morador = get_morador_ativo(request)

    condominio = get_condominio_ativo(request)



    context = {

        'morador': morador,

        'condominio': condominio,

        'active_page': active_page,

    }



    if request.user.is_authenticated:

        context['notificacoes_nao_lidas'] = Notificacao.objects.filter(

            usuario=request.user, lida=False

        ).count()

        context['mensagens_nao_lidas'] = Mensagem.objects.filter(

            destinatario=request.user, lida=False

        ).count()

        context['VAPID_PUBLIC_KEY'] = getattr(settings, 'VAPID_PUBLIC_KEY', '')



    if extra_context:

        context.update(extra_context)

    return context





@morador_required

def portal_home(request):

    pass

    if request.user.is_superuser:

        return redirect('admin:index')

    morador = request.morador





    encomendas_pendentes = Encomenda.objects.filter(

        morador=morador,

        entregue=False

    ).count()





    solicitacoes_pendentes = Solicitacao.objects.filter(

        morador=morador,

        status='PENDENTE'

    ).count()





    avisos_nao_lidos = Notificacao.objects.filter(

        usuario=request.user,

        tipo='aviso',

        lida=False

    ).count()





    solicitacoes_recentes = Solicitacao.objects.filter(

        morador=morador

    ).order_by('-data_criacao')[:5]





    avisos = Aviso.objects.filter(ativo=True)[:3]





    cobrancas_pendentes = Cobranca.objects.filter(

        morador=morador,

        condominio=morador.condominio,

        status__in=['PENDENTE', 'ATRASADO']

    ).count()



    context = {

        'morador': morador,

        'encomendas_pendentes': encomendas_pendentes,

        'solicitacoes_pendentes': solicitacoes_pendentes,

        'avisos_nao_lidos': avisos_nao_lidos,

        'solicitacoes_recentes': solicitacoes_recentes,

        'avisos': avisos,

        'cobrancas_pendentes': cobrancas_pendentes,

    }





    visitante_id = request.GET.get('visitante_id')

    if visitante_id:

        from .models import Visitante

        try:

            visitante = Visitante.objects.get(

                id=visitante_id,

                morador_responsavel=morador

            )

            context['visitante_detalhes'] = visitante

            context['abrir_modal_visitante'] = True

        except Visitante.DoesNotExist:

            pass



    return render(request, 'morador/portal_home.html', context)



@morador_required

def minhas_cobrancas(request):

    pass

    morador = request.morador



    if request.method == 'POST':

        action = request.POST.get('action')

        if action == 'avisar_pagamento':

            cobranca_id = request.POST.get('cobranca_id')

            cobranca = get_object_or_404(Cobranca, id=cobranca_id, morador=morador)



            comprovante = request.FILES.get('comprovante')

            if comprovante:

                content_type = getattr(comprovante, 'content_type', '')

                if content_type.startswith('video/') or str(comprovante.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                    messages.error(request, "O envio de vídeos não é permitido para o comprovante.")

                    return redirect('morador_cobrancas')

                if comprovante.size > 5 * 1024 * 1024:

                    messages.error(request, 'O comprovante deve ter no máximo 5MB.')

                    return redirect('morador_cobrancas')

                cobranca.comprovante = comprovante



            cobranca.status = 'EM_ANALISE'

            cobranca.save()





            notificar_sindicos_do_condominio(

                condominio=morador.condominio,

                tipo='geral',

                titulo='Aviso de Pagamento',

                mensagem=f'O morador {morador.nome} ({morador.bloco}-{morador.apartamento}) informou o pagamento de uma cobrança.',

                link='/sindico/financeiro/'

            )

            messages.success(request, 'Aviso de pagamento enviado com sucesso. O síndico analisará o comprovante.')

            return redirect('morador_cobrancas')



    status_filter = request.GET.get('status')

    data_inicio = request.GET.get('data_inicio')

    data_fim = request.GET.get('data_fim')



    queryset = Cobranca.objects.filter(

        morador=morador,

        condominio=morador.condominio

    )



    if status_filter:

        queryset = queryset.filter(status=status_filter)

    if data_inicio:

        queryset = queryset.filter(data_vencimento__gte=data_inicio)

    if data_fim:

        queryset = queryset.filter(data_vencimento__lte=data_fim)



    cobrancas_list = queryset.order_by('-data_criacao')



    paginator = Paginator(cobrancas_list, 10)

    page_number = request.GET.get('page')

    cobrancas = paginator.get_page(page_number)



    context = morador_context(request, {

        'cobrancas': cobrancas,

    }, active_page='cobrancas')



    return render(request, 'morador/cobrancas.html', context)





@morador_required

def minhas_encomendas(request):

    pass

    morador = request.morador





    status = request.GET.get('status', 'pendentes')



    if status == 'entregues':

        encomendas_list = Encomenda.objects.filter(

            morador=morador,

            entregue=True

        ).order_by('-data_entrega')

    else:

        encomendas_list = Encomenda.objects.filter(

            morador=morador,

            entregue=False

        ).order_by('-data_chegada')



    paginator = Paginator(encomendas_list, 10)

    page_number = request.GET.get('page')

    encomendas = paginator.get_page(page_number)



    context = {

        'morador': morador,

        'encomendas': encomendas,

        'status_filtro': status,

    }

    return render(request, 'morador/encomendas.html', context)





@morador_required

def minhas_solicitacoes(request):

    pass

    morador = request.morador





    Notificacao.objects.filter(

        usuario=request.user, tipo='resposta_solicitacao', lida=False

    ).update(lida=True)



    solicitacoes_list = Solicitacao.objects.filter(

        morador=morador

    ).order_by('-data_criacao')





    tipo = request.GET.get('tipo')

    status = request.GET.get('status')



    if tipo:

        solicitacoes_list = solicitacoes_list.filter(tipo=tipo)

    if status:

        solicitacoes_list = solicitacoes_list.filter(status=status)



    paginator = Paginator(solicitacoes_list, 10)

    page_number = request.GET.get('page')

    solicitacoes = paginator.get_page(page_number)



    context = {

        'morador': morador,

        'solicitacoes': solicitacoes,

        'tipo_filtro': tipo,

        'status_filtro': status,

    }

    return render(request, 'morador/solicitacoes.html', context)





@morador_required

def nova_solicitacao(request):

    pass

    morador = request.morador



    if request.method == 'POST':

        tipo = request.POST.get('tipo')

        descricao = request.POST.get('descricao')

        arquivo = request.FILES.get('arquivo')



        if arquivo:

            content_type = getattr(arquivo, 'content_type', '')

            if content_type.startswith('video/') or str(arquivo.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                messages.error(request, "O envio de vídeos não é permitido.")

                return redirect('morador_nova_solicitacao')

            if arquivo.size > 5 * 1024 * 1024:

                messages.error(request, 'O arquivo deve ter no máximo 5MB.')

                return redirect('morador_nova_solicitacao')



        if tipo and descricao:

            sol_kwargs = dict(

                tipo=tipo,

                descricao=descricao,

                morador=morador,

                criado_por=request.user,

                condominio=morador.condominio,

            )

            if arquivo:

                sol_kwargs['arquivo'] = arquivo

            solicitacao = Solicitacao.objects.create(**sol_kwargs)





            notificar_sindicos_do_condominio(

                condominio=morador.condominio,

                tipo='solicitacao',

                titulo='Nova Solicitação de Manutenção',

                mensagem=f'O morador {request.user.first_name} abriu um chamado para a unidade {morador.bloco}/{morador.apartamento}.',

                link='/sindico/solicitacoes/'

            )



            messages.success(request, f"Solicitação #{solicitacao.id} criada com sucesso!")

            return redirect('morador_solicitacoes')

        else:

            messages.error(request, "Preencha todos os campos obrigatórios.")



    context = {

        'morador': morador,

        'tipos': Solicitacao.TIPOS_CHOICES,

    }

    return render(request, 'morador/nova_solicitacao.html', context)





@morador_required

def ver_solicitacao(request, id):

    pass

    morador = request.morador

    solicitacao = get_object_or_404(Solicitacao, id=id, morador=morador)



    context = {

        'morador': morador,

        'solicitacao': solicitacao,

    }

    return render(request, 'morador/ver_solicitacao.html', context)





@morador_required

def avisos(request):

    pass

    morador = request.morador





    avisos_list = Aviso.objects.filter(

        ativo=True, condominio=morador.condominio

    ).order_by('-data_publicacao')



    paginator = Paginator(avisos_list, 10)

    page_number = request.GET.get('page')

    avisos = paginator.get_page(page_number)



    context = {

        'morador': morador,

        'avisos': avisos,

    }



    response = render(request, 'morador/avisos.html', context)







    Notificacao.objects.filter(

        usuario=request.user, tipo='aviso', lida=False

    ).update(lida=True)



    return response













@morador_required

def areas_disponiveis(request):

    pass

    morador = request.morador



    areas = AreaComum.objects.filter(

        condominio=morador.condominio, ativo=True

    )



    context = {

        'morador': morador,

        'areas': areas,

    }

    return render(request, 'morador/areas_disponiveis.html', context)





@morador_required

def fazer_reserva(request, area_id):

    pass

    morador = request.morador

    area = get_object_or_404(AreaComum, id=area_id, condominio=morador.condominio, ativo=True)



    if request.method == 'POST':

        data = request.POST.get('data')

        observacoes = request.POST.get('observacoes', '')



        if data:



            conflito = Reserva.objects.filter(

                area=area,

                data=data,

                status__in=['PENDENTE', 'APROVADA'],

            ).exists()



            if conflito:

                messages.error(request, 'Esta data já está reservada. Escolha outra data disponível.')

            else:

                reserva = Reserva.objects.create(

                    area=area,

                    morador=morador,

                    data=data,

                    horario_inicio=area.horario_abertura,

                    horario_fim=area.horario_fechamento,

                    observacoes=observacoes,

                )





                notificar_sindicos_do_condominio(

                    condominio=morador.condominio,

                    tipo='reserva',

                    titulo='Nova Reserva',

                    mensagem=f'O morador {morador.nome[:20]} solicitou a reserva de {area.nome}.',

                    link='/sindico/reservas/'

                )



                messages.success(request, f'Reserva de {area.nome} para {data} solicitada com sucesso!')

                return redirect('morador_reservas')

        else:

            messages.error(request, 'Selecione uma data.')





    datas_bloqueadas = list(

        Reserva.objects.filter(

            area=area,

            data__gte=timezone.now().date(),

            status__in=['PENDENTE', 'APROVADA'],

        ).values_list('data', flat=True).distinct()

    )



    datas_bloqueadas_str = [d.strftime('%Y-%m-%d') for d in datas_bloqueadas]





    reservas_existentes = Reserva.objects.filter(

        area=area,

        data__gte=timezone.now().date(),

        status__in=['PENDENTE', 'APROVADA'],

    ).select_related('morador').order_by('data')[:20]



    context = {

        'morador': morador,

        'area': area,

        'reservas_existentes': reservas_existentes,

        'datas_bloqueadas_json': datas_bloqueadas_str,

    }

    return render(request, 'morador/fazer_reserva.html', context)





@morador_required

def minhas_reservas(request):

    pass

    morador = request.morador





    Notificacao.objects.filter(

        usuario=request.user, tipo='reserva', lida=False

    ).update(lida=True)



    reservas_list = Reserva.objects.filter(

        morador=morador

    ).select_related('area').order_by('-data')





    status_filtro = request.GET.get('status')

    if status_filtro:

        reservas_list = reservas_list.filter(status=status_filtro)





    area_filtro = request.GET.get('area')

    if area_filtro:

        reservas_list = reservas_list.filter(area_id=area_filtro)





    areas = AreaComum.objects.filter(

        condominio=morador.condominio, ativo=True

    ).order_by('nome') if morador.condominio else AreaComum.objects.none()



    paginator = Paginator(reservas_list, 10)

    page_number = request.GET.get('page')

    reservas = paginator.get_page(page_number)



    context = {

        'morador': morador,

        'reservas': reservas,

        'status_filtro': status_filtro,

        'area_filtro': area_filtro,

        'areas': areas,

    }

    return render(request, 'morador/reservas.html', context)





@morador_required

def cancelar_reserva(request, reserva_id):

    pass

    morador = request.morador

    reserva = get_object_or_404(Reserva, id=reserva_id, morador=morador)



    if reserva.status == 'PENDENTE':

        reserva.status = 'CANCELADA'

        reserva.save()

        messages.success(request, 'Reserva cancelada.')

    else:

        messages.error(request, 'Só é possível cancelar reservas pendentes.')



    return redirect('morador_reservas')











@morador_required

def mensagens(request):

    pass

    morador = request.morador

    usuario = request.user

    condominio = morador.condominio



    if request.method == 'POST':

        destinatario_id = request.POST.get('destinatario_id')

        conteudo = request.POST.get('conteudo', '').strip()



        if destinatario_id and conteudo:

            from django.contrib.auth import get_user_model

            User = get_user_model()

            destinatario = get_object_or_404(User, id=destinatario_id)



            Mensagem.objects.create(

                condominio=condominio,

                remetente=usuario,

                destinatario=destinatario,

                conteudo=conteudo

            )



            notificar_sindicos_do_condominio(

                condominio=condominio,

                tipo='aviso',

                titulo='Nova Mensagem Recebida',

                mensagem=f"Enviada pelo morador {request.user.first_name or request.user.username}.",

                link="/sindico/mensagens/"

            )



            messages.success(request, 'Mensagem enviada com sucesso!')

            return redirect('morador_mensagens')

        else:

            messages.error(request, 'Destinatário e conteúdo são obrigatórios.')





    Mensagem.objects.filter(destinatario=usuario, lida=False).update(lida=True)



    mensagens_list = Mensagem.objects.filter(

        Q(remetente=usuario) | Q(destinatario=usuario)

    ).select_related('remetente', 'destinatario').order_by('-data_envio')



    from django.contrib.auth import get_user_model

    User = get_user_model()

    destinatarios_possiveis = User.objects.filter(

        condominios=condominio,

        tipo_usuario__in=['sindico', 'porteiro']

    ).exclude(id=usuario.id)





    conversas = {}

    for msg in mensagens_list:

        outro_usuario = msg.destinatario if msg.remetente == usuario else msg.remetente

        if outro_usuario not in conversas:

            conversas[outro_usuario] = []

        conversas[outro_usuario].append(msg)





    for k in conversas:

        conversas[k] = list(reversed(conversas[k]))



    context = morador_context(request, {

        'conversas': conversas,

        'destinatarios': destinatarios_possiveis,

    }, active_page='mensagens')



    return render(request, 'morador/mensagens.html', context)











@login_required

def ocorrencias(request):

    pass

    morador = get_morador_ativo(request)

    if not morador:

        return redirect('home')



    condominio = get_condominio_ativo(request)



    if request.method == 'POST':

        infrator = request.POST.get('infrator', '').strip()

        descricao = request.POST.get('descricao', '').strip()

        foto = request.FILES.get('foto')



        if foto:

            content_type = getattr(foto, 'content_type', '')

            if content_type.startswith('video/') or str(foto.name).lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):

                messages.error(request, "O envio de vídeos não é permitido.")

                return redirect('morador_ocorrencias')

            if foto.size > 5 * 1024 * 1024:

                messages.error(request, 'A foto deve ter no máximo 5MB.')

                return redirect('morador_ocorrencias')



        if descricao:

            ocorrencia = Ocorrencia.objects.create(

                condominio=condominio,

                autor=morador,

                infrator=infrator,

                descricao=descricao,

                foto=foto

            )





            notificar_sindicos_do_condominio(

                condominio=condominio,

                tipo='ocorrencia',

                titulo='Nova Ocorrência',

                mensagem=f'O morador {request.user.first_name} abriu um chamado para a unidade {morador.bloco}/{morador.apartamento}.',

                link='/sindico/ocorrencias/'

            )



            messages.success(request, 'Ocorrência registrada com sucesso.')

            return redirect('morador_ocorrencias')

        else:

            messages.error(request, 'A descrição da ocorrência é obrigatória.')



    ocorrencias_list = Ocorrencia.objects.filter(condominio=condominio, autor=morador).order_by('-data_registro')



    context = morador_context(request, {

        'ocorrencias': ocorrencias_list,

    }, active_page='ocorrencias')



    return render(request, 'morador/ocorrencias.html', context)









from .forms import MoradorPerfilForm



@morador_required

def editar_perfil_morador(request):

    pass

    morador = request.morador

    if request.method == 'POST':

        form = MoradorPerfilForm(request.POST, instance=morador, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Perfil atualizado com sucesso!')

            return redirect('editar_perfil_morador')

    else:

        form = MoradorPerfilForm(instance=morador, user=request.user)



    context = morador_context(request, {

        'form': form,

    }, active_page='perfil')

    return render(request, 'morador/editar_perfil.html', context)













@morador_required

def documentos_morador(request):

    pass

    morador = request.morador

    from .models import DocumentoCondominio



    documentos = DocumentoCondominio.objects.filter(

        condominio=morador.condominio

    ).order_by('-data_upload')



    categoria = request.GET.get('categoria', '')

    if categoria:

        documentos = documentos.filter(categoria=categoria)



    context = {

        'morador': morador,

        'documentos': documentos,

        'categoria_filtro': categoria,

        'categorias': DocumentoCondominio.CATEGORIA_CHOICES,

    }

    return render(request, 'morador/central_documentos.html', context)











@login_required

def completar_cadastro(request):

    pass

    if getattr(request.user, 'tipo_usuario', '') != 'morador':

        return redirect('home')





    if hasattr(request.user, 'morador') and request.user.morador:

        return redirect('morador_home')



    condominios_ativos = Condominio.objects.filter(ativo=True).order_by('nome')

    convite_condominio_id = request.session.get('condominio_convite_id')



    if request.method == 'POST':

        condominio_id = request.POST.get('condominio')

        bloco = request.POST.get('bloco', '').strip()

        apartamento = request.POST.get('apartamento', '').strip()

        telefone = request.POST.get('telefone', '').strip()



        if condominio_id and apartamento:

            condominio = get_object_or_404(Condominio, id=condominio_id, ativo=True)











            morador = Morador.objects.create(

                condominio=condominio,

                usuario=request.user,

                nome=request.user.get_full_name() or request.user.username,

                cpf='',                                                                        

                telefone=telefone,

                email=request.user.email,

                bloco=bloco,

                apartamento=apartamento,

                status_aprovacao='AGUARDANDO'

            )





            request.user.condominios.add(condominio)



            notificar_sindicos_do_condominio(

                condominio=condominio,

                tipo='geral',

                titulo='Novo cadastro de Morador via Social',

                mensagem=f"{request.user.get_full_name() or request.user.username} ({bloco}-{apartamento}) aguarda sua aprovação.",

                link='/sindico/moradores/'

            )



            messages.success(request, 'Seu perfil foi completado! Você poderá acessar o portal assim que o síndico aprovar.')

            return redirect('morador_home')

        else:

            messages.error(request, 'Condomínio e Apartamento são campos obrigatórios.')



    return render(request, 'morador/completar_cadastro.html', {

        'condominios': condominios_ativos,

        'user_name': request.user.get_full_name() or request.user.username,

        'convite_condominio_id': convite_condominio_id,

    })









from django.views.decorators.csrf import csrf_exempt



@csrf_exempt

@login_required

def atualizar_preferencia_push(request):

    pass

    if request.user.is_authenticated and request.method == 'POST':

        try:

            data = json.loads(request.body)



            valor = data.get('valor', False)



            request.user.receber_push = valor

            request.user.save(update_fields=['receber_push'])

            return JsonResponse({'status': 'ok', 'receber_push': valor})

        except json.JSONDecodeError:

            return JsonResponse({'error': 'JSON Invalido'}, status=400)

    return JsonResponse({'error': 'Acesso negado'}, status=403)

