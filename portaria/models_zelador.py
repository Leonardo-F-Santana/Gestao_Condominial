from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Condominio

def validate_file_size(value):
    filesize = value.size
    
    if filesize > 5242880:
        raise ValidationError("O tamanho máximo do arquivo é 5MB")
    else:
        return value

class ChecklistZelador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    concluido = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    zelador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.titulo

class OrdemServicoZelador(models.Model):
    STATUS_CHOICES = (
        ('ABERTA', 'Aberta'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDA', 'Concluída'),
    )
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTA')
    foto = models.ImageField(upload_to='os_zelador/', blank=True, null=True, validators=[validate_file_size])
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_encerramento = models.DateTimeField(null=True, blank=True)
    zelador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.titulo

class AgendaZelador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    data_manutencao = models.DateField()
    descricao = models.TextField(blank=True, null=True)
    realizada = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo

class LivroOcorrenciaZelador(models.Model):
    GRAVIDADE_CHOICES = (
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta (Grave)'),
    )
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    gravidade = models.CharField(max_length=10, choices=GRAVIDADE_CHOICES, default='BAIXA')
    foto = models.ImageField(upload_to='ocorrencias_zelador/', blank=True, null=True, validators=[validate_file_size])
    data_registro = models.DateTimeField(auto_now_add=True)
    zelador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.titulo

class PrestadorServicoZelador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200, blank=True, null=True)
    documento = models.CharField(max_length=50, blank=True, null=True)
    data_entrada = models.DateTimeField(auto_now_add=True)
    liberado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.nome

class EstoqueZelador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    quantidade_atual = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(default=0)

    def __str__(self):
        return self.nome
