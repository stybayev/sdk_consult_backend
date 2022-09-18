from django.db import models


class ContactsForCommunication(models.Model):
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='images/user_pics/', blank=True, null=True)

    def __str__(self):
        return f'{self.first_name} - {self.last_name}'

    class Meta:
        verbose_name = "Контакты"
        verbose_name_plural = "01 Контакты"

    @property
    def contact_info(self):
        contact = dict()
        contact['phone_number'] = self.phone_number
        contact['first_name'] = self.first_name
        contact['last_name'] = self.last_name
        if self.image:
            contact['image'] = self.image.url
        return contact
