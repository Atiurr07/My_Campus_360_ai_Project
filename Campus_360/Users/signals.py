from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

@receiver(social_account_added)
def redirect_to_role_selection(request, sociallogin, **kwargs):
    request.session['new_social_user'] = True