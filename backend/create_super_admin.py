"""
Create the default super admin user
Run this once to set up the system administrator
"""

from shared.database import SessionLocal
from shared.models import User, Profile
from services.auth.service import AuthService

def create_super_admin():
    db = SessionLocal()
    
    try:
        print("\n=== Creating Super Admin ===\n")
        
        # Check if super admin already exists
        existing = db.query(User).filter(User.role == "super_admin").first()
        if existing:
            print(f"✓ Super admin already exists: {existing.username}")
            print(f"  Email: {existing.email}")
            return
        
        # Create super admin
        username = "superadmin"
        email = "admin@techfootprint.com"  # Use valid domain
        password = "SuperAdmin@123"  # Change this in production!
        
        hashed_password = AuthService.get_password_hash(password)
        
        super_admin = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name="System Administrator",
            role="super_admin",
            is_active=True
        )
        
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        # Create profile
        profile = Profile(
            user_id=super_admin.id,
            bio="System Administrator",
            portfolio_slug=username,
            is_public=False
        )
        db.add(profile)
        db.commit()
        
        print("✓ Super Admin created successfully!\n")
        print("=" * 50)
        print("LOGIN CREDENTIALS")
        print("=" * 50)
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Email: {email}")
        print("=" * 50)
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("⚠️  This account has full system access.\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
