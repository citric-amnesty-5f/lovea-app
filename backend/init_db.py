"""
Initialize database with sample data for testing
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.database import SessionLocal, init_db, engine
from app.models import (
    User, Profile, Interest, Preference,
    Gender, UserRole, Base
)
from app.auth import get_password_hash


def create_sample_interests(db: Session):
    """Create sample interests"""
    interests_data = [
        {"name": "Hiking", "category": "sports", "icon": "🥾"},
        {"name": "Yoga", "category": "fitness", "icon": "🧘"},
        {"name": "Cooking", "category": "food", "icon": "🍳"},
        {"name": "Photography", "category": "arts", "icon": "📷"},
        {"name": "Travel", "category": "lifestyle", "icon": "✈️"},
        {"name": "Reading", "category": "hobbies", "icon": "📚"},
        {"name": "Music", "category": "entertainment", "icon": "🎵"},
        {"name": "Dancing", "category": "entertainment", "icon": "💃"},
        {"name": "Gaming", "category": "hobbies", "icon": "🎮"},
        {"name": "Fitness", "category": "sports", "icon": "💪"},
        {"name": "Art", "category": "arts", "icon": "🎨"},
        {"name": "Movies", "category": "entertainment", "icon": "🎬"},
        {"name": "Coffee", "category": "food", "icon": "☕"},
        {"name": "Wine", "category": "food", "icon": "🍷"},
        {"name": "Dogs", "category": "pets", "icon": "🐕"},
        {"name": "Cats", "category": "pets", "icon": "🐈"},
        {"name": "Running", "category": "sports", "icon": "🏃"},
        {"name": "Cycling", "category": "sports", "icon": "🚴"},
        {"name": "Meditation", "category": "wellness", "icon": "🧘"},
        {"name": "Beach", "category": "lifestyle", "icon": "🏖️"},
    ]

    for interest_data in interests_data:
        existing = db.query(Interest).filter(Interest.name == interest_data["name"]).first()
        if not existing:
            interest = Interest(**interest_data)
            db.add(interest)

    db.commit()
    print(f"✅ Created {len(interests_data)} interests")


def create_admin_user(db: Session):
    """Create admin user"""
    admin_email = "admin@loveai.com"

    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print(f"⚠️  Admin user already exists")
        return existing

    # Create admin user
    admin_user = User(
        email=admin_email,
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    db.flush()

    # Create admin profile
    admin_profile = Profile(
        user_id=admin_user.id,
        name="Admin User",
        date_of_birth=datetime(1990, 1, 1),
        gender=Gender.OTHER,
        bio="System administrator",
        occupation="System Admin",
        location="San Francisco, CA",
        onboarding_completed=True,
        profile_completion=100
    )
    db.add(admin_profile)
    db.flush()

    # Create admin preferences
    admin_prefs = Preference(
        profile_id=admin_profile.id,
        min_age=18,
        max_age=99,
        looking_for=[Gender.MALE.value, Gender.FEMALE.value, Gender.NON_BINARY.value],
        max_distance=100
    )
    db.add(admin_prefs)

    db.commit()
    db.refresh(admin_user)

    print(f"✅ Created admin user: {admin_email} / admin123")
    return admin_user


def create_demo_users(db: Session, count: int = 10):
    """Create demo users for testing"""
    names = [
        "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank",
        "Grace", "Henry", "Ivy", "Jack", "Kate", "Leo",
        "Mia", "Noah", "Olivia", "Peter", "Quinn", "Ruby"
    ]

    occupations = [
        "Software Engineer", "Designer", "Teacher", "Doctor",
        "Artist", "Entrepreneur", "Consultant", "Writer",
        "Marketing Manager", "Data Scientist"
    ]

    cities = [
        "San Francisco, CA", "New York, NY", "Los Angeles, CA",
        "Chicago, IL", "Austin, TX", "Seattle, WA",
        "Boston, MA", "Denver, CO", "Portland, OR", "Miami, FL"
    ]

    bios = [
        "Love exploring new places and trying new foods. Always up for an adventure!",
        "Passionate about technology and innovation. Let's grab coffee and talk startups!",
        "Artist at heart, engineer by profession. Looking for someone to share experiences with.",
        "Fitness enthusiast and foodie. Balance is key!",
        "World traveler seeking a partner in crime for the next adventure.",
        "Music lover and coffee addict. Let's see where this goes!",
        "Outdoor enthusiast who loves hiking and camping. Nature is my therapy.",
        "Bookworm by day, Netflix binger by night. Looking for my reading buddy.",
        "Yoga instructor with a passion for wellness and mindfulness.",
        "Tech geek who loves gaming and building cool projects."
    ]

    all_interests = db.query(Interest).all()

    created_count = 0

    for i in range(count):
        email = f"user{i+1}@loveai.com"

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            continue

        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash("user123"),
            role=UserRole.USER,
            is_active=True,
            is_verified=random.choice([True, False])
        )
        db.add(user)
        db.flush()

        # Random age between 22 and 45
        age = random.randint(22, 45)
        dob = datetime.now() - timedelta(days=age * 365)

        # Create profile
        profile = Profile(
            user_id=user.id,
            name=names[i % len(names)],
            date_of_birth=dob,
            gender=random.choice([Gender.MALE, Gender.FEMALE, Gender.NON_BINARY]),
            bio=random.choice(bios),
            occupation=random.choice(occupations),
            location=random.choice(cities),
            height=random.randint(155, 195),
            onboarding_completed=True,
            profile_completion=random.randint(60, 100)
        )
        db.add(profile)
        db.flush()

        # Add random interests
        num_interests = random.randint(3, 8)
        selected_interests = random.sample(all_interests, num_interests)
        profile.interests.extend(selected_interests)

        # Create preferences
        looking_for_options = [
            [Gender.FEMALE.value],
            [Gender.MALE.value],
            [Gender.MALE.value, Gender.FEMALE.value],
            [Gender.MALE.value, Gender.FEMALE.value, Gender.NON_BINARY.value]
        ]

        prefs = Preference(
            profile_id=profile.id,
            min_age=max(18, age - 10),
            max_age=min(99, age + 10),
            looking_for=random.choice(looking_for_options),
            max_distance=random.choice([25, 50, 100])
        )
        db.add(prefs)

        created_count += 1

    db.commit()
    print(f"✅ Created {created_count} demo users (password: user123)")


def main():
    """Initialize database with sample data"""
    print("🚀 Initializing database...")

    # Create tables
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")

    # Create session
    db = SessionLocal()

    try:
        # Create interests
        print("🏷️  Creating interests...")
        create_sample_interests(db)

        # Create admin user
        print("👤 Creating admin user...")
        create_admin_user(db)

        # Create demo users
        print("👥 Creating demo users...")
        create_demo_users(db, count=100)

        print("\n✨ Database initialization complete!")
        print("\n📋 Test Credentials:")
        print("   Admin: admin@loveai.com / admin123")
        print("   Users: user1@loveai.com through user100@loveai.com / user123")

    finally:
        db.close()


if __name__ == "__main__":
    main()
