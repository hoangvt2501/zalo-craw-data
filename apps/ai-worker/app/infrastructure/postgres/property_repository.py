from app.ports.repositories import PropertyRepository


class PostgresPropertyRepository(PropertyRepository):
    def __init__(self, conn):
        self.conn = conn

    def list_properties(self) -> list[dict]:
        return self.conn.execute(
            """
            SELECT id, name, address, district, province, stars, aliases, metadata
            FROM properties
            ORDER BY province, name
            """
        ).fetchall()
