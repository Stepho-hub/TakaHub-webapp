from django import forms
from django.core.validators import EmailValidator, RegexValidator
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

class ContactForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Your full name'}),
        label='Full Name'
    )
    email = forms.EmailField(
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={'placeholder': 'your.email@example.com'}),
        label='Email Address'
    )
    phone = forms.CharField(
        required=False,
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        widget=forms.TextInput(attrs={'placeholder': '+254712345678'}),
        label='Phone Number (Optional)'
    )
    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Subject of your enquiry'}),
        label='Subject'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Your message here...', 'rows': 5}),
        label='Message'
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic validation using regex
            import re
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                raise forms.ValidationError("Please enter a valid phone number in the format +254701456780.")
        return phone
