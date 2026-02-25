from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.utils.html import format_html
from import_export import resources
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.forms import AdminPasswordChangeForm
from .models import Condominio, Sindico, Porteiro, Visitante, Morador, Encomenda, Solicitacao, Aviso, Notificacao, AreaComum, Reserva
from .forms import CustomUserChangeForm, CustomUserCreationForm

User = get_user_model()

# --- CONFIGURAÇÃO DE USUÁRIOS (Django Auth) ---

# Desregistrar o admin padrão
# admin.site.unregister(User)
admin.site.unregister(Group)

class TenantAdminMixin:
    """Mixin para gerenciar o isolamento de dados por condomínio e ocultar dos superusuários"""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.none() # Superuser não vê dados operacionais
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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return False
        return super().has_module_permission(request)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm
    filter_horizontal = ('groups',)
    list_display = ('username', 'first_name', 'last_name', 'email', 'tipo_usuario', 'condominio', 'is_staff', 'is_active')
    list_filter = ('tipo_usuario', 'condominio', 'is_staff', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Classificação', {'fields': ('tipo_usuario', 'condominio')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Classificação', {
            'classes': ('wide',),
            'fields': ('tipo_usuario', 'condominio'),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'condominio') and request.user.condominio:
            return qs.filter(condominio=request.user.condominio)
        return qs.none()

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


# --- CONFIGURAÇÃO DE CONDOMÍNIOS (MULTI-TENANCY) ---

@admin.register(Condominio)
class CondominioAdmin(ModelAdmin):
    list_display = ('nome', 'endereco', 'cnpj', 'telefone', 'ativo', 'data_criacao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'endereco', 'cnpj')
    list_editable = ('ativo',)


@admin.register(Sindico)
class SindicoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'usuario', 'telefone', 'get_condominios')
    search_fields = ('nome', 'usuario__username')

    def get_condominios(self, obj):
        return obj.condominio.nome if obj.condominio else ""
    get_condominios.short_description = 'Condomínio'


@admin.register(Porteiro)
class PorteiroAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'usuario', 'condominio', 'cargo')
    list_filter = ('condominio', 'cargo')
    search_fields = ('nome', 'usuario__username', 'condominio__nome')
    autocomplete_fields = ('usuario', 'condominio')


# --- CONFIGURAÇÃO DE MORADORES (COM IMPORTAÇÃO) ---


# 1. Receita de como ler o Excel
class MoradorResource(resources.ModelResource):
    class Meta:
        model = Morador
        # Campos que podem vir no Excel
        fields = ('nome', 'cpf', 'bloco', 'apartamento', 'telefone', 'email')
        # Identificador único (se o CPF já existir, ele atualiza em vez de duplicar)
        import_id_fields = ('cpf',)

@admin.register(Morador)
class MoradorAdmin(TenantAdminMixin, ModelAdmin):
    resource_class = MoradorResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('nome', 'bloco', 'apartamento', 'telefone', 'email')
    list_filter = ('bloco',)
    search_fields = ('nome', 'apartamento', 'cpf', 'email')
    ordering = ('bloco', 'apartamento')

# --- OUTROS CADASTROS ---

@admin.register(Visitante)
class VisitanteAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome_completo', 'condominio', 'morador_responsavel', 'horario_chegada', 'horario_saida', 'registrado_por')
    list_filter = ('condominio', 'horario_chegada', 'registrado_por')
    search_fields = ('nome_completo', 'cpf', 'placa_veiculo')
    readonly_fields = ('horario_chegada', 'registrado_por')

@admin.register(Encomenda)
class EncomendaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('morador', 'condominio', 'volume', 'data_chegada', 'get_status_html', 'porteiro_cadastro')
    list_filter = ('condominio', 'entregue', 'data_chegada', 'porteiro_cadastro')
    search_fields = ('morador__nome', 'volume', 'quem_retirou')
    readonly_fields = ('data_chegada', 'data_entrega', 'porteiro_cadastro', 'porteiro_entrega')

    def get_status_html(self, obj):
        if obj.entregue:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✅ Entregue')
        return format_html('<span style="color: orange; font-weight: bold;">{}</span>', '📦 Na Portaria')
    get_status_html.short_description = 'Status'

@admin.register(Solicitacao)
class SolicitacaoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('get_tipo_html', 'condominio', 'morador', 'descricao_curta', 'criado_por', 'data_criacao', 'get_status_html')
    list_filter = ('condominio', 'status', 'tipo', 'data_criacao', 'criado_por')
    search_fields = ('descricao', 'morador__nome', 'morador__apartamento')
    readonly_fields = ('data_criacao', 'criado_por')

    def get_status_html(self, obj):
        cores = {
            'PENDENTE': 'orange',
            'EM_ANDAMENTO': 'blue',
            'CONCLUIDO': 'green',
            'CANCELADO': 'red',
        }
        cor = cores.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            cor,
            obj.get_status_display()
        )
    get_status_html.short_description = 'Situação'

    def get_tipo_html(self, obj):
        return obj.get_tipo_display()
    get_tipo_html.short_description = 'Tipo'

    def descricao_curta(self, obj):
        if len(obj.descricao) > 50:
            return obj.descricao[:50] + "..."
        return obj.descricao
    descricao_curta.short_description = "Descrição Detalhada"


@admin.register(Aviso)
class AvisoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('titulo', 'data_publicacao', 'ativo', 'criado_por')
    list_filter = ('ativo', 'data_publicacao')
    search_fields = ('titulo', 'conteudo')
    readonly_fields = ('data_publicacao', 'criado_por')
    list_editable = ('ativo',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
        
        # Criar notificações para todos os moradores do condomínio (apenas ao criar)
        if not change and obj.condominio:
            moradores = Morador.objects.filter(
                condominio=obj.condominio, usuario__isnull=False
            )
            notificacoes = [
                Notificacao(
                    usuario=m.usuario,
                    tipo='aviso',
                    mensagem=f'Novo aviso: {obj.titulo[:80]}',
                    link='/morador/avisos/'
                ) for m in moradores
            ]
            Notificacao.objects.bulk_create(notificacoes)


@admin.register(Notificacao)
class NotificacaoAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('tipo', 'usuario', 'mensagem', 'lida', 'data_criacao')
    list_filter = ('tipo', 'lida')
    search_fields = ('mensagem', 'usuario__username')
    readonly_fields = ('data_criacao',)
    list_editable = ('lida',)


@admin.register(AreaComum)
class AreaComumAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('nome', 'condominio', 'capacidade', 'horario_abertura', 'horario_fechamento', 'ativo')
    list_filter = ('condominio', 'ativo')
    search_fields = ('nome',)
    list_editable = ('ativo',)


@admin.register(Reserva)
class ReservaAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ('area', 'morador', 'data', 'horario_inicio', 'horario_fim', 'get_status_html')
    list_filter = ('status', 'data', 'area')
    search_fields = ('area__nome', 'morador__nome')
    readonly_fields = ('data_criacao',)

    def get_status_html(self, obj):
        cores = {
            'PENDENTE': 'orange',
            'APROVADA': 'green',
            'RECUSADA': 'red',
            'CANCELADA': 'gray',
        }
        cor = cores.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            cor,
            obj.get_status_display()
        )
    get_status_html.short_description = 'Status'
