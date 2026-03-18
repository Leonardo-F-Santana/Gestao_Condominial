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


class CustomUser(AbstractUser):
    TIPO_CHOICES = (
        ('sindico', 'Síndico'),
        ('porteiro', 'Porteiro'),
        ('morador', 'Morador'),
        ('admin', 'Administrador SaaS'),
    )
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, default='morador', verbose_name="Tipo de Usuário")
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios_cadastrados', verbose_name="Condomínio")

    def __str__(self):
        if self.condominio:
            return f"{self.username} - {self.condominio.nome}"
        return self.username


class Sindico(models.Model):
    """Síndico/Administrador que gerencia um condomínio"""
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
    """Porteiro/Zelador vinculado a um condomínio específico"""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='porteiro_perfil')
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, 
                                    related_name='porteiros', verbose_name="Condomínio")
    cargo = models.CharField(max_length=50, default='Porteiro', verbose_name="Cargo",
                              help_text="Ex: Porteiro, Zelador, Segurança")

    def __str__(self):
        return f"{self.nome} — {self.condominio.nome} ({self.cargo})"

    class Meta:
        verbose_name = "Porteiro / Acesso"
        verbose_name_plural = "Porteiros e Acessos"


# ==========================================
# MODELOS PRINCIPAIS
# ==========================================

class Morador(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, 
                                    verbose_name="Condomínio")
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
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

    class Meta:
        verbose_name = "Morador"
        verbose_name_plural = "Moradores"
        ordering = ['bloco', 'apartamento']


class Cobranca(models.Model):
    """Gestão de pagamentos e taxas do condomínio"""
    STATUS_CHOICES = [
        ('PENDENTE', '🟡 Pendente'),
        ('EM_ANALISE', '🟠 Em Análise'),
        ('PAGO', '🟢 Pago'),
        ('ATRASADO', '🔴 Atrasado'),
        ('CANCELADO', '⚫ Cancelado'),
    ]

    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, 
                                    related_name='cobrancas', verbose_name="Condomínio")
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE, 
                                 related_name='cobrancas', verbose_name="Morador")
    descricao = models.CharField(max_length=200, verbose_name="Descrição da Cobrança", default="Taxa Condominial")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data do Pagamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name="Status")
    
    arquivo_boleto = models.FileField(upload_to='cobrancas/boletos/', null=True, blank=True, verbose_name="Arquivo do Boleto")
    comprovante = models.FileField(upload_to='cobrancas/comprovantes/', null=True, blank=True, verbose_name="Comprovante de Pagamento")
    chave_pix = models.CharField(max_length=255, null=True, blank=True, verbose_name="Chave PIX ou Link")
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Gerado em")

    def __str__(self):
        return f"{self.descricao} - {self.morador} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Cobrança"
        verbose_name_plural = "Cobranças"
        ordering = ['-data_vencimento']


class Visitante(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE,
                                    verbose_name="Condomínio",
                                    related_name='visitantes')
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
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Porteiro Responsável")

    def __str__(self):
        return self.nome_completo

class Encomenda(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE,
                                    verbose_name="Condomínio",
                                    related_name='encomendas')
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE, verbose_name="Morador")
    data_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Data de Chegada")
    volume = models.CharField(max_length=50, verbose_name="Volume")
    destinatario_alternativo = models.CharField(max_length=100, blank=True, verbose_name="Destinatário Externo (A/C)")
    entregue = models.BooleanField(default=False, verbose_name="Entregue?")
    data_entrega = models.DateTimeField(null=True, blank=True, verbose_name="Data da Entrega")
    quem_retirou = models.CharField(max_length=100, blank=True, verbose_name="Quem retirou?")
    documento_retirada = models.CharField(max_length=50, blank=True, verbose_name="Documento de quem retirou")
    notificado = models.BooleanField(default=False, verbose_name="Morador foi avisado?")
    porteiro_cadastro = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cadastrou_encomenda')
    porteiro_entrega = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='entregou_encomenda')

    def __str__(self):
        return f"{self.volume} - {self.morador}"

class Solicitacao(models.Model):
    TIPOS_CHOICES = [
        ('DUVIDA', '❓ Dúvida'),
        ('SUGESTAO', '💡 Sugestão'),
        ('MANUTENCAO', '🛠️ Manutenção'),
        ('MUDANCA', '🚚 Mudança'),
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
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE,
                                    verbose_name="Condomínio",
                                    related_name='solicitacoes')
    morador = models.ForeignKey(Morador, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Morador Solicitante")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name="Status Atual")
    arquivo = models.FileField(upload_to='solicitacoes/%Y/%m/', blank=True, verbose_name="Foto/Vídeo")
    
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Registrado por")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data do Registro")
    resposta_admin = models.TextField(blank=True, verbose_name="Resposta da Administração")

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.morador or 'Portaria'}"

    class Meta:
        verbose_name = "Solicitação / Ocorrência"
        verbose_name_plural = "Solicitações e Ocorrências"


