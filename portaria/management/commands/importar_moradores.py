import csv
from django.core.management.base import BaseCommand
from portaria.models import Morador

class Command(BaseCommand):
    help = 'Importa moradores de um arquivo CSV'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando importação...'))

        
        with open('moradores.csv', encoding='utf-8') as arquivo:
            leitor = csv.DictReader(arquivo)
            
            contador = 0
            
            for linha in leitor:
               
                morador, created = Morador.objects.get_or_create(
                    cpf=linha['cpf'], 
                    defaults={
                        'nome': linha['nome'],
                        'bloco': linha['bloco'],
                        'apartamento': linha['apartamento'],
                        'telefone': linha['telefone']
                    }
                )
                
                if created:
                    contador += 1
                    
                    self.stdout.write(f"Criado: {morador.nome} - {morador.apartamento}")
                else:
                    self.stdout.write(f"Já existe: {morador.nome}")

        self.stdout.write(self.style.SUCCESS(f'Processo finalizado! {contador} novos moradores importados.'))