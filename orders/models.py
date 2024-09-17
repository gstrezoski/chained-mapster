import json

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class OrganizationalUnit(models.Model):

    gl_id = models.CharField(
        _("Global Id"), max_length=100, blank=True, null=False, default=""
    )

    ou_id = models.PositiveBigIntegerField(
        _("Organization Unit ID"), blank=True, null=True
    )

    add_id = models.PositiveBigIntegerField(_("Address ID"), blank=True, null=True)

    client_name = models.CharField(
        _("Client Name"), max_length=255, blank=True, null=True, default=""
    )

    name = models.CharField(
        _("address"), max_length=255, blank=True, null=False, default=""
    )

    address = models.CharField(
        _("address"), max_length=255, blank=True, null=False, default=""
    )

    house_number = models.CharField(
        _("house number"),
        max_length=255,
        blank=True,
        null=False,
        default="",
    )

    house_number_extension = models.CharField(
        _("house number extension"), max_length=255, blank=True, null=False, default=""
    )

    city = models.CharField(
        _("city"), max_length=255, blank=True, null=False, default=""
    )

    post_code = models.CharField(
        _("zip / post code"), max_length=100, blank=True, null=False, default=""
    )
    country = CountryField(_("country"), blank=True, null=False, default="")

    latitude = models.FloatField(
        _("Latitude"), blank=True, null=True, default=41.9172025
    )

    longitude = models.FloatField(
        _("Longitude"), blank=True, null=True, default=22.4067487
    )

    def __str__(self):
        return "{}:{}".format(self.gl_id, self.name)

    def to_coords(self):
        return json.dumps(
            {"lon": self.longitude, "lat": self.latitude, "name": self.name}
        )

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
