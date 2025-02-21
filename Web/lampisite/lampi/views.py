from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from .models import Lampi
from django.contrib.auth.models import User

# Create your views here.

class DetailView(LoginRequiredMixin, TemplateView):
    template_name = 'lampi/detail.html'

class IndexView(LoginRequiredMixin, ListView):
    template_name = 'lampi/index.html'

    def get_queryset(self):
        return Lampi.objects.filter(user=self.request.user)
