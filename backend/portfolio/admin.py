from django.contrib import admin

# Register your models here.
from .models.holding import Holding

admin.site.register(Holding)

