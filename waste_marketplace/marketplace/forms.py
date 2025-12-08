from django import forms
from .models import UpcycledProduct, TrashItem

class UpcycledProductForm(forms.ModelForm):
    class Meta:
        model = UpcycledProduct
        # only expose the fields the artisan actually fills in:
        fields = [
            'product_name',
            'category',
            'description',
            'price',
            'stock_availability',
            'product_images',
            'location',
            'tags',
        ]

class TrashItemForm(forms.ModelForm):
    quantity = forms.IntegerField(label="Quantity (KGS)")

    class Meta:
        model = TrashItem
        fields = [
            'material_name',
            'category',
            'description',
            'price',
            'quantity',
            'images',
            'location',
            'condition',
            'trash_point',
            'tags',
        ]
