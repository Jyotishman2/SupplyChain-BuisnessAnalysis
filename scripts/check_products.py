from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_products,
            COUNT(DISTINCT sku) AS unique_skus,
            COUNT(DISTINCT category_id) AS categories_used,
            COUNT(DISTINCT supplier_id) AS suppliers_used
        FROM products;
    """)

    total, unique_skus, categories_used, suppliers_used = cur.fetchone()

    print("Product validation:\n")
    print(f"Total products: {total}")
    print(f"Unique SKUs: {unique_skus}")
    print(f"Categories used: {categories_used}")
    print(f"Suppliers used: {suppliers_used}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()