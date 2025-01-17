from django.db import models


class Customer(models.Model):
    customer_number = models.CharField(verbose_name="Номер участника", max_length=255)
    customer_name = models.CharField(verbose_name="Название", max_length=518)
    bin = models.CharField(verbose_name='БИН', max_length=255)

    def __str__(self):
        return self.bin

    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'


class Contract(models.Model):
    file_url = models.URLField(verbose_name="Ссылка на договор")
    file_path = models.FileField(verbose_name="Файл", upload_to='contracts/')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contracts")

    def __str__(self):
        return self.customer.bin

    class Meta:
        verbose_name = 'Договор'
        verbose_name_plural = 'Договора'


class PhoneNumber(models.Model):
    number = models.CharField(verbose_name="Номер телефона", max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="phone_numbers")

    def __str__(self):
        return f"{self.number} - {self.customer}"

    class Meta:
        verbose_name = 'Номер телефона'
        verbose_name_plural = 'Номера телефонов'

# class File(models.Model):
#     file = models.FileField(verbose_name="Файл")
#     customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="files")
