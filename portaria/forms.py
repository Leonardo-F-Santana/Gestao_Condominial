from django import forms

from django.contrib.auth.models import Permission

from unfold.forms import UserChangeForm as BaseUserChangeForm, UserCreationForm as BaseUserCreationForm

from django.contrib.auth import get_user_model

User = get_user_model()

from django.core.validators import RegexValidator

def validate_email_domain(email):

    if not email:

        return email

    domain = email.split('@')[-1].lower() if '@' in email else ''

    valid_tlds = ['.com', '.com.br', '.net', '.org', '.edu', '.gov', '.mil', '.int', '.io', '.coop']

    if not any(domain.endswith(tld) for tld in valid_tlds) or domain.startswith('.') or domain.endswith('.co') or domain.endswith('.con'):

        raise forms.ValidationError("Informe um e-mail com um domínio válido (ex: .com, .com.br, .net, .org).")

    return email

username_validator = RegexValidator(

    regex=r'^[\w.@+\- ]+$',

    message='Informe um nome de usuário válido. Pode conter letras, números, espaços e @/./+/-/_.',

)

class PermissionToggleWidget(forms.Widget):

    pass

    template_name = 'admin/widgets/permission_toggles.html'

    MODEL_LABELS = {

        'portaria.condominio': {'label': 'Condomínio', 'icon': 'apartment'},

        'portaria.sindico': {'label': 'Síndico', 'icon': 'admin_panel_settings'},

        'portaria.morador': {'label': 'Moradores', 'icon': 'groups'},

        'portaria.visitante': {'label': 'Visitantes', 'icon': 'badge'},

        'portaria.encomenda': {'label': 'Encomendas', 'icon': 'package_2'},

        'portaria.solicitacao': {'label': 'Solicitações', 'icon': 'assignment'},

        'portaria.aviso': {'label': 'Avisos', 'icon': 'campaign'},

        'portaria.notificacao': {'label': 'Notificações', 'icon': 'notifications'},

        'auth.user': {'label': 'Usuários', 'icon': 'person'},

        'auth.group': {'label': 'Grupos', 'icon': 'group'},

    }

    ACTION_LABELS = {

        'view': {'label': 'Visualizar', 'order': 0},

        'add': {'label': 'Adicionar', 'order': 1},

        'change': {'label': 'Editar', 'order': 2},

        'delete': {'label': 'Excluir', 'order': 3},

    }

    def get_context(self, name, value, attrs):

        context = super().get_context(name, value, attrs)

        selected_ids = set()

        if value:

            for v in value:

                try:

                    selected_ids.add(int(v))

                except (ValueError, TypeError):

                    if hasattr(v, 'pk'):

                        selected_ids.add(v.pk)

        relevant_apps = ['portaria', 'auth']

        permissions = (

            Permission.objects

            .filter(content_type__app_label__in=relevant_apps)

            .select_related('content_type')

            .order_by('content_type__app_label', 'content_type__model', 'codename')

        )

        grouped = {}

        shown_ids = set()

        for perm in permissions:

            ct = perm.content_type

            model_key = f"{ct.app_label}.{ct.model}"

            if model_key not in self.MODEL_LABELS:

                continue

            if model_key not in grouped:

                info = self.MODEL_LABELS[model_key]

                grouped[model_key] = {

                    'label': info['label'],

                    'icon': info['icon'],

                    'actions': [],

                }

            action = perm.codename.split('_', 1)[0]

            action_info = self.ACTION_LABELS.get(

                action, {'label': perm.name, 'order': 9}

            )

            grouped[model_key]['actions'].append({

                'id': perm.id,

                'label': action_info['label'],

                'order': action_info['order'],

                'checked': perm.id in selected_ids,

            })

            shown_ids.add(perm.id)

        for model_key in grouped:

            grouped[model_key]['actions'].sort(key=lambda a: a['order'])

        other_selected = [

            {'id': pid} for pid in (selected_ids - shown_ids)

        ]

        context['grouped_permissions'] = grouped

        context['other_selected'] = other_selected

        context['field_name'] = name

        return context

    def value_from_datadict(self, data, files, name):

        return data.getlist(name)

    def value_omitted_from_data(self, data, files, name):

        return False

