import random
from faker import Faker

from src.utils.database import get_connection


fake = Faker("en_IN")

# Make our generated data reproducible.
random.seed(42)
Faker.seed(42)


SUPPLIER_COUNT = 250


SUPPLIER_TYPES = [
    "Manufacturer",
    "Distributor",
    "Wholesaler",
    "Importer",
]


PAYMENT_TERMS = [
    "Net-15",
    "Net-30",
    "Net-45",
    "Net-60",
]


# Indian locations for our simulated suppliers.
LOCATIONS = [
    ("Maharashtra", "Mumbai"),
    ("Karnataka", "Bengaluru"),
    ("Tamil Nadu", "Chennai"),
    ("Telangana", "Hyderabad"),
    ("West Bengal", "Kolkata"),
    ("Gujarat", "Ahmedabad"),
    ("Delhi", "New Delhi"),
    ("Uttar Pradesh", "Noida"),
    ("Haryana", "Gurugram"),
    ("Rajasthan", "Jaipur"),
    ("Madhya Pradesh", "Indore"),
    ("Kerala", "Kochi"),
    ("Punjab", "Ludhiana"),
    ("Bihar", "Patna"),
    ("Assam", "Guwahati"),
]


def generate_supplier_profile():
    """
    Generate a supplier with a realistic performance profile.

    70% = good suppliers
    20% = average suppliers
    10% = problematic suppliers
    """

    profile = random.choices(
        ["GOOD", "AVERAGE", "PROBLEM"],
        weights=[70, 20, 10],
        k=1,
    )[0]

    if profile == "GOOD":
        rating = round(random.uniform(4.2, 5.0), 2)
        lead_time = random.randint(3, 7)

    elif profile == "AVERAGE":
        rating = round(random.uniform(3.2, 4.19), 2)
        lead_time = random.randint(6, 12)

    else:
        rating = round(random.uniform(2.0, 3.19), 2)
        lead_time = random.randint(10, 20)

    return profile, rating, lead_time


def generate_suppliers():

    connection = get_connection()
    cursor = connection.cursor()

    insert_query = """
        INSERT INTO suppliers (
            supplier_name,
            country,
            state,
            city,
            supplier_type,
            rating,
            default_lead_time_days,
            payment_terms,
            is_active
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        );
    """

    suppliers = []

    for i in range(1, SUPPLIER_COUNT + 1):

        state, city = random.choice(LOCATIONS)

        profile, rating, lead_time = generate_supplier_profile()

        supplier_name = (
            f"{fake.company()} "
            f"({profile.title()})"
        )

        supplier_type = random.choice(SUPPLIER_TYPES)
        payment_terms = random.choice(PAYMENT_TERMS)

        suppliers.append(
            (
                supplier_name,
                "India",
                state,
                city,
                supplier_type,
                rating,
                lead_time,
                payment_terms,
                True,
            )
        )

    cursor.executemany(insert_query, suppliers)

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Inserted {len(suppliers)} suppliers.")


if __name__ == "__main__":
    generate_suppliers()