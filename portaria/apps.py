from django.apps import AppConfig


class PortariaConfig(AppConfig):
    name = 'portaria'

    def ready(self):
        from django.contrib.auth.models import User
        from django.core.validators import RegexValidator

        # Substituir o validador do campo username para permitir espaços
        username_field = User._meta.get_field('username')
        username_field.validators = [
            RegexValidator(
                regex=r'^[\w.@+\- ]+$',
                message='Informe um nome de usuário válido. Pode conter letras, números, espaços e @/./+/-/_.',
            )
        ]
        username_field.help_text = 'Obrigatório. 150 caracteres ou menos. Letras, números, espaços e @/./+/-/_.'
