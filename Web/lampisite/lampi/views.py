from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.

class DetailView(LoginRequiredMixin, TemplateView):
    template_name = 'lampi/detail.html'
