from PIL import Image
import sys
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils import timezone


User = get_user_model()

def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})



class MinResException(Exception):
    pass

class MaxResException(Exception):
    pass
class MaxSizeException(Exception):
    pass


class LatestProductsManager:
    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products



class LatestProducts:
    objects = LatestProductsManager()



class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Haine' : 'clothes__count',
        'Încălțăminte' : 'shoes__count',
        'Accesorii' : 'accessories__count'

    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('clothes', 'shoes', 'accessories')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data



class Category(models.Model):

    objects = CategoryManager()
    name = models.CharField(max_length=255, verbose_name='Listă categorii')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    Min_Resolution = 400
    Max_Resolution = 800
    Max_Image_Size = 3145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Categoria', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Produs')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Imagine', null=True)
    description = models.TextField(verbose_name='Detalii', null=True)
    price = models.IntegerField(verbose_name='Preț')

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()

    def save(self, *args, **kwargs):

        image = self.image
        img = Image.open(image)
        new_img = img.convert('RGB')

        w, h = new_img.size
        max_scale = 800 / max(h, w)
        min_scale = 400 / max(h, w)
        Max_Resolution = 800
        Min_Resolution = 400
        resized_new_img = new_img

        if h >= Max_Resolution:
            resized_new_img = new_img.resize((int(w * max_scale), int(h * max_scale)), Image.ANTIALIAS)
        if h <= Min_Resolution:
            resized_new_img = new_img.resize((int(w * min_scale), int(h * min_scale)), Image.ANTIALIAS)
        else:
            None

        filestream = BytesIO()
        resized_new_img.save(filestream, 'JPEG', quality=90)
        filestream.seek(0)
        name = '{}.{}'.format(*self.image.name.split('.'))
        print(self.image.name, name)
        self.image = InMemoryUploadedFile(
            filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)


class Clothes(Product):

    model = models.CharField(max_length=255, verbose_name='Model')
    gender = models.CharField(max_length=255, verbose_name='Gen')
    season = models.CharField(max_length=255, verbose_name='Sezon')
    style = models.CharField(max_length=255, verbose_name='Stil')
    size = models.CharField(max_length=5, verbose_name='Mărime')
    color = models.CharField(max_length=255, verbose_name='Culoare')

    def __str__(self):
            return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
            return get_product_url(self, 'product_detail')



class Shoes(Product):

    model = models.CharField(max_length=20, verbose_name='Model')
    gender = models.CharField(max_length=20, verbose_name='Gen')
    season = models.CharField(max_length=20, verbose_name='Sezon')
    size = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='Mărime')
    color = models.CharField(max_length=255, verbose_name='Culoare')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')



class Accessories(Product):

    gender = models.CharField(max_length=20, verbose_name='Gen')
    color = models.CharField(max_length=255, verbose_name='Culoare')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CartProduct(models.Model):

    user = models.ForeignKey('Customer', verbose_name='Client', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Comanda dvs.', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Preț final')

    def __str__(self):
        return "Produs: {}".format(self.content_object.title)

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)



class Cart(models.Model):

    owner = models.ForeignKey('Customer', null=True, verbose_name='Client', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='În total')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='Client', on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name='Numărul de telefon', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Adresa dvs.', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Comenzile mele', related_name='related_order')

    def __str__(self):
        return "Client: {} {}".format(self.user.first_name, self.user.last_name)


class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Comandă nouă'),
        (STATUS_IN_PROGRESS, 'Comanda în procesare'),
        (STATUS_READY, 'Comanda în livrare'),
        (STATUS_COMPLETED, 'Comanda executată')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Ridicare personală'),
        (BUYING_TYPE_DELIVERY, 'Livrare')
    )

    customer = models.ForeignKey(Customer, verbose_name='Cumpărător', related_name='related_orders', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Prenumele')
    last_name = models.CharField(max_length=255, verbose_name='Numele')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    cart = models.ForeignKey(Cart, verbose_name='Comanda', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Adresa', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Statut comandă',
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Selectați',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )
    created_at = models.DateTimeField(auto_now=True, verbose_name='Data comenzii')
    order_date = models.DateField(verbose_name='Data livrării', default=timezone.now)

    def __str__(self):
        return str(self.id)

















