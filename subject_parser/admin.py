from django.contrib import admin
from .models import Customer, Contract, PhoneNumber

# Register your models here.

admin.site.register(Customer)
admin.site.register(Contract)
admin.site.register(PhoneNumber)