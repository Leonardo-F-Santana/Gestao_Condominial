from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    pass

    def save_user(self, request, sociallogin, form=None):

        user = super().save_user(request, sociallogin, form)

        user.tipo_usuario = 'morador'

        user.save()

        return user

