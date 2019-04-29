from collections import OrderedDict
from datetime import timedelta
import json

from braces.views import JSONResponseMixin, AjaxResponseMixin
from django.contrib import messages
from django.core.serializers import serialize
from django.db.models import Sum, Case, When, IntegerField, Count, F, Q
from django.db.models.functions import Coalesce
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.shortcuts import render

from test_products_task.common.mixins import ActiveTabMixin
from test_products_task.common.utils import get_ip_from_request
from test_products_task.products.forms import LikeForm
from test_products_task.products.models import Category, Product, Like, Comment


class CategoryListView(ActiveTabMixin, ListView):
    model = Category
    active_tab = 'category_list'

    def get_ordered_grade_info(self):
        return []

    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs)
        context['grade_info'] = self.get_ordered_grade_info()
        return context

    def get(self, request, *args, **kwargs):
        categories_list = []
        categories = json.loads(serialize('json', Category.objects.all()))
        print(categories)
        for i in categories:
            number_filt = Product.objects.filter(category__name=i['fields']['name']).count()
            el = {'name': i['fields']['name'], 'number': number_filt, 'get_absolute_url': 'http://localhost:8000/products/'+ i['fields']['slug']}
            categories_list.append(el)
        return render(request, 'products/category_list.html', {'category_list': categories_list})


class CategoryDetailView(DetailView):
    model = Category
    slug_url_kwarg = 'category_slug'
    PARAM_FOLLOWING = 'following'
    PARAM_PRICE_FROM = 'price_from'
    PARAM_PRICE_TO = 'price_to'


class ProductDetailView(DetailView):
    model = Product
    slug_url_kwarg = 'product_slug'
    category = None

    def get(self, request, *args, **kwargs):
        category_slug = kwargs['category_slug']
        try:
            self.category = Category.objects.get(slug=category_slug)
            product_slug = request.path.split('/')[4]
            #self.comment = Category.objects.filter(product_slug=product_slug)
        except Category.DoesNotExist:
            raise Http404
        return super().get(request, *args, **kwargs)


class LikeToggleView(AjaxResponseMixin, JSONResponseMixin, FormView):
    http_method_names = ('post', )
    form_class = LikeForm
    product = None

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        product_id = kwargs['product_pk']
        try:
            self.product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        like = Like()
        if request.user.is_authenticated:
            like.user = request.user
        else:
            like.ip = get_ip_from_request(request)
        product_id = request.path.split('/')[2]
        like.product =  Product.objects.get(id=product_id)
        try:
            like.save()
        except IntegrityError:
            messages.warning(request, 'You have already liked this product')
            return HttpResponse('#')

        return HttpResponseRedirect('#')


class CommentToggleView(AjaxResponseMixin, JSONResponseMixin, FormView, Comment):
    model = Comment
    active_tab = 'product_detail'

    def get (request, pk):
        new = get_object_or_404(Product, pk)
        comment = model.objects.filter(new=pk)
        print(comment)
        return render(request, 'products/product_detail.html', {'new': new, 'comments': comment})

class AddToCartView(AjaxResponseMixin, JSONResponseMixin, FormView):
    http_method_names = ('post',)
    success_url = reverse_lazy('products:cart')

    def post(self, request, *args, **kwargs):
        raise NotImplementedError


class CartView(ActiveTabMixin, TemplateView):
    active_tab = 'cart'
    template_name = 'products/cart.html'

