from src.utils.database import get_connection


CATEGORIES = [
    ("Smartphones", "Electronics"),
    ("Laptops", "Electronics"),
    ("Televisions", "Electronics"),
    ("Audio", "Electronics"),
    ("Cameras", "Electronics"),
    ("Home Appliances", "Home & Kitchen"),
    ("Kitchen Appliances", "Home & Kitchen"),
    ("Furniture", "Home & Kitchen"),
    ("Cookware", "Home & Kitchen"),
    ("Groceries", "Grocery"),
    ("Beverages", "Grocery"),
    ("Snacks", "Grocery"),
    ("Mens Clothing", "Fashion"),
    ("Womens Clothing", "Fashion"),
    ("Kids Clothing", "Fashion"),
    ("Footwear", "Fashion"),
    ("Beauty", "Beauty"),
    ("Personal Care", "Beauty"),
    ("Sports Equipment", "Sports"),
    ("Fitness", "Sports"),
    ("Books", "Books"),
    ("Toys", "Toys"),
    ("Automotive", "Automotive"),
    ("Pet Supplies", "Pet"),
    ("Office Supplies", "Office")
]


def generate_categories():

    connection = get_connection()
    cursor = connection.cursor()

    insert_query = """
        INSERT INTO categories
            (category_name, department)
        VALUES
            (%s, %s)
        ON CONFLICT (category_name)
        DO NOTHING;
    """

    cursor.executemany(insert_query, CATEGORIES)

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Inserted {len(CATEGORIES)} categories.")


if __name__ == "__main__":
    generate_categories()