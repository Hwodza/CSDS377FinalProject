from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView
from .models import Lampi

# Create your views here.


class DetailView(LoginRequiredMixin, TemplateView):
    template_name = 'lampi/detail.html'

    def get_context_data(self, **kwargs):
        # call super class method
        context = super(DetailView, self).get_context_data(**kwargs)
        # get the device object or raise/return an HTTP 404
        #   store device object reference in the context object at a key
        #   of "device"
        context['device'] = get_object_or_404(
            Lampi, pk=kwargs['device_id'], user=self.request.user)
        # return the context object
        return context


class IndexView(LoginRequiredMixin, ListView):
    template_name = 'lampi/index.html'

    def get_queryset(self):
        return Lampi.objects.filter(user=self.request.user)
