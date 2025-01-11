from django.contrib import admin
from .models import Customer, Contract, PhoneNumber

# Register your models here.

class CustomerAdmin(admin.ModelAdmin):
    search_fields = ['bin']

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Contract)
admin.site.register(PhoneNumber)