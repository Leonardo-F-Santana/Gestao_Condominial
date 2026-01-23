from django.db import models

class Visitante(models.Model):
    nome_completo = models.CharField(max_length=190, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=15, verbose_name="CPF")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    numero_casa = models.CharField(max_length=30, verbose_name="Número da Casa/Apto")
    placa_veiculo = models.CharField(max_length=7, blank=True, null=True, verbose_name="Placa do Carro")
    horario_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Chegada")
    
    def __str__(self):
        return self.nome_completo