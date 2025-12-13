from db_manager import get_db_engine, Base
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def inspect_db():
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Check columns in 'projects' table
    print("--- Projects Table Columns ---")
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result]
        print(columns)
        
        has_is_deleted = 'is_deleted' in columns
        print(f"Has 'is_deleted': {has_is_deleted}")

    # 2. Check for the requested titles
    titles = [
        "250809 23기 공동체학교 2-2",
        "250809 23기 공동체학교 2-3",
        "250816 23기 공동체학교 3-1",
        "250816 23기 공동체학교 3-2",
        "250816 23기 공동체학교 3-3"
    ]

    print("\n--- Searching for Titles ---")
    for t in titles:
        # Search using like
        query = text("SELECT id, title, youtube_url" + (", is_deleted" if has_is_deleted else "") + " FROM projects WHERE title LIKE :t")
        result = session.execute(query, {"t": f"%{t}%"}).fetchall()
        
        if result:
            for row in result:
                print(f"Found '{t}': ID={row.id}, Title='{row.title}', Deleted={row.is_deleted if has_is_deleted else 'N/A'}")
        else:
            print(f"NOT Found: '{t}'")

    session.close()

if __name__ == "__main__":
    inspect_db()
