from models import Skills
from database import SessionLocal
def seed_skills():
    db = SessionLocal()
    try:
        skills_to_add = ["Plumber", "Electrician", "Carpenter", "Mason", "Painter"]
        for skill_na in skills_to_add:
            exists = db.query(Skills).filter(Skills.skills_name == skill_na).first()
            if not exists:
                new_skill = Skills(skills_name = skill_na)
                db.add(new_skill)
                print(f"Adding skill: {skill_na}")
            else:
                print(f"Skill {skill_na} already exists. Skipping...")
        db.commit()
        print("Seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback() 
    finally:
        db.close() 
if __name__ == "__main__":
    seed_skills()