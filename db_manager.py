from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    youtube_url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    video_duration = Column(Float, nullable=True)
    last_position = Column(Float, default=0.0)

    subtitles = relationship("Subtitle", back_populates="project", cascade="all, delete-orphan")

class Subtitle(Base):
    __tablename__ = 'subtitles'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    is_completed = Column(Integer, default=0) # SQLite doesn't have native Boolean, use Integer 0/1 properly or sqlalchemy handles it. Using Boolean in sqlalchemy usually maps to int/bool. Let's keep Boolean type for ORM.
    # Actually, let's use Boolean from sqlalchemy. 
    # But wait, original code used standard sqlalchemy types.
    # Let's redefine.
    
    project = relationship("Project", back_populates="subtitles")

class LearnedWord(Base):
    __tablename__ = 'learned_words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False, unique=True)
    count = Column(Integer, default=1)

def get_db_engine(db_path="editor.db"):
    return create_engine(f'sqlite:///{db_path}')

def init_db(db_path="editor.db"):
    engine = get_db_engine(db_path)
    Base.metadata.create_all(engine)
    
    # Auto-Migration: Check if is_completed exists in subtitles
    # Simple workaround for SQLite migration without alembic
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('subtitles')]
    if 'is_completed' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE subtitles ADD COLUMN is_completed BOOLEAN DEFAULT 0"))
            conn.commit()
            
    return sessionmaker(bind=engine)

class DBManager:
    def __init__(self, db_path="editor.db"):
        self.Session = init_db(db_path)

    def create_project(self, youtube_url, title, video_duration=None):
        session = self.Session()
        project = Project(
            youtube_url=youtube_url, 
            title=title, 
            video_duration=video_duration or 0
        )
        session.add(project)
        session.commit()
        project_id = project.id
        session.close()
        return project_id

    def delete_project(self, project_id):
        session = self.Session()
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            session.delete(project) # Cascades to subtitles
            session.commit()
        session.close()

    def get_all_projects(self):
        session = self.Session()
        projects = session.query(Project).order_by(Project.created_at.desc()).all()
        result = []
        for p in projects:
            total = len(p.subtitles)
            completed = sum(1 for s in p.subtitles if s.is_completed)
            
            status = "⚪" # New/Not started
            if total > 0:
                if completed == total:
                    status = "🟢"
                elif completed > 0:
                    status = "🟡"
            
            result.append({
                "id": p.id,
                "title": p.title,
                "youtube_url": p.youtube_url,
                "created_at": p.created_at,
                "status": status,
                "progress": f"{completed}/{total}"
            })
        session.close()
        return result

    def get_project(self, project_id):
        session = self.Session()
        project = session.query(Project).filter(Project.id == project_id).first()
        session.close()
        return project

    def save_subtitles(self, project_id, subtitles_data):
        """
        subtitles_data: list of dicts {'start': float, 'end': float, 'text': str, 'is_completed': bool}
        """
        session = self.Session()
        # Clear existing
        session.query(Subtitle).filter(Subtitle.project_id == project_id).delete()
        
        objects = [
            Subtitle(
                project_id=project_id,
                start_time=s['start'],
                end_time=s['end'],
                text=s['text'],
                is_completed=s.get('is_completed', False)
            ) for s in subtitles_data
        ]
        session.add_all(objects)
        session.commit()
        session.close()

    def get_subtitles(self, project_id):
        session = self.Session()
        subs = session.query(Subtitle).filter(Subtitle.project_id == project_id).order_by(Subtitle.start_time).all()
        result = [{
            "id": s.id,
            "start": s.start_time,
            "end": s.end_time,
            "text": s.text,
            "is_completed": s.is_completed
        } for s in subs]
        session.close()
        return result

    def add_learned_words(self, words):
        session = self.Session()
        for w in words:
            w = w.strip()
            if not w: continue
            existing = session.query(LearnedWord).filter(LearnedWord.word == w).first()
            if existing:
                existing.count += 1
            else:
                session.add(LearnedWord(word=w))
        session.commit()
        session.close()

    def get_learned_words(self):
        session = self.Session()
        # Get top 100 most frequent words to prevent prompt overflow
        words = session.query(LearnedWord).order_by(LearnedWord.count.desc()).limit(100).all()
        result = [w.word for w in words]
        session.close()
        return result

    # Deprecated dictionary methods removed.

    def update_project_position(self, project_id, position):
        session = self.Session()
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            project.last_position = position
            session.commit()
        session.close()
