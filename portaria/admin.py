from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.utils import timezone
from .models import Visitante, Morador, Encomenda

admin.site.register(Visitante)

@admin.register(Morador)
class MoradorAdmin(ImportExportModelAdmin):
    list_display = ('nome', 'bloco', 'apartamento', 'telefone')
    search_fields = ('nome', 'cpf', 'bloco', 'apartamento')
    list_filter = ('bloco',)

@admin.register(Encomenda)
class EncomendaAdmin(admin.ModelAdmin):
    list_display = ('morador', 'volume', 'data_chegada', 'entregue')
    list_filter = ('entregue', 'data_chegada')
    search_fields = ('morador__nome', 'morador__apartamento')
    
    
    actions = ['marcar_como_entregue']

    def marcar_como_entregue(self, request, queryset):
        queryset.update(entregue=True, data_entrega=timezone.now())
        self.message_user(request, "Encomendas selecionadas foram marcadas como ENTREGUES!")
    
    marcar_como_entregue.short_description = "Marcar selecionadas como Entregues"