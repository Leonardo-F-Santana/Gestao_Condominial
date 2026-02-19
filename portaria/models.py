from django.db import models
from django.contrib.auth.models import User
import uuid


# ==========================================
# MULTI-TENANCY: Modelos Base
# ==========================================

class Condominio(models.Model):
    """Representa um condomínio no sistema multi-tenant"""
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


class Sindico(models.Model):
    """Síndico/Administrador que gerencia um ou mais condomínios"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sindico')
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    condominios = models.ManyToManyField(Condominio, related_name='sindicos', 
                                          verbose_name="Condomínios Gerenciados")

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"

    class Meta:
        verbose_name = "Síndico"
        verbose_name_plural = "Síndicos"


# ==========================================
# MODELOS PRINCIPAIS
# ==========================================

class Morador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, 
                                    null=True, blank=True, verbose_name="Condomínio")
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    verbose_name="Conta de Acesso", related_name='morador')
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="E-mail", blank=True)
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone", blank=True)
    bloco = models.CharField(max_length=10, verbose_name="Bloco", blank=True)
    apartamento = models.CharField(max_length=10, verbose_name="Apartamento")

    def __str__(self):
        if self.bloco:
            return f"{self.bloco} - {self.apartamento} - {self.nome}"
        return f"{self.apartamento} - {self.nome}"

class Visitante(models.Model):
    nome_completo = models.CharField(max_length=100, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True, null=True)
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", blank=True, null=True)
    numero_casa = models.CharField(max_length=10, verbose_name="Número da Casa/Apto (Antigo)", blank=True)
    morador_responsavel = models.ForeignKey(Morador, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Morador Responsável")
    placa_veiculo = models.CharField(max_length=20, verbose_name="Placa do Veículo", blank=True)
    horario_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Horário de Chegada")
    horario_saida = models.DateTimeField(null=True, blank=True, verbose_name="Horário de Saída")
    quem_autorizou = models.CharField(max_length=100, verbose_name="Quem Autorizou?", blank=True)
    observacoes = models.TextField(verbose_name="Observações", blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Porteiro Responsável")

    def __str__(self):
        return self.nome_completo

class Encomenda(models.Model):
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE, verbose_name="Morador")
    data_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Data de Chegada")
    volume = models.CharField(max_length=50, verbose_name="Volume")
    destinatario_alternativo = models.CharField(max_length=100, blank=True, verbose_name="Destinatário Externo (A/C)")
    entregue = models.BooleanField(default=False, verbose_name="Entregue?")
    data_entrega = models.DateTimeField(null=True, blank=True, verbose_name="Data da Entrega")
    quem_retirou = models.CharField(max_length=100, blank=True, verbose_name="Quem retirou?")
    documento_retirada = models.CharField(max_length=50, blank=True, verbose_name="Documento de quem retirou")
    notificado = models.BooleanField(default=False, verbose_name="Morador foi avisado?")
    porteiro_cadastro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cadastrou_encomenda')
    porteiro_entrega = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='entregou_encomenda')

    def __str__(self):
        return f"{self.volume} - {self.morador}"

class Solicitacao(models.Model):
    TIPOS_CHOICES = [
        ('RECLAMACAO', '📢 Reclamação'),
        ('MANUTENCAO', '🛠️ Manutenção'),
        ('MUDANCA', '🚚 Mudança'),
        ('RESERVA', '📅 Reserva de Espaço'),
        ('OUTRO', '📝 Outro'),
    ]

    STATUS_CHOICES = [
        ('PENDENTE', '🟡 Pendente'),
        ('EM_ANDAMENTO', '🔵 Em Andamento'),
        ('CONCLUIDO', '🟢 Concluído'),
        ('CANCELADO', '🔴 Cancelado'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS_CHOICES, verbose_name="Tipo de Solicitação")
    descricao = models.TextField(verbose_name="Descrição do Pedido")
    morador = models.ForeignKey(Morador, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Morador Solicitante")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name="Status Atual")
    arquivo = models.FileField(upload_to='solicitacoes/%Y/%m/', blank=True, verbose_name="Foto/Vídeo")
    
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Registrado por")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data do Registro")
    resposta_admin = models.TextField(blank=True, verbose_name="Resposta da Administração")

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.morador or 'Portaria'}"

    class Meta:
        verbose_name = "Solicitação / Ocorrência"
        verbose_name_plural = "Solicitações e Ocorrências"


class Aviso(models.Model):
    """Avisos e comunicados do condomínio para os moradores"""
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, null=True, blank=True,
                                    verbose_name="Condomínio", related_name='avisos')
    titulo = models.CharField(max_length=200, verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo")
    imagem = models.ImageField(upload_to='avisos/%Y/%m/', blank=True, verbose_name="Imagem")
    arquivo = models.FileField(upload_to='avisos/anexos/%Y/%m/', blank=True, verbose_name="Arquivo Anexo")
    data_publicacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Publicação")
    data_expiracao = models.DateField(null=True, blank=True, verbose_name="Data de Expiração")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Aviso"
        verbose_name_plural = "Avisos"
        ordering = ['-data_publicacao']


class Notificacao(models.Model):
    """Notificações para moradores e síndicos"""
    TIPO_CHOICES = [
        ('aviso', '📢 Novo Aviso'),
        ('solicitacao', '📋 Nova Solicitação'),
        ('resposta_solicitacao', '💬 Resposta de Solicitação'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensagem = models.CharField(max_length=200)
    link = models.CharField(max_length=200, blank=True)
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} → {self.usuario.username}"

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-data_criacao']