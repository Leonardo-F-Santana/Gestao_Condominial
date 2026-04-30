from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required, user_passes_test

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.forms import AuthenticationForm

from django.contrib import messages

from django.utils import timezone

from django.utils.timezone import localdate

import datetime

from django.db.models import Q, Count

from django.core.paginator import Paginator

from django.http import HttpResponse

from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from django.views.decorators.cache import never_cache

from django_ratelimit.decorators import ratelimit

from .models import Visitante, Morador, Encomenda, Solicitacao, Notificacao, Sindico, Porteiro, Condominio, Mensagem, PushSubscription, Reserva

from .utils import enviar_push_notification, disparar_push_individual





try:

    from django.template.loader import get_template

    from xhtml2pdf import pisa

except ImportError:

    pisa = None









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











def is_porteiro(user):

    pass

    if user.is_superuser:

        return True

    return getattr(user, 'tipo_usuario', '') == 'porteiro' or user.is_staff or user.groups.filter(name='Portaria').exists()





def get_condominio_porteiro(user):

    pass

    return getattr(user, 'condominio', None)





@never_cache

def popup_close(request):

    pass

    return render(request, 'popup_close.html')



@never_cache

@ratelimit(key='ip', rate='5/m', method='POST', block=True)

def login_view(request):

    if request.user.is_authenticated:

        if request.user.is_superuser or request.user.is_staff:

            return redirect('/admin/')





        if getattr(request.user, 'tipo_usuario', '') == 'morador':

            if not hasattr(request.user, 'morador') or not request.user.morador:

                return redirect('completar_cadastro')

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





            if getattr(user, 'tipo_usuario', '') == 'morador':

                if not hasattr(user, 'morador') or not user.morador:

                    return redirect('completar_cadastro')

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





import smtplib

import logging

from django.contrib.auth.views import PasswordResetView



logger = logging.getLogger(__name__)



class CustomPasswordResetView(PasswordResetView):

    def form_valid(self, form):

        try:

            return super().form_valid(form)

        except smtplib.SMTPException as e:

            logger.error(f"Erro crítico de SMTP: {e}")

            messages.error(self.request, "Ocorreu um erro ao tentar enviar o e-mail. O servidor de correio recusou a conexão. Tente novamente mais tarde ou contate o administrador.")

            return self.render_to_response(self.get_context_data(form=form))

        except Exception as e:

            logger.error(f"Erro desconhecido ao enviar e-mail: {e}")

            messages.error(self.request, "Falha interna ao processar a recuperação de senha.")

            return self.render_to_response(self.get_context_data(form=form))





@login_required

def alterar_senha(request):

    pass

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



    tipo = getattr(request.user, 'tipo_usuario', '')

    if tipo == 'morador':

        from .views_morador import morador_context

        context = morador_context(request, {}, active_page='perfil')

        return render(request, 'morador/alterar_senha.html', context)

    elif tipo == 'sindico':

        from .views_sindico import sindico_context

        context = sindico_context(request, {}, active_page='perfil')

        return render(request, 'sindico/alterar_senha.html', context)



    return render(request, 'alterar_senha.html')





@ensure_csrf_cookie

def cadastro_morador(request, codigo_convite):

    pass

    from .models import Condominio, Morador

    from django.contrib.auth import get_user_model

    UserModel = get_user_model()



    condominio = get_object_or_404(Condominio, codigo_convite=codigo_convite, ativo=True)





    request.session['condominio_convite_id'] = condominio.id



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

                usuario=user_obj,

                status_aprovacao='AGUARDANDO'

            )





            from portaria.views_morador import notificar_sindicos_do_condominio

            notificar_sindicos_do_condominio(

                condominio=condominio,

                tipo='geral',

                titulo='Novo cadastro de Morador',

                mensagem=f"{nome} ({bloco}-{apartamento}) cadastrou-se e aguarda sua aprovação.",

                link='/sindico/moradores/'

            )



            messages.success(request, f"Conta criada com sucesso! Você poderá acessar o portal assim que o síndico aprovar.")

            return redirect('login')



    return render(request, 'cadastro_morador.html', {

        'condominio': condominio,

        'form_data': form_data

    })













from django.http import JsonResponse



@login_required

