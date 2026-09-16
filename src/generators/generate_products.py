import random
from datetime import datetime

from faker import Faker

from src.utils.database import get_connection


fake = Faker("en_IN")

random.seed(42)
Faker.seed(42)


PRODUCT_COUNT = 1000


BRANDS = [
    "Nova",
    "Vertex",
    "Apex",
    "Zenith",
    "Orbit",
    "Prime",
    "Urban",
    "Pulse",
    "Nexa",
    "Everest",
    "Vivid",
    "Fusion",
    "Crest",
    "Matrix",
    "Titan",
]


def generate_products():

    connection = get_connection()
    cursor = connection.cursor()

    # Fetch categories already loaded into Supabase.
    cursor.execute("""
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_id;
    """)

    categories = cursor.fetchall()

    if not categories:
        raise RuntimeError(
            "No categories found. Run generate_categories first."
        )

    # Fetch suppliers already loaded into Supabase.
    cursor.execute("""
        SELECT supplier_id
        FROM suppliers
        WHERE is_active = TRUE
        ORDER BY supplier_id;
    """)

    suppliers = cursor.fetchall()

    if not suppliers:
        raise RuntimeError(
            "No active suppliers found. Run generate_suppliers first."
        )

    insert_query = """
        INSERT INTO products (
            sku,
            product_name,
            category_id,
            brand,
            unit_cost,
            selling_price,
            weight_kg,
            reorder_point,
            safety_stock,
            supplier_id,
            is_active,
            created_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (sku)
        DO NOTHING;
    """

    products = []

    for i in range(1, PRODUCT_COUNT + 1):

        category_id, category_name = random.choice(categories)
        supplier_id = random.choice(suppliers)[0]
        brand = random.choice(BRANDS)

        product_name = f"{brand} {category_name} {fake.word().title()}"

        # Generate realistic cost and selling price.
        unit_cost = round(random.uniform(100, 50_000), 2)

        margin = random.uniform(1.15, 1.50)

        selling_price = round(
            unit_cost * margin,
            2
        )

        weight_kg = round(
            random.uniform(0.1, 25.0),
            2
        )

        reorder_point = random.randint(20, 500)

        safety_stock = random.randint(
            max(5, reorder_point // 4),
            max(10, reorder_point // 2)
        )

        sku = f"SKU-{i:06d}"

        products.append(
            (
                sku,
                product_name,
                category_id,
                brand,
                unit_cost,
                selling_price,
                weight_kg,
                reorder_point,
                safety_stock,
                supplier_id,
                True,
                datetime.now(),
            )
        )

    cursor.executemany(insert_query, products)

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Inserted {len(products)} products.")


if __name__ == "__main__":
    generate_products()