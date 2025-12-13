from db_manager import DBManager, Project

db = DBManager('editor.db')
session = db.Session()

target_title = "250816 23기 공동체학교 3-3"
print(f"Searching for: {target_title}")

# Search by likely title match
projects = session.query(Project).filter(Project.title.like(f"%{target_title}%")).all()

if not projects:
    print("❌ Project not found!")
    # List all titles to see if it's slightly different
    all_projs = session.query(Project).all()
    print("Available projects:")
    for p in all_projs:
        print(f" - {p.id}: {p.title} (Deleted: {p.is_deleted})")
else:
    for p in projects:
        print(f"✅ Found: ID {p.id} | Title: {p.title} | Deleted: {p.is_deleted}")
        if p.is_deleted:
            print(f"   Shape: Restoring Project {p.id}...")
            p.is_deleted = False
        else:
            print(f"   Shape: Already Active.")
            
    session.commit()
    print("Done.")

session.close()