def api_stats(request):

    pass

    if not (request.user.is_staff or is_porteiro(request.user)):

        return JsonResponse({'error': 'Não autorizado'}, status=403)



    cond = get_condominio_porteiro(request.user)

    filtro_cond = {'condominio': cond} if cond else {}



    return JsonResponse({

        'visitantes_no_local': Visitante.objects.filter(horario_saida__isnull=True, **filtro_cond).count(),

        'encomendas_pendentes': Encomenda.objects.filter(entregue=False, **filtro_cond).count(),

        'solicitacoes_pendentes': Solicitacao.objects.filter(status='PENDENTE', **filtro_cond).count(),

    })











@login_required

def home(request):

    if request.user.is_superuser:

        return redirect('admin:index')



    if request.user.is_staff:





        pass



    elif getattr(request.user, 'tipo_usuario', '') == 'morador':

        if not hasattr(request.user, 'morador') or not getattr(request.user, 'morador'):

            return redirect('completar_cadastro')

        return redirect('morador_home')





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





    hoje = localdate()

    base_visitantes = Visitante.objects.filter(condominio=cond) if cond else Visitante.objects.all()

    base_encomendas = Encomenda.objects.filter(condominio=cond) if cond else Encomenda.objects.all()

    base_solicitacoes = Solicitacao.objects.filter(condominio=cond) if cond else Solicitacao.objects.all()



    visitantes_hoje_total = base_visitantes.filter(horario_chegada__date=hoje).count()

    visitantes_no_local_count = base_visitantes.filter(horario_saida__isnull=True).count()



    encomendas_pendentes_count = base_encomendas.filter(entregue=False).count()

    solicitacoes_pendentes_count = base_solicitacoes.filter(status='PENDENTE').count()



    base_reservas = Reserva.objects.filter(area__condominio=cond) if cond else Reserva.objects.all()

    reservas_hoje_count = base_reservas.filter(data=hoje, status='APROVADA').count()

    inicio_semana = hoje - datetime.timedelta(days=hoje.weekday())

    fim_semana = inicio_semana + datetime.timedelta(days=6)

    lista_reservas_semana = base_reservas.filter(

        data__gte=inicio_semana,

        data__lte=fim_semana,

        status='APROVADA'

    ).select_related('area', 'morador').order_by('data', 'horario_inicio')



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

        'reservas_hoje': reservas_hoje_count,

        'lista_reservas_semana': lista_reservas_semana,

    }

    return render(request, 'index.html', context)



@login_required

def liberar_acesso_reserva(request, reserva_id):

    if not is_porteiro(request.user):

        messages.error(request, "Sem permissão.")

        return redirect('login')

    reserva = get_object_or_404(Reserva, id=reserva_id)

    if request.method == 'POST':

        nome = request.POST.get('nome_liberado', '').strip()

        if not nome:

            messages.error(request, "O nome completo é obrigatório.")

            return redirect('/?aba=reservas')

        reserva.acesso_liberado = True

        reserva.nome_liberado = nome

        reserva.bloco_apto_liberado = request.POST.get('bloco_apto_liberado', '').strip()

        reserva.documento_liberado = request.POST.get('documento_liberado', '').strip()

        reserva.data_liberacao = timezone.now()

        reserva.save()

        messages.success(request, f"Acesso liberado com sucesso para {nome} — {reserva.area.nome} ({reserva.data.strftime('%d/%m/%Y')}).")

    return redirect('/?aba=reservas')



@login_required

