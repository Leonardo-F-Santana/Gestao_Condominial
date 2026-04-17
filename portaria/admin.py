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

# --- MIXIN DE SEGURANÇA MULTI-TENANT (SaaS) ---

class TenantAdminMixin:
    """Garante que cada condomínio só veja seus próprios dados"""
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and hasattr(request.user, 'condominio') and request.user.condominio:
            if db_field.name == "morador":
                kwargs["queryset"] = Morador.objects.filter(condominio=request.user.condominio)
            if db_field.name == "condominio":
                kwargs["queryset"] = Condominio.objects.filter(id=request.user.condominio.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# --- INLINES PARA O PAINEL DO CONDOMÍNIO ---

class DocumentoInline(TabularInline):
    model = DocumentoCondominio
    extra = 0

class MoradorInline(StackedInline):
    model = Morador
    extra = 0
    can_delete = False
    autocomplete_fields = ['condominio']

class SindicoUserInline(TabularInline):
    model = User.condominios.through
    extra = 0
    verbose_name = "Síndico vinculado"
    def get_queryset(self, request):
        return super().get_queryset(request).filter(customuser__tipo_usuario='sindico')

# --- CONFIGURAÇÃO DE USUÁRIOS ---

admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'first_name', 'email', 'tipo_usuario', 'is_active')
    list_filter = ('condominios', 'tipo_usuario', 'is_active')
    inlines = [MoradorInline]
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Classificação', {'fields': ('tipo_usuario', 'condominios')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

# --- GESTÃO DE CONDOMÍNIOS ---

@admin.register(Condominio)
class CondominioAdmin(ModelAdmin):
    list_display = ('nome', 'cnpj', 'get_status_ativo')
    search_fields = ('nome', 'cnpj')
    inlines = [SindicoUserInline, DocumentoInline]

    def get_status_ativo(self, obj):
        color = "#22c55e" if obj.ativo else "#ef4444"
        return format_html('<span style="color: {}; font-weight: bold;">● {}</span>', color, "Ativo" if obj.ativo else "Inativo")
    get_status_ativo.short_description = 'Status'

@admin.register(Sindico)
class SindicoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'usuario', 'telefone')

@admin.register(Porteiro)
class PorteiroAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'condominio', 'cargo')

# --- MORADORES COM AUTO-USER E IMPORTAÇÃO ---

class MoradorResource(resources.ModelResource):
    class Meta:
        model = Morador
        fields = ('nome', 'cpf', 'bloco', 'apartamento', 'email')
        import_id_fields = ('cpf',)

@admin.register(Morador)
class MoradorAdmin(TenantAdminMixin, ModelAdmin):
    resource_class = MoradorResource
    list_display = ('nome', 'condominio', 'bloco', 'apartamento', 'get_usuario_status')
    search_fields = ('nome', 'cpf', 'apartamento')

    def get_usuario_status(self, obj):
        color = "green" if obj.usuario and obj.usuario.is_active else "gray"
        return format_html('<span style="color: {};">{}</span>', color, "Ativo" if obj.usuario else "Sem Login")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.usuario:
            # Lógica comercial de criar usuário automático ao cadastrar morador
            username = f"{obj.nome.split()[0].lower()}.{obj.apartamento}"
            user = User.objects.create_user(username=username, password='mudar123', email=obj.email or '', tipo_usuario='morador')
            cond = obj.condominio if obj.condominio else request.user.condominio
            if cond: user.condominios.add(cond)
            obj.usuario = user
        super().save_model(request, obj, form, change)

# --- OPERACIONAL ---

@admin.register(Cobranca)
class CobrancaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('descricao', 'morador', 'valor', 'get_status_html')
    def get_status_html(self, obj):
        cores = {'PENDENTE': 'orange', 'PAGO': 'green', 'ATRASADO': 'red'}
        return format_html('<b style="color: {};">{}</b>', cores.get(obj.status, 'black'), obj.status)

@admin.register(Visitante)
class VisitanteAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome_completo', 'condominio', 'horario_chegada')

@admin.register(Encomenda)
class EncomendaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('id', 'morador', 'entregue')

@admin.register(Solicitacao)
class SolicitacaoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('tipo', 'morador', 'status')

@admin.register(PushSubscription)
class PushSubscriptionAdmin(ModelAdmin):
    list_display = ('usuario', 'get_condominio_name', 'endpoint', 'criado_em')
    readonly_fields = ('usuario', 'endpoint', 'p256dh', 'auth', 'criado_em')
    def get_condominio_name(self, obj):
        cond = obj.usuario.condominios.first()
        return cond.nome if cond else "Nenhum"

# Registrar os demais modelos básicos
admin.site.register([Aviso, Notificacao, AreaComum, Reserva, Mensagem, Ocorrencia, DocumentoCondominio])