from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.utils.html import format_html
from import_export import resources
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.forms import AdminPasswordChangeForm
from .models import (
    Condominio, Sindico, Porteiro, Visitante, Morador, Encomenda, Solicitacao, Aviso, Notificacao, 
    AreaComum, Reserva, Cobranca, Mensagem, Ocorrencia, DocumentoCondominio, PushSubscription
)
from .forms import CustomUserChangeForm, CustomUserCreationForm

User = get_user_model()

# --- MIXIN DE SEGURANÇA MULTI-TENANT ---

class TenantAdminMixin:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'condominio') and request.user.condominio:
            return qs.filter(condominio=request.user.condominio)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            if hasattr(obj, 'condominio_id') and obj.condominio_id is None:
                obj.condominio = request.user.condominio
        super().save_model(request, obj, form, change)

# --- CONFIGURAÇÃO DE USUÁRIOS ---

admin.site.unregister(Group)

class MoradorInline(StackedInline):
    model = Morador
    extra = 0
    can_delete = False

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'tipo_usuario', 'is_active')
    inlines = [MoradorInline]

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

# --- GESTÃO DE CONDOMÍNIOS ---

@admin.register(Condominio)
class CondominioAdmin(ModelAdmin):
    list_display = ('nome', 'cnpj', 'ativo')
    search_fields = ('nome', 'cnpj')

@admin.register(Sindico)
class SindicoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'usuario', 'condominio')

@admin.register(Porteiro)
class PorteiroAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'condominio', 'cargo')

# --- OPERACIONAL MORADORES ---

class MoradorResource(resources.ModelResource):
    class Meta:
        model = Morador
        fields = ('nome', 'cpf', 'bloco', 'apartamento', 'email')
        import_id_fields = ('cpf',)

@admin.register(Morador)
class MoradorAdmin(TenantAdminMixin, ModelAdmin):
    resource_class = MoradorResource
    list_display = ('nome', 'condominio', 'bloco', 'apartamento')
    search_fields = ('nome', 'cpf', 'apartamento')

@admin.register(Visitante)
class VisitanteAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome_completo', 'condominio', 'horario_chegada')

@admin.register(Encomenda)
class EncomendaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('id', 'morador', 'condominio', 'entregue')

@admin.register(Solicitacao)
class SolicitacaoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('tipo', 'morador', 'status', 'data_criacao')

@admin.register(Cobranca)
class CobrancaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('descricao', 'morador', 'valor', 'status')

@admin.register(Aviso)
class AvisoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('titulo', 'condominio', 'data_publicacao')

@admin.register(Notificacao)
class NotificacaoAdmin(ModelAdmin):
    list_display = ('usuario', 'mensagem', 'lida')

@admin.register(AreaComum)
class AreaComumAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'condominio', 'capacidade')

@admin.register(Reserva)
class ReservaAdmin(ModelAdmin):
    list_display = ('area', 'morador', 'data', 'status')

@admin.register(Mensagem)
class MensagemAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('remetente', 'destinatario', 'data_envio')

@admin.register(Ocorrencia)
class OcorrenciaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('autor', 'condominio', 'status')

@admin.register(DocumentoCondominio)
class DocumentoCondominioAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('titulo', 'condominio', 'data_upload')

# --- NOTIFICAÇÕES WEB PUSH (CORRIGIDO) ---

@admin.register(PushSubscription)
class PushSubscriptionAdmin(ModelAdmin):
    list_display = ('usuario', 'get_condominio_name', 'endpoint', 'criado_em')
    list_filter = ('criado_em',)
    readonly_fields = ('usuario', 'endpoint', 'p256dh', 'auth', 'criado_em')

    def get_condominio_name(self, obj):
        cond = obj.usuario.condominios.first()
        return cond.nome if cond else "Nenhum"
    get_condominio_name.short_description = 'Condomínio'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        condominio_ativo = getattr(request.user, 'get_condominio_ativo', None)
        if condominio_ativo:
            return qs.filter(usuario__condominios=condominio_ativo)
        return qs.none()