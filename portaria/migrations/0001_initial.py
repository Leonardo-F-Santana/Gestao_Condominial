



import django.contrib.auth.models

import django.contrib.auth.validators

import django.db.models.deletion

import django.utils.timezone

import uuid

from django.conf import settings

from django.db import migrations, models





class Migration(migrations.Migration):



    initial = True



    dependencies = [

        ('auth', '0013_alter_user_username'),

    ]



    operations = [

        migrations.CreateModel(

            name='Condominio',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('nome', models.CharField(max_length=100, verbose_name='Nome do Condomínio')),

                ('endereco', models.CharField(blank=True, max_length=200, verbose_name='Endereço')),

                ('cnpj', models.CharField(blank=True, max_length=18, verbose_name='CNPJ')),

                ('telefone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),

                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-mail')),

                ('logo', models.ImageField(blank=True, upload_to='condominios/', verbose_name='Logo')),

                ('codigo_convite', models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Código de Convite')),

                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro')),

                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),

            ],

            options={

                'verbose_name': 'Condomínio',

                'verbose_name_plural': 'Condomínios',

                'ordering': ['nome'],

            },

        ),

        migrations.CreateModel(

            name='CustomUser',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('password', models.CharField(max_length=128, verbose_name='password')),

                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),

                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),

                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),

                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),

                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),

                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),

                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),

                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),

                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),

                ('tipo_usuario', models.CharField(choices=[('sindico', 'Síndico'), ('porteiro', 'Porteiro'), ('morador', 'Morador'), ('admin', 'Administrador SaaS')], default='morador', max_length=20, verbose_name='Tipo de Usuário')),

                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),

                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),

                ('condominio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usuarios_cadastrados', to='portaria.condominio', verbose_name='Condomínio')),

            ],

            options={

                'verbose_name': 'user',

                'verbose_name_plural': 'users',

                'abstract': False,

            },

            managers=[

                ('objects', django.contrib.auth.models.UserManager()),

            ],

        ),

        migrations.CreateModel(

            name='Aviso',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('titulo', models.CharField(max_length=200, verbose_name='Título')),

                ('conteudo', models.TextField(verbose_name='Conteúdo')),

                ('imagem', models.ImageField(blank=True, upload_to='avisos/%Y/%m/', verbose_name='Imagem')),

                ('arquivo', models.FileField(blank=True, upload_to='avisos/anexos/%Y/%m/', verbose_name='Arquivo Anexo')),

                ('data_publicacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Publicação')),

                ('data_expiracao', models.DateField(blank=True, null=True, verbose_name='Data de Expiração')),

                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),

                ('criado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Publicado por')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avisos', to='portaria.condominio', verbose_name='Condomínio')),

            ],

            options={

                'verbose_name': 'Aviso',

                'verbose_name_plural': 'Avisos',

                'ordering': ['-data_publicacao'],

            },

        ),

        migrations.CreateModel(

            name='AreaComum',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('nome', models.CharField(max_length=100, verbose_name='Nome do Espaço')),

                ('descricao', models.TextField(blank=True, verbose_name='Descrição / Regras de Uso')),

                ('imagem', models.ImageField(blank=True, upload_to='areas_comuns/', verbose_name='Foto do Espaço')),

                ('capacidade', models.PositiveIntegerField(default=0, verbose_name='Capacidade (pessoas)')),

                ('horario_abertura', models.TimeField(default='08:00', verbose_name='Horário de Abertura')),

                ('horario_fechamento', models.TimeField(default='22:00', verbose_name='Horário de Fechamento')),

                ('ativo', models.BooleanField(default=True, verbose_name='Disponível para Reservas')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='areas_comuns', to='portaria.condominio', verbose_name='Condomínio')),

            ],

            options={

                'verbose_name': 'Área Comum',

                'verbose_name_plural': 'Áreas Comuns',

                'ordering': ['nome'],

            },

        ),

        migrations.CreateModel(

            name='Morador',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('nome', models.CharField(max_length=100, verbose_name='Nome Completo')),

                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-mail')),

                ('cpf', models.CharField(blank=True, max_length=14, verbose_name='CPF')),

                ('telefone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),

                ('bloco', models.CharField(blank=True, max_length=10, verbose_name='Bloco')),

                ('apartamento', models.CharField(max_length=10, verbose_name='Apartamento')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.condominio', verbose_name='Condomínio')),

                ('usuario', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='morador', to=settings.AUTH_USER_MODEL, verbose_name='Conta de Acesso')),

            ],

            options={

                'verbose_name': 'Morador',

                'verbose_name_plural': 'Moradores',

                'ordering': ['bloco', 'apartamento'],

            },

        ),

        migrations.CreateModel(

            name='Encomenda',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('data_chegada', models.DateTimeField(auto_now_add=True, verbose_name='Data de Chegada')),

                ('volume', models.CharField(max_length=50, verbose_name='Volume')),

                ('destinatario_alternativo', models.CharField(blank=True, max_length=100, verbose_name='Destinatário Externo (A/C)')),

                ('entregue', models.BooleanField(default=False, verbose_name='Entregue?')),

                ('data_entrega', models.DateTimeField(blank=True, null=True, verbose_name='Data da Entrega')),

                ('quem_retirou', models.CharField(blank=True, max_length=100, verbose_name='Quem retirou?')),

                ('documento_retirada', models.CharField(blank=True, max_length=50, verbose_name='Documento de quem retirou')),

                ('notificado', models.BooleanField(default=False, verbose_name='Morador foi avisado?')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='encomendas', to='portaria.condominio', verbose_name='Condomínio')),

                ('porteiro_cadastro', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cadastrou_encomenda', to=settings.AUTH_USER_MODEL)),

                ('porteiro_entrega', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entregou_encomenda', to=settings.AUTH_USER_MODEL)),

                ('morador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.morador', verbose_name='Morador')),

            ],

        ),

        migrations.CreateModel(

            name='Notificacao',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('tipo', models.CharField(choices=[('aviso', '📢 Novo Aviso'), ('solicitacao', '📋 Nova Solicitação'), ('resposta_solicitacao', '💬 Resposta de Solicitação'), ('reserva', '📅 Reserva de Espaço')], max_length=30)),

                ('mensagem', models.CharField(max_length=200)),

                ('link', models.CharField(blank=True, max_length=200)),

                ('lida', models.BooleanField(default=False)),

                ('data_criacao', models.DateTimeField(auto_now_add=True)),

                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to=settings.AUTH_USER_MODEL)),

            ],

            options={

                'verbose_name': 'Notificação',

                'verbose_name_plural': 'Notificações',

                'ordering': ['-data_criacao'],

            },

        ),

        migrations.CreateModel(

            name='Porteiro',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('nome', models.CharField(max_length=100, verbose_name='Nome Completo')),

                ('cargo', models.CharField(default='Porteiro', help_text='Ex: Porteiro, Zelador, Segurança', max_length=50, verbose_name='Cargo')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='porteiros', to='portaria.condominio', verbose_name='Condomínio')),

                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='porteiro_perfil', to=settings.AUTH_USER_MODEL)),

            ],

            options={

                'verbose_name': 'Porteiro / Acesso',

                'verbose_name_plural': 'Porteiros e Acessos',

            },

        ),

        migrations.CreateModel(

            name='Reserva',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('data', models.DateField(verbose_name='Data da Reserva')),

                ('horario_inicio', models.TimeField(verbose_name='Horário de Início')),

                ('horario_fim', models.TimeField(verbose_name='Horário de Término')),

                ('status', models.CharField(choices=[('PENDENTE', '🟡 Pendente'), ('APROVADA', '🟢 Aprovada'), ('RECUSADA', '🔴 Recusada'), ('CANCELADA', '⚫ Cancelada')], default='PENDENTE', max_length=20, verbose_name='Status')),

                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),

                ('motivo_recusa', models.TextField(blank=True, verbose_name='Motivo da Recusa')),

                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data do Pedido')),

                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservas', to='portaria.areacomum', verbose_name='Área Comum')),

                ('morador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservas', to='portaria.morador', verbose_name='Morador')),

            ],

            options={

                'verbose_name': 'Reserva',

                'verbose_name_plural': 'Reservas',

                'ordering': ['-data', '-horario_inicio'],

            },

        ),

        migrations.CreateModel(

            name='Sindico',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('nome', models.CharField(max_length=100, verbose_name='Nome Completo')),

                ('telefone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sindicos_perfil', to='portaria.condominio', verbose_name='Condomínio')),

                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sindico', to=settings.AUTH_USER_MODEL)),

            ],

            options={

                'verbose_name': 'Síndico',

                'verbose_name_plural': 'Síndicos',

            },

        ),

        migrations.CreateModel(

            name='Solicitacao',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('tipo', models.CharField(choices=[('RECLAMACAO', '📢 Reclamação'), ('MANUTENCAO', '🛠️ Manutenção'), ('MUDANCA', '🚚 Mudança'), ('OUTRO', '📝 Outro')], max_length=20, verbose_name='Tipo de Solicitação')),

                ('descricao', models.TextField(verbose_name='Descrição do Pedido')),

                ('status', models.CharField(choices=[('PENDENTE', '🟡 Pendente'), ('EM_ANDAMENTO', '🔵 Em Andamento'), ('CONCLUIDO', '🟢 Concluído'), ('CANCELADO', '🔴 Cancelado')], default='PENDENTE', max_length=20, verbose_name='Status Atual')),

                ('arquivo', models.FileField(blank=True, upload_to='solicitacoes/%Y/%m/', verbose_name='Foto/Vídeo')),

                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data do Registro')),

                ('resposta_admin', models.TextField(blank=True, verbose_name='Resposta da Administração')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes', to='portaria.condominio', verbose_name='Condomínio')),

                ('criado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),

                ('morador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='portaria.morador', verbose_name='Morador Solicitante')),

            ],

            options={

                'verbose_name': 'Solicitação / Ocorrência',

                'verbose_name_plural': 'Solicitações e Ocorrências',

            },

        ),

        migrations.CreateModel(

            name='Visitante',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('nome_completo', models.CharField(max_length=100, verbose_name='Nome Completo')),

                ('cpf', models.CharField(blank=True, max_length=14, null=True, verbose_name='CPF')),

                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')),

                ('numero_casa', models.CharField(blank=True, max_length=10, verbose_name='Número da Casa/Apto (Antigo)')),

                ('placa_veiculo', models.CharField(blank=True, max_length=20, verbose_name='Placa do Veículo')),

                ('horario_chegada', models.DateTimeField(auto_now_add=True, verbose_name='Horário de Chegada')),

                ('horario_saida', models.DateTimeField(blank=True, null=True, verbose_name='Horário de Saída')),

                ('quem_autorizou', models.CharField(blank=True, max_length=100, verbose_name='Quem Autorizou?')),

                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visitantes', to='portaria.condominio', verbose_name='Condomínio')),

                ('morador_responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='portaria.morador', verbose_name='Morador Responsável')),

                ('registrado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Porteiro Responsável')),

            ],

        ),

    ]

