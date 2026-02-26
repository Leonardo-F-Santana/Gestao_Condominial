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


from unfold.admin import ModelAdmin, StackedInline

class MoradorInline(StackedInline):
    model = Morador
    extra = 0
    can_delete = False
    autocomplete_fields = ['condominio']
    
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
    inlines = [MoradorInline]
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
    list_display = ('nome', 'condominio', 'bloco', 'apartamento', 'get_usuario_status')
    list_filter = ('condominio', 'bloco')
    search_fields = ('nome', 'apartamento', 'cpf', 'email')
    ordering = ('condominio', 'bloco', 'apartamento')

    def get_usuario_status(self, obj):
        if obj.usuario:
            if obj.usuario.is_active:
                return format_html('<span style="color: green;">Ativo</span>')
            return format_html('<span style="color: orange;">Inativo</span>')
        return format_html('<span style="color: gray;">Sem Login</span>')
    get_usuario_status.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.usuario:
            # Generate a default user
            username = f"{obj.nome.split()[0].lower()}.{obj.apartamento}"
            if obj.bloco:
                username += f".{obj.bloco.lower()}"
                
            # Ensure uniqueness
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                password='mudar123',
                first_name=obj.nome.split()[0] if obj.nome else '',
                email=obj.email or '',
                tipo_usuario='morador',
                condominio=obj.condominio if obj.condominio else request.user.condominio
            )
            obj.usuario = user
            
            # Show a success message to the admin
            from django.contrib import messages
            messages.success(request, f"Conta criada automaticamente: Login = '{username}' | Senha = 'mudar123'")

        super().save_model(request, obj, form, change)

# --- OUTROS CADASTROS (REMOVIDOS DO ADMIN GLOBAL) ---

# Os models operacionais (Visitante, Encomenda, Solicitacao, Aviso, Notificacao, AreaComum, Reserva)
# foram ocultados do painel global de administração conforme o requisito 4.
