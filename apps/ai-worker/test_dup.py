import sys
import psycopg

url = "postgresql://hotel_intel_app:123456@localhost:5432/hotel_intel"
conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)

text = """Vinpearl Resort Ha Long:
- 30/4: Deluxe Ocean 3000k/dem an sang
- 01/5: Deluxe Ocean 3500k/dem an sang
lien he 0909123456"""

exclude_id = "97c24f70-fab8-43bc-aa9d-71b1258e31b7"

with conn.cursor() as cur:
    row = cur.execute(
        """
        SELECT id, captured_at FROM raw_messages 
        WHERE text = %s 
            AND id != %s
            AND (group_id = %s OR (%s::text IS NULL AND group_id IS NULL))
            AND captured_at >= now() - interval '1 hour' * %s
        """,
        (text, exclude_id, "group_test_001", "group_test_001", 1)
    ).fetchall()
    print("Duplicates found:", row)
