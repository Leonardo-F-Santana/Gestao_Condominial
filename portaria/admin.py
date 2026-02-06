from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from .models import Visitante, Morador, Encomenda, Solicitacao, Aviso

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
class MoradorAdmin(ModelAdmin):
    resource_class = MoradorResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('nome', 'bloco', 'apartamento', 'telefone', 'email')
    list_filter = ('bloco',)
    search_fields = ('nome', 'apartamento', 'cpf', 'email')
    ordering = ('bloco', 'apartamento')

# --- OUTROS CADASTROS ---

@admin.register(Visitante)
class VisitanteAdmin(ModelAdmin):
    list_display = ('nome_completo', 'morador_responsavel', 'horario_chegada', 'horario_saida', 'registrado_por')
    list_filter = ('horario_chegada', 'registrado_por')
    search_fields = ('nome_completo', 'cpf', 'placa_veiculo')
    readonly_fields = ('horario_chegada', 'registrado_por')

@admin.register(Encomenda)
class EncomendaAdmin(ModelAdmin):
    list_display = ('morador', 'volume', 'data_chegada', 'get_status_html', 'porteiro_cadastro')
    list_filter = ('entregue', 'data_chegada', 'porteiro_cadastro')
    search_fields = ('morador__nome', 'volume', 'quem_retirou')
    readonly_fields = ('data_chegada', 'data_entrega', 'porteiro_cadastro', 'porteiro_entrega')

    def get_status_html(self, obj):
        if obj.entregue:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✅ Entregue')
        return format_html('<span style="color: orange; font-weight: bold;">{}</span>', '📦 Na Portaria')
    get_status_html.short_description = 'Status'

@admin.register(Solicitacao)
class SolicitacaoAdmin(ModelAdmin):
    list_display = ('get_tipo_html', 'morador', 'descricao_curta', 'criado_por', 'data_criacao', 'get_status_html')
    list_filter = ('status', 'tipo', 'data_criacao', 'criado_por')
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
class AvisoAdmin(ModelAdmin):
    list_display = ('titulo', 'data_publicacao', 'ativo', 'criado_por')
    list_filter = ('ativo', 'data_publicacao')
    search_fields = ('titulo', 'conteudo')
    readonly_fields = ('data_publicacao', 'criado_por')
    list_editable = ('ativo',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)