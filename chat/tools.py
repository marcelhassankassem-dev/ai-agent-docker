from decimal import ROUND_HALF_UP, Decimal

from .models import Item


def check_stock(name):
    """Look up how many of an item we have."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    return {"name": item.name, "quantity": item.quantity, "price": float(item.price)}


def list_items():
    """Return every item in the inventory."""
    items = Item.objects.all()
    return {"items": [{"name": i.name, "quantity": i.quantity, "price": float(i.price)} for i in items]}


def add_item(name, quantity, price=None):
    """Create a new item, or add to an existing one's stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is not None:
        item.quantity += quantity
        if price is not None:
            item.price = Decimal(price)
        item.save()
        return {"name": item.name, "quantity": item.quantity, "price": float(item.price), "created": False}
    item = Item.objects.create(name=name, quantity=quantity, price=Decimal(price) if price is not None else Decimal(0.00))
    return {"name": item.name, "quantity": item.quantity, "price": float(item.price), "created": True}

def set_price(name, price):
    """Set the price of an existing item."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.price = Decimal(price)
    item.save()
    return {"name": item.name, "quantity": item.quantity, "price": float(item.price)}

def calculate_cost(name, quantity, vat_percent=0):
    """Compute the total cost of buying some units of an item, optionally with VAT."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    cents = Decimal("0.01")
    subtotal = (item.price * quantity).quantize(cents, ROUND_HALF_UP)
    vat = (subtotal * Decimal(str(vat_percent)) / 100).quantize(cents, ROUND_HALF_UP)
    return {
        "name": item.name,
        "unit_price": float(item.price),
        "quantity": quantity,
        "subtotal": float(subtotal),
        "vat_percent": vat_percent,
        "vat_amount": float(vat),
        "total": float(subtotal + vat),
    }

def remove_stock(name, quantity):
    """Take a quantity out of stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    if quantity > item.quantity:
        return {
            "error": f"Cannot remove {quantity}. Only {item.quantity} in stock.",
            "name": item.name,
            "quantity": item.quantity,
        }
    item.quantity -= quantity
    item.save()
    return {"name": item.name, "quantity": item.quantity}


def delete_item(name):
    """Remove an item from the inventory entirely."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.delete()
    return {"deleted": name}


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "check_stock",
        "description": "Look up the current quantity of a single item in the inventory. Use this whenever the user asks whether something is in stock or how many there are.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_items",
        "description": "Return every item in the inventory with its quantity. Use this when the user asks what is in stock generally, or asks for a list, rather than about one specific item.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "add_item",
        "description": "Add stock to the inventory. If the item does not exist it is created; if it already exists the quantity is added to the existing total. Use this for restocking and for new deliveries.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to add. Must be positive.",
                },
                "price": {
                    "type": "number",
                    "description": "Optional unit price in dollars, e.g. 1.50.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
     {
        "type": "function",
        "name": "set_price", "description": "Set or change the unit price of an existing item.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the item."},
                "price": {"type": "number", "description": "The new unit price in dollars."},
            },
            "required": ["name", "price"],
        },
    },
    {
        "type": "function",
        "name": "calculate_cost",
        "description": "Calculate the total cost of buying a quantity of an item, optionally adding a VAT/tax percentage. Always use this for any price or cost question instead of doing math yourself.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the item."},
                "quantity": {"type": "integer", "description": "How many units."},
                "vat_percent": {"type": "number", "description": "VAT percentage to add, e.g. 10 for 10%. Use 0 if none."},
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "remove_stock",
        "description": "Reduce the quantity of an existing item. Use this when items are sold, shipped or used. This does NOT delete the item; it only lowers the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to remove. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "delete_item",
        "description": "Permanently remove an item and its record from the inventory entirely. This is destructive. Only use it when the user clearly wants the item gone, not when they want to reduce its quantity.",
        "parameters": {
            "type": "object",
            "properties": {

                "name": {
                    "type": "string",
                    "description": "The name of the item to delete.",
                },
            },
            "required": ["name"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_stock": check_stock,
    "list_items": list_items,
    "add_item": add_item,
    "set_price": set_price,
    "calculate_cost": calculate_cost,
    "remove_stock": remove_stock,
    "delete_item": delete_item,
}
