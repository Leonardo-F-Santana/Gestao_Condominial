from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Visitante, Morador, Encomenda, Solicitacao

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
class MoradorAdmin(ImportExportModelAdmin):  # Mudamos de admin.ModelAdmin para ImportExportModelAdmin
    resource_class = MoradorResource
    list_display = ('nome', 'bloco', 'apartamento', 'telefone')
    list_filter = ('bloco',)
    search_fields = ('nome', 'apartamento', 'cpf')
    ordering = ('bloco', 'apartamento')

# --- OUTROS CADASTROS (MANTIDOS IGUAIS) ---

@admin.register(Visitante)
class VisitanteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'morador_responsavel', 'horario_chegada', 'horario_saida', 'registrado_por')
    list_filter = ('horario_chegada', 'registrado_por')
    search_fields = ('nome_completo', 'cpf', 'placa_veiculo')
    readonly_fields = ('horario_chegada', 'registrado_por')

@admin.register(Encomenda)
class EncomendaAdmin(admin.ModelAdmin):
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
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('get_tipo_html', 'morador', 'descricao_curta', 'criado_por', 'data_criacao', 'get_status_html')
    list_filter = ('status', 'tipo', 'data_criacao', 'criado_por')
    search_fields = ('descricao', 'morador__nome', 'morador__apartamento')
    readonly_fields = ('data_criacao', 'criado_por')

    def get_status_html(self, obj):
        cores = {
            'PENDENTE': 'orange',
            'EM_ANALISE': 'blue',
            'APROVADO': 'green',
            'NEGADO': 'red',
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