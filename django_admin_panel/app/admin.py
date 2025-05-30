from app.models import Category, Client, Order, OrderItem, Product
from django.contrib import admin


class ClientAdmin(admin.ModelAdmin):
    list_display = ("username", "telegram_id")
    search_fields = ("username", "telegram_id")


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    search_fields = ("name", "description")
    list_filter = ("category",)


admin.site.register(Client, ClientAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
