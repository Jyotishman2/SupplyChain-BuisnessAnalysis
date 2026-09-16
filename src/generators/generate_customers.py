import io
import random
from datetime import date, timedelta

from faker import Faker

from src.utils.database import get_connection


fake = Faker("en_IN")

random.seed(42)
Faker.seed(42)

CUSTOMER_COUNT = 10_000

LOCATIONS = [
    ("Mumbai", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Bengaluru", "Karnataka"),
    ("Hyderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"),
    ("Kolkata", "West Bengal"),
    ("Pune", "Maharashtra"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"),
    ("Surat", "Gujarat"),
    ("Kochi", "Kerala"),
    ("Indore", "Madhya Pradesh"),
    ("Bhopal", "Madhya Pradesh"),
    ("Guwahati", "Assam"),
]

SEGMENTS = [
    "Regular",
    "Premium",
    "VIP",
]

SEGMENT_WEIGHTS = [70, 25, 5]


def generate_customers():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers;")
    existing_count = cursor.fetchone()[0]

    if existing_count:
        print(
            f"Customers table already contains {existing_count} rows. "
            "No new customers inserted."
        )
        cursor.close()
        connection.close()
        return

    customers = []

    start_date = date(2021, 1, 1)
    end_date = date(2026, 8, 31)

    days_range = (end_date - start_date).days

    for _ in range(CUSTOMER_COUNT):

        city, state = random.choice(LOCATIONS)

        segment = random.choices(
            SEGMENTS,
            weights=SEGMENT_WEIGHTS,
            k=1,
        )[0]

        signup_date = start_date + timedelta(
            days=random.randint(0, days_range)
        )

        customers.append(
            (
                segment,
                city,
                state,
                "India",
                signup_date,
            )
        )

    buffer = io.StringIO()

    for customer in customers:
        buffer.write(
            "\t".join(str(value) for value in customer)
            + "\n"
        )

    buffer.seek(0)

    cursor.copy_from(
        buffer,
        "customers",
        columns=(
            "customer_segment",
            "city",
            "state",
            "country",
            "signup_date",
        ),
        sep="\t",
    )

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Inserted {len(customers)} customers.")


if __name__ == "__main__":
    generate_customers()