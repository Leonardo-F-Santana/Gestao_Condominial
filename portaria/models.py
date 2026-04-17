from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# ==========================================
# MULTI-TENANCY: Modelos Base
# ==========================================

class Condominio(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Condomínio")
    endereco = models.CharField(max_length=200, blank=True, verbose_name="Endereço")
    cnpj = models.CharField(max_length=18, blank=True, verbose_name="CNPJ")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    logo = models.ImageField(upload_to='condominios/', blank=True, verbose_name="Logo")
    codigo_convite = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="Código de Convite")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Condomínio"
        verbose_name_plural = "Condomínios"
        ordering = ['nome']

class CustomUser(AbstractUser):
    TIPO_CHOICES = (
        ('sindico', 'Síndico'),
        ('porteiro', 'Porteiro'),
        ('morador', 'Morador'),
        ('admin', 'Administrador SaaS'),
    )
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, default='morador', verbose_name="Tipo de Usuário")
    condominios = models.ManyToManyField(Condominio, blank=True, related_name='usuarios')

    @property
    def get_condominio_ativo(self):
        return self.condominios.first()

    @property
    def condominio(self):
        return self.get_condominio_ativo

    def __str__(self):
        condominio_ativo = self.get_condominio_ativo
        if condominio_ativo:
            return f"{self.username} - {condominio_ativo.nome}"
        return self.username

class Sindico(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sindico')
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='sindicos_perfil', verbose_name="Condomínio")

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"

    class Meta:
        verbose_name = "Síndico"
        verbose_name_plural = "Síndicos"

class Porteiro(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='porteiro_perfil')
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='porteiros', verbose_name="Condomínio")
    cargo = models.CharField(max_length=50, default='Porteiro', verbose_name="Cargo")

    def __str__(self):
        return f"{self.nome} — {self.condominio.nome}"

    class Meta:
        verbose_name = "Porteiro / Acesso"
        verbose_name_plural = "Porteiros e Acessos"

class Morador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, verbose_name="Condomínio")
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Conta de Acesso", related_name='morador')
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="E-mail", blank=True)
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone", blank=True)
    bloco = models.CharField(max_length=10, verbose_name="Bloco", blank=True)
    apartamento = models.CharField(max_length=10, verbose_name="Apartamento")
    status_aprovacao = models.CharField(max_length=20, default='APROVADO', verbose_name="Status")

    def __str__(self):
        return f"{self.apartamento} - {self.nome}"

    class Meta:
        verbose_name = "Morador"
        verbose_name_plural = "Moradores"
        ordering = ['bloco', 'apartamento']

class Cobranca(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='cobrancas', verbose_name="Condomínio")
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE, related_name='cobrancas', verbose_name="Morador")
    descricao = models.CharField(max_length=200, verbose_name="Descrição", default="Taxa Condominial")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    data_vencimento = models.DateField(verbose_name="Vencimento")
    status = models.CharField(max_length=20, default='PENDENTE', verbose_name="Status")

    class Meta:
        verbose_name = "Cobrança"
        verbose_name_plural = "Cobranças"

class Visitante(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='visitantes')
    nome_completo = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    morador_responsavel = models.ForeignKey(Morador, on_delete=models.SET_NULL, null=True, blank=True)
    horario_chegada = models.DateTimeField(auto_now_add=True)

class Encomenda(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='encomendas')
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE)
    data_chegada = models.DateTimeField(auto_now_add=True)
    volume = models.CharField(max_length=50)
    entregue = models.BooleanField(default=False)

class Solicitacao(models.Model):
    tipo = models.CharField(max_length=20)
    descricao = models.TextField()
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='solicitacoes')
    morador = models.ForeignKey(Morador, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDENTE')
    data_criacao = models.DateTimeField(auto_now_add=True)

class Aviso(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='avisos')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    data_publicacao = models.DateTimeField(auto_now_add=True)

class Notificacao(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificacoes')
    mensagem = models.CharField(max_length=200)
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

class AreaComum(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='areas_comuns')
    nome = models.CharField(max_length=100)
    capacidade = models.PositiveIntegerField()

class Reserva(models.Model):
    area = models.ForeignKey(AreaComum, on_delete=models.CASCADE, related_name='reservas')
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE)
    data = models.DateField()
    status = models.CharField(max_length=20, default='PENDENTE')

class Mensagem(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensagens_recebidas')
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

class Ocorrencia(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='ocorrencias')
    autor = models.ForeignKey(Morador, on_delete=models.CASCADE)
    descricao = models.TextField()
    status = models.CharField(max_length=20, default='REGISTRADA')
    data_registro = models.DateTimeField(auto_now_add=True)

class DocumentoCondominio(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='documentos/')
    data_upload = models.DateTimeField(auto_now_add=True)

class PushSubscription(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=200)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscrição Web Push"
        verbose_name_plural = "Inscrições Web Push"

    def __str__(self):
        return f"Push de {self.usuario.username}"