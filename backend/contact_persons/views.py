from rest_framework import viewsets, permissions
from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(active=True)

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()
        # также делаем неактивной всю контактную информацию
        instance.contact_info.update(active=False)
