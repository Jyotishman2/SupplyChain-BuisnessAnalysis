import random

from src.utils.database import get_connection


random.seed(42)


WAREHOUSES = [
    ("WH_DEL_01", "Delhi Central", "New Delhi", "Delhi"),
    ("WH_MUM_01", "Mumbai Central", "Mumbai", "Maharashtra"),
    ("WH_BLR_01", "Bengaluru Central", "Bengaluru", "Karnataka"),
    ("WH_CHE_01", "Chennai Central", "Chennai", "Tamil Nadu"),
    ("WH_HYD_01", "Hyderabad Central", "Hyderabad", "Telangana"),
    ("WH_KOL_01", "Kolkata Central", "Kolkata", "West Bengal"),
    ("WH_PUN_01", "Pune Central", "Pune", "Maharashtra"),
    ("WH_GUW_01", "Guwahati Central", "Guwahati", "Assam"),
    ("WH_AHM_01", "Ahmedabad Central", "Ahmedabad", "Gujarat"),
    ("WH_JAI_01", "Jaipur Central", "Jaipur", "Rajasthan"),
    ("WH_LKO_01", "Lucknow Central", "Lucknow", "Uttar Pradesh"),
    ("WH_PAT_01", "Patna Central", "Patna", "Bihar"),
    ("WH_BBS_01", "Bhubaneswar Central", "Bhubaneswar", "Odisha"),
    ("WH_KOC_01", "Kochi Central", "Kochi", "Kerala"),
    ("WH_IND_01", "Indore Central", "Indore", "Madhya Pradesh"),
    ("WH_LDH_01", "Ludhiana Central", "Ludhiana", "Punjab"),
    ("WH_NAG_01", "Nagpur Central", "Nagpur", "Maharashtra"),
    ("WH_SUR_01", "Surat Central", "Surat", "Gujarat"),
    ("WH_VIZ_01", "Visakhapatnam Central", "Visakhapatnam", "Andhra Pradesh"),
    ("WH_RNC_01", "Ranchi Central", "Ranchi", "Jharkhand"),
]


# Approximate coordinates for the simulated warehouse locations.
COORDINATES = {
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567),
    "Guwahati": (26.1445, 91.7362),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Patna": (25.5941, 85.1376),
    "Bhubaneswar": (20.2961, 85.8245),
    "Kochi": (9.9312, 76.2673),
    "Indore": (22.7196, 75.8577),
    "Ludhiana": (30.9010, 75.8573),
    "Nagpur": (21.1458, 79.0882),
    "Surat": (21.1702, 72.8311),
    "Visakhapatnam": (17.6868, 83.2185),
    "Ranchi": (23.3441, 85.3096),
}


def generate_warehouses():

    connection = get_connection()
    cursor = connection.cursor()

    insert_query = """
        INSERT INTO warehouses (
            warehouse_name,
            city,
            state,
            country,
            warehouse_type,
            capacity_units,
            operating_cost_per_day,
            latitude,
            longitude,
            opened_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        );
    """

    warehouses = []

    for warehouse_id, name, city, state in WAREHOUSES:

        # Different warehouse sizes create realistic utilization differences.
        capacity = random.randint(100_000, 500_000)

        operating_cost = round(
            random.uniform(40_000, 150_000),
            2
        )

        latitude, longitude = COORDINATES[city]

        warehouse_type = random.choices(
            [
                "FULFILLMENT_CENTER",
                "REGIONAL_WAREHOUSE",
                "DISTRIBUTION_CENTER",
            ],
            weights=[50, 30, 20],
            k=1,
        )[0]

        warehouses.append(
            (
                name,
                city,
                state,
                "India",
                warehouse_type,
                capacity,
                operating_cost,
                latitude,
                longitude,
                "2023-01-01",
            )
        )

    cursor.executemany(insert_query, warehouses)

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Inserted {len(warehouses)} warehouses.")


if __name__ == "__main__":
    generate_warehouses()
    