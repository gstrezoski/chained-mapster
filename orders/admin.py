from django.contrib import admin

from orders.models import OrganizationalUnit


# Register your models here.
@admin.register(OrganizationalUnit)
class OrganizationalUnitAdmin(admin.ModelAdmin):
    pass
