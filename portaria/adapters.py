from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter customizado do django-allauth.
    Garante que contas criadas via credenciais sociais (Google) 
    tenham o tipo_usuario definido como 'morador'.
    """
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.tipo_usuario = 'morador'
        user.save()
        return user
