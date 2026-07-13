from sqlalchemy import create_engine, text

url = "postgresql+psycopg://opportunitymap:opportunitymap_dev@localhost:5432/opportunitymap"
engine = create_engine(url)
with engine.connect() as conn:
    counts = conn.execute(
        text("SELECT source_name, COUNT(*) FROM opportunities GROUP BY source_name ORDER BY source_name")
    ).fetchall()
    print("By source:", counts)
    sample = conn.execute(
        text(
            "SELECT title, source_name, opportunity_type::text "
            "FROM opportunities ORDER BY id DESC LIMIT 5"
        )
    ).fetchall()
    print("Recent:")
    for row in sample:
        print(" ", row)
