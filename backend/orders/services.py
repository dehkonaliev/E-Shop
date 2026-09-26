from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.models import Product

from .models import Cart, CartItem, Order, OrderItem


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def add_to_cart(user, product_id, quantity):
    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(user=user)
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
        product = (
            Product.objects.select_for_update()
            .filter(pk=product_id)
            .first()
        )
        if product is None:
            raise ValidationError({"product_id": "Product not found."})
        item = (
            CartItem.objects.select_for_update()
            .filter(cart=cart, product=product)
            .first()
        )
        new_quantity = quantity if item is None else item.quantity + quantity
        if new_quantity > product.stock:
            raise ValidationError(
                {"quantity": "Requested quantity exceeds available stock."}
            )
        if item is None:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
            )
        else:
            item.quantity = new_quantity
            item.save(update_fields=["quantity", "updated_at"])
    return cart


def remove_from_cart(user, product_id):
    cart = get_or_create_cart(user)
    deleted, _ = CartItem.objects.filter(
        cart=cart,
        product_id=product_id,
    ).delete()
    if not deleted:
        raise ValidationError({"product_id": "Product is not in the cart."})
    return cart


def checkout_cart(user, shipping_address):
    with transaction.atomic():
        cart = (
            Cart.objects.select_for_update()
            .filter(user=user)
            .first()
        )
        if cart is None:
            raise ValidationError({"detail": "Cart is empty."})
        cart_items = list(
            CartItem.objects.select_for_update()
            .filter(cart=cart)
            .select_related("product")
            .order_by("product_id")
        )
        if not cart_items:
            raise ValidationError({"detail": "Cart is empty."})
        product_ids = [item.product_id for item in cart_items]
        products = {
            product.pk: product
            for product in Product.objects.select_for_update()
            .filter(pk__in=product_ids)
            .order_by("pk")
        }
        for item in cart_items:
            product = products.get(item.product_id)
            if product is None:
                raise ValidationError(
                    {"detail": "A product in the cart no longer exists."}
                )
            if product.stock < item.quantity:
                raise ValidationError(
                    {
                        "product_id": product.pk,
                        "stock": f"Only {product.stock} units are available.",
                    }
                )
        total_price = sum(
            (
                item.product.price * item.quantity
                for item in cart_items
            ),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"))
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            shipping_address=shipping_address,
            status=Order.Status.PENDING,
        )
        order_items = []
        for item in cart_items:
            product = products[item.product_id]
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    product_name=product.name,
                    quantity=item.quantity,
                    price_at_that_time=product.price,
                )
            )
            product.stock -= item.quantity
            product.save(update_fields=["stock", "updated_at"])
        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()
    return order


def update_order_status(order, new_status):
    allowed_transitions = {
        Order.Status.PENDING: {Order.Status.SHIPPING, Order.Status.CANCELLED},
        Order.Status.SHIPPING: {Order.Status.COMPLETED, Order.Status.CANCELLED},
        Order.Status.COMPLETED: set(),
        Order.Status.CANCELLED: set(),
    }
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)
        if locked_order.status == new_status:
            return locked_order
        if new_status not in allowed_transitions[locked_order.status]:
            raise ValidationError(
                {"status": "This order status transition is not allowed."}
            )
        if new_status == Order.Status.CANCELLED:
            product_ids = list(
                locked_order.items.order_by("product_id").values_list(
                    "product_id",
                    flat=True,
                )
            )
            products = {
                product.pk: product
                for product in Product.objects.select_for_update()
                .filter(pk__in=product_ids)
                .order_by("pk")
            }
            for order_item in locked_order.items.select_related("product"):
                product = products[order_item.product_id]
                product.stock += order_item.quantity
                product.save(update_fields=["stock", "updated_at"])
        locked_order.status = new_status
        locked_order.save(update_fields=["status", "updated_at"])
    return locked_order