def mensagens_portaria(request):

    pass

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





    conversas = {}

    for msg in mensagens:

        other_user = msg.destinatario if msg.remetente == request.user else msg.remetente

        if other_user not in conversas:

            conversas[other_user] = []

        conversas[other_user].append(msg)



    mensagens_nao_lidas = 0                                                        



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



        condominio_registro = (morador.condominio if morador and morador.condominio else cond)



        visitante = Visitante.objects.create(

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



        if morador and morador.usuario:

            nome_visitante = request.POST.get('nome_completo')

            disparar_push_individual(

                morador.usuario,

                '🔔 Visitante na Portaria',

                f'O visitante {nome_visitante} acabou de ser registrado.',

                f'/morador/?visitante_id={visitante.id}'

            )



        messages.success(request, "Visitante registrado!")

    return redirect('home')



@login_required

def registrar_saida(request, id_visitante):

    visitante = get_object_or_404(Visitante, id=id_visitante)

    visitante.horario_saida = timezone.now()

    visitante.save()

    messages.info(request, "Saída registrada.")





    page = request.GET.get('page', '')

    busca = request.GET.get('busca', '')

    params = []

    if page:

        params.append(f'page={page}')

    if busca:

        params.append(f'busca={busca}')

    url = '/' + ('?' + '&'.join(params) if params else '')

    return redirect(url)











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



            if morador.usuario:

                volume = request.POST.get('volume', 'pacote')

                disparar_push_individual(

                    morador.usuario,

                    '📦 Nova Encomenda',

                    f'Uma nova encomenda ({volume}) chegou na portaria.',

                    '/morador/encomendas/'

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





        if morador and morador.usuario:

            descricao = request.POST.get('descricao', '')

            disparar_push_individual(

                morador.usuario,

                '⚠️ Aviso da Portaria',

                descricao[:50],

                '/morador/solicitacoes/'

            )



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













import json



@login_required

def api_moradores_offline(request):

    pass

    cond = get_condominio_porteiro(request.user)

    qs = Morador.objects.all().order_by('bloco', 'apartamento')

    if cond:

        qs = qs.filter(condominio=cond)

    moradores = qs.values('id', 'nome', 'bloco', 'apartamento', 'telefone')

    return JsonResponse({'moradores': list(moradores), 'porteiro': request.user.username})





@csrf_exempt

@login_required

def api_sync_offline(request):

    pass

    if request.method != 'POST':

        return JsonResponse({'error': 'Método não permitido'}, status=405)



    try:

        data = json.loads(request.body)

    except json.JSONDecodeError:

        return JsonResponse({'error': 'JSON inválido'}, status=400)



    resultados = {'visitantes_criados': 0, 'encomendas_criadas': 0, 'solicitacoes_criadas': 0, 'erros': []}



    cond = get_condominio_porteiro(request.user)





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



@login_required

def trocar_condominio(request, condominio_id):

    pass

    if request.user.condominios.filter(id=condominio_id).exists() or request.user.is_superuser:

        request.session['condominio_ativo_id'] = condominio_id

        messages.success(request, 'Condomínio alterado com sucesso.')

    else:

        messages.error(request, 'Você não tem acesso a este condomínio.')

    return redirect(request.META.get('HTTP_REFERER', '/'))







from django.views.decorators.csrf import csrf_exempt

from portaria.models import PushSubscription

import json

from django.http import JsonResponse



@csrf_exempt

@login_required

def salvar_inscricao_push(request):

    if request.user.is_authenticated and request.method == 'POST':

        try:

            data = json.loads(request.body)

            endpoint = data.get('endpoint')

            keys = data.get('keys', {})

            p256dh = keys.get('p256dh')

            auth = keys.get('auth')



            if endpoint and p256dh and auth:

                PushSubscription.objects.update_or_create(

                    usuario=request.user,

                    endpoint=endpoint,

                    defaults={'p256dh': p256dh, 'auth': auth}

                )





                request.user.receber_push = True

                request.user.save(update_fields=['receber_push'])



                return JsonResponse({'status': 'ok'})

        except Exception as e:

            pass

    return JsonResponse({'status': 'error'}, status=400)





@csrf_exempt

@login_required

def remover_subscricao(request):

    pass

    if request.user.is_authenticated and request.method == 'POST':

        try:

            data = json.loads(request.body)

            endpoint = data.get('endpoint')





            request.user.receber_push = False

            request.user.save(update_fields=['receber_push'])

            print(f"[RADAR] Preferência de Push desativada para {request.user.username}")



            if endpoint:



                PushSubscription.objects.filter(usuario=request.user, endpoint=endpoint).delete()

                print(f"[RADAR] Subscrição endpoint removida para o logado {request.user.username}")



            return JsonResponse({'status': 'sucesso', 'mensagem': 'Subscrição e preferências removidas.'})

        except json.JSONDecodeError:

            print("[RADAR ERRO] Falha ao decodificar JSON na remoção de subscrição.")



            request.user.receber_push = False

            request.user.save(update_fields=['receber_push'])

            return JsonResponse({'status': 'sucesso', 'mensagem': 'Desativado.'})

    return JsonResponse({'status': 'erro', 'mensagem': 'Requisição inválida.'}, status=400)