class CustomUserChangeForm(BaseUserChangeForm):

    pass

    username = forms.CharField(

        max_length=150,

        validators=[username_validator],

        help_text='Obrigatório. 150 caracteres ou menos. Letras, números, espaços e @/./+/-/_.',

        label='Nome de usuário',

    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if 'user_permissions' in self.fields:

            self.fields['user_permissions'].widget = PermissionToggleWidget()

            self.fields['user_permissions'].help_text = (

                'Ative ou desative as permissões específicas deste usuário.'

            )

    class Meta(BaseUserChangeForm.Meta):

        model = User

        fields = '__all__'

    def clean(self):

        cleaned_data = super().clean()

        tipo_usuario = cleaned_data.get("tipo_usuario")

        condominios = cleaned_data.get("condominios")

        is_superuser = cleaned_data.get("is_superuser", False)

        if not is_superuser and tipo_usuario in ['sindico', 'porteiro', 'morador'] and not condominios:

            self.add_error('condominios', 'Pelo menos um condomínio é obrigatório para este tipo de usuário.')

        return cleaned_data

class CustomUserCreationForm(BaseUserCreationForm):

    pass

    username = forms.CharField(

        max_length=150,

        validators=[username_validator],

        help_text='Obrigatório. 150 caracteres ou menos. Letras, números, espaços e @/./+/-/_.',

        label='Nome de usuário',

    )

    class Meta(BaseUserCreationForm.Meta):

        model = User

        fields = ('username', 'tipo_usuario', 'condominios')

    def clean(self):

        cleaned_data = super().clean()

        tipo_usuario = cleaned_data.get("tipo_usuario")

        condominios = cleaned_data.get("condominios")

        if tipo_usuario in ['sindico', 'porteiro', 'morador'] and not condominios:

            self.add_error('condominios', 'Pelo menos um condomínio é obrigatório para este tipo de usuário.')

        return cleaned_data

from .models import Morador, Sindico, Porteiro

class MoradorPerfilForm(forms.ModelForm):

    username = forms.CharField(label="Usuário (Login)", required=True)

    email = forms.EmailField(label="E-mail", required=False)

    class Meta:

        model = Morador

        fields = ['telefone', 'apartamento', 'bloco']

        widgets = {

            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),

            'apartamento': forms.TextInput(attrs={'class': 'form-control'}),

            'bloco': forms.TextInput(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if self.user:

            self.fields['username'].initial = self.user.username

            self.fields['username'].widget.attrs.update({'class': 'form-control'})

            self.fields['email'].initial = self.user.email

            self.fields['email'].widget.attrs.update({'class': 'form-control'})

        self.fields['apartamento'].disabled = True

        self.fields['bloco'].disabled = True

    def clean_email(self):

        email = self.cleaned_data.get('email')

        return validate_email_domain(email)

    def save(self, commit=True):

        morador = super().save(commit=False)

        if self.user:

            self.user.username = self.cleaned_data['username']

            self.user.email = self.cleaned_data['email']

            morador.email = self.cleaned_data['email']

            if commit:

                self.user.save()

        if commit:

            morador.save()

        return morador

class SindicoPerfilForm(forms.ModelForm):

    username = forms.CharField(label="Usuário (Login)", required=True)

    email = forms.EmailField(label="E-mail", required=False)

    receber_push = forms.BooleanField(label="Receber Notificações Push", required=False)

    class Meta:

        model = Sindico

        fields = ['telefone']

        widgets = {

            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),

        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if self.user:

            self.fields['username'].initial = self.user.username

            self.fields['username'].widget.attrs.update({'class': 'form-control'})

            self.fields['email'].initial = self.user.email

            self.fields['email'].widget.attrs.update({'class': 'form-control'})

            self.fields['receber_push'].initial = self.user.receber_push

    def clean_email(self):

        email = self.cleaned_data.get('email')

        return validate_email_domain(email)

    def save(self, commit=True):

        sindico = super().save(commit=False)

        if self.user:

            self.user.username = self.cleaned_data['username']

            self.user.email = self.cleaned_data['email']

            self.user.receber_push = self.cleaned_data['receber_push']

            if commit:

                self.user.save()

        if commit:

            sindico.save()

        return sindico

class PorteiroForm(forms.ModelForm):

    username = forms.CharField(label="Usuário (Login)", required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: login.porteiro'}))

    password = forms.CharField(label="Senha", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 6 caracteres'}))

    class Meta:

        model = Porteiro

        fields = ['nome']

        widgets = {

            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),

        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if self.user:

            self.fields['username'].initial = self.user.username

            self.fields['password'].required = False

    def save(self, commit=True):

        porteiro = super().save(commit=False)

        return porteiro

