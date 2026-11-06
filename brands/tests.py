from django.test import TestCase
from django.urls import reverse

from bikes.models import Bike, Brand, Category


class BrandsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(name='Test Motors')
        cls.category = Category.objects.create(name='Test Category')
        Bike.objects.create(
            brand=cls.brand,
            category=cls.category,
            model_name='Test 100',
            price=100000,
            mileage=50,
            engine_cc=100,
            power_bhp=10,
            is_active=True,
        )

    def test_brand_list_loads(self):
        response = self.client.get(reverse('brands:brand_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Motors')
        self.assertContains(response, '1 models')

    def test_brand_detail_loads(self):
        response = self.client.get(
            reverse('brands:brand_detail', args=['test-motors'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test 100')

    def test_unknown_brand_returns_404(self):
        response = self.client.get('/brands/does-not-exist/')
        self.assertEqual(response.status_code, 404)
