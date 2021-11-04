
from django.forms import ModelChoiceField, ModelForm
from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *


class PictureAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            """<spam style="color:blue; font-size:13px">Imaginile cu rizoluția mai mică de {}px sau<br>mai mare de {}px vor fi automat redimensionate</spam>""".format(
            Product.Min_Resolution, Product.Max_Resolution
            )
        )


class ClothesAdmin(admin.ModelAdmin):

    form = PictureAdminForm
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Clothes'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ClothesCategoryChoiceField(forms.ModelChoiceField):
    category = forms.ModelChoiceField(Category.objects.all())


class ShoesAdmin(admin.ModelAdmin):

    form = PictureAdminForm
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Shoes'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ShoesCategoryChoiceField(forms.ModelChoiceField):
    category = forms.ModelChoiceField(Category.objects.all())



class AccessoriesAdmin(admin.ModelAdmin):

    form = PictureAdminForm
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Accessories'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AccessoriesCategoryChoiceField(forms.ModelChoiceField):
    category = forms.ModelChoiceField(Category.objects.all())

admin.site.register(Category)
admin.site.register(Clothes, ClothesAdmin)
admin.site.register(Shoes, ShoesAdmin)
admin.site.register(Accessories, AccessoriesAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)


