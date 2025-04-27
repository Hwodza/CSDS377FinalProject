from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Lampi, SenderDevice, DeviceData, DiskStats, CpuLoad, \
NetworkStats
from django.conf import settings
from lampi.forms import AddLampiForm, AddSenderForm
from mixpanel import Mixpanel


class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'lampi/index.html'

    def get_queryset(self):
        results = Lampi.objects.filter(user=self.request.user)
        return results

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['lampi_devices'] = Lampi.objects.filter(user=self.request.user)
        context['sender_devices'] = SenderDevice.objects.filter(
            user=self.request.user)
        context['MIXPANEL_TOKEN'] = settings.MIXPANEL_TOKEN
        return context


class DetailView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'lampi/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['device'] = get_object_or_404(
            Lampi, pk=kwargs['device_id'], user=self.request.user)
        context['MIXPANEL_TOKEN'] = settings.MIXPANEL_TOKEN
        return context


class AddLampiView(LoginRequiredMixin, generic.FormView):
    template_name = 'lampi/addlampi.html'
    form_class = AddLampiForm
    success_url = '/lampi'

    def get_context_data(self, **kwargs):
        context = super(AddLampiView, self).get_context_data(**kwargs)
        context['MIXPANEL_TOKEN'] = settings.MIXPANEL_TOKEN
        return context

    def form_valid(self, form):
        device = form.cleaned_data['device']
        device.associate_and_publish_associated_msg(self.request.user)

        mp = Mixpanel(settings.MIXPANEL_TOKEN)
        mp.track(device.user.username, "LAMPI Activation",
                 {'event_type': 'activations', 'interface': 'web',
                  'device_id': device.device_id})

        return super(AddLampiView, self).form_valid(form)


class AddSenderView(LoginRequiredMixin, generic.FormView):
    template_name = 'lampi/addsender.html'
    form_class = AddSenderForm
    success_url = '/lampi'

    def get_context_data(self, **kwargs):
        context = super(AddSenderView, self).get_context_data(**kwargs)
        context['MIXPANEL_TOKEN'] = settings.MIXPANEL_TOKEN
        return context

    def form_valid(self, form):
        device = form.cleaned_data['device']
        device.associate_and_publish_associated_msg(self.request.user)

        return super(AddSenderView, self).form_valid(form)


# class SenderDetailView(LoginRequiredMixin, generic.TemplateView):
#     template_name = 'lampi/sender_detail.html'

#     def get_context_data(self, **kwargs):
#         context = super(SenderDetailView, self).get_context_data(**kwargs)
#         context['device'] = get_object_or_404(
#             SenderDevice, pk=kwargs['device_id'], user=self.request.user)
#         context['MIXPANEL_TOKEN'] = settings.MIXPANEL_TOKEN
#         return context

class SenderDetailView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'lampi/sender_detail.html'

    def get_context_data(self, **kwargs):
        context = super(SenderDetailView, self).get_context_data(**kwargs)
        device = get_object_or_404(
            SenderDevice, pk=kwargs['device_id'], user=self.request.user)

        # Get the latest data point
        current_stats = device.data_points.order_by('-timestamp').first()

        # Get data for charts (last 24 hours)
        time_threshold = timezone.now() - timedelta(hours=24)
        chart_data = device.data_points.filter(
            timestamp__gte=time_threshold
        ).order_by('timestamp')

        # Prepare chart data
        chart_context = {
            'timestamps': [data.timestamp.isoformat() for data in chart_data],
            'memory_data': {
                'free': [data.kbmemfree for data in chart_data],
                'used': [data.kbmemused for data in chart_data],
                'percent': [data.memused_percent for data in chart_data],
            },
            'cpu_temp': [data.cputemp for data in chart_data],
            'disk_stats': [],
            'cpu_loads': [],
            'network_stats': []
        }

        # Add related data if current_stats exists
        if current_stats:
            chart_context['disk_stats'] = [
                {'device': stat.device, 'wait': stat.wait, 'util': stat.util}
                for stat in current_stats.disk_stats.all()
            ]
            chart_context['cpu_loads'] = [
                {'core': load.core, 'load': load.load}
                for load in current_stats.cpu_loads.all()
            ]
            chart_context['network_stats'] = [
                {'iface': stat.iface, 'rx_kb': stat.rx_kb, 'tx_kb': stat.tx_kb}
                for stat in current_stats.network_stats.all()
            ]

        context.update({
            'device': device,
            'current_stats': current_stats,
            'chart_data': chart_context,
            'MIXPANEL_TOKEN': settings.MIXPANEL_TOKEN,
        })

        return context