class Aviso(models.Model):
    """Avisos e comunicados do condomínio para os moradores"""
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE,
                                    verbose_name="Condomínio", related_name='avisos')
    titulo = models.CharField(max_length=200, verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo")
    imagem = models.ImageField(upload_to='avisos/%Y/%m/', blank=True, verbose_name="Imagem")
    arquivo = models.FileField(upload_to='avisos/anexos/%Y/%m/', blank=True, verbose_name="Arquivo Anexo")
    data_publicacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Publicação")
    data_expiracao = models.DateField(null=True, blank=True, verbose_name="Data de Expiração")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")

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
        ('reserva', '📅 Reserva de Espaço'),
        ('ocorrencia', '🚨 Nova Ocorrência'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificacoes')
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


# ==========================================
# ÁREAS COMUNS E RESERVAS
# ==========================================

class AreaComum(models.Model):
    """Espaços reserváveis do condomínio"""
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE,
                                    related_name='areas_comuns', verbose_name="Condomínio")
    nome = models.CharField(max_length=100, verbose_name="Nome do Espaço")
    descricao = models.TextField(blank=True, verbose_name="Descrição / Regras de Uso")
    imagem = models.ImageField(upload_to='areas_comuns/', blank=True, verbose_name="Foto do Espaço")
    capacidade = models.PositiveIntegerField(help_text="Capacidade máxima de pessoas", verbose_name="Capacidade")
    horario_abertura = models.TimeField(verbose_name="Horário de Abertura")
    horario_fechamento = models.TimeField(verbose_name="Horário de Fechamento")
    ativo = models.BooleanField(default=True)
    taxa_reserva = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, 
        verbose_name="Taxa de Reserva (R$)",
        help_text="Valor cobrado automaticamente ao aprovar a reserva (0 = Grátis)"
    )

    def __str__(self):
        return f"{self.nome} — {self.condominio.nome}"

    class Meta:
        verbose_name = "Área Comum"
        verbose_name_plural = "Áreas Comuns"
        ordering = ['nome']


class Reserva(models.Model):
    """Reservas de áreas comuns pelos moradores"""
    STATUS_CHOICES = [
        ('PENDENTE', '🟡 Pendente'),
        ('APROVADA', '🟢 Aprovada'),
        ('RECUSADA', '🔴 Recusada'),
        ('CANCELADA', '⚫ Cancelada'),
    ]

    area = models.ForeignKey(AreaComum, on_delete=models.CASCADE,
                              related_name='reservas', verbose_name="Área Comum")
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE,
                                 related_name='reservas', verbose_name="Morador")
    data = models.DateField(verbose_name="Data da Reserva")
    horario_inicio = models.TimeField(verbose_name="Horário de Início")
    horario_fim = models.TimeField(verbose_name="Horário de Término")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE',
                               verbose_name="Status")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    motivo_recusa = models.TextField(blank=True, verbose_name="Motivo da Recusa")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data do Pedido")

    def __str__(self):
        return f"{self.area.nome} — {self.data} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-data', '-horario_inicio']

# ==========================================
# CHAT / MENSAGENS INTERNAS
# ==========================================

class Mensagem(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensagens_enviadas', verbose_name="Remetente")
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensagens_recebidas', verbose_name="Destinatário")
    conteudo = models.TextField(verbose_name="Memsagem")
    resposta_a = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='respostas', verbose_name="Em resposta a")
    lida = models.BooleanField(default=False, verbose_name="Lida?")
    data_envio = models.DateTimeField(auto_now_add=True, verbose_name="Enviada em")

    def __str__(self):
        return f"De {self.remetente} para {self.destinatario} - {self.data_envio.strftime('%d/%m %H:%M')}"

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['-data_envio']


# ==========================================
# OCORRÊNCIAS / LIVRO NEGRO
# ==========================================

class Ocorrencia(models.Model):
    STATUS_CHOICES = (
        ('REGISTRADA', 'Registrada'),
        ('EM_ANALISE', 'Em Análise'),
        ('RESOLVIDA', 'Resolvida')
    )
    
    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='ocorrencias')
    autor = models.ForeignKey(Morador, on_delete=models.CASCADE, related_name='ocorrencias_registradas', verbose_name="Autor da Ocorrência")
    infrator = models.CharField(max_length=200, blank=True, verbose_name="Possível Infrator/Unidade")
    descricao = models.TextField(verbose_name="Descrição da Ocorrência")
    foto = models.FileField(upload_to='ocorrencias/%Y/%m/', blank=True, null=True, verbose_name="Foto/Prova")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTRADA', verbose_name="Status")
    resposta_sindico = models.TextField(blank=True, verbose_name="Resposta do Síndico")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data do Registro")
    advertencia_emitida = models.BooleanField(default=False, verbose_name="Advertência Emitida")

    def __str__(self):
        return f"Ocorrência {self.id} - {self.condominio.nome}"

    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ['-data_registro']

# ==========================================
# WEB PUSH NOTIFICATIONS
# ==========================================

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
        return f"Push Sub de {self.usuario.username}"


# ==============================================================================
# CENTRAL DE DOCUMENTOS
# ==============================================================================

class DocumentoCondominio(models.Model):
    CATEGORIA_CHOICES = (
        ('CONVENCAO', 'Convenção'),
        ('REGIMENTO', 'Regimento Interno'),
        ('ATA', 'Ata de Assembleia'),
        ('FINANCEIRO', 'Relatório Financeiro'),
        ('OUTROS', 'Outros'),
    )

    condominio = models.ForeignKey(Condominio, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=200, verbose_name="Título do Documento")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='OUTROS', verbose_name="Categoria")
    arquivo = models.FileField(upload_to='documentos/%Y/%m/', verbose_name="Arquivo")
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name="Data de Upload")

    def __str__(self):
        return f"{self.titulo} — {self.condominio.nome}"

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-data_upload']

