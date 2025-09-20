#!/usr/bin/env python3
"""
Create admin user script
Run this script to create the first admin user for the application.
"""

import asyncio
import sys
from getpass import getpass
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User

def create_admin_user():
    """Create an admin user interactively"""
    
    print("=== BulletDrop Admin User Creation ===")
    print("This script will create an admin user for the application.")
    print()
    
    # Get user details
    username = input("Enter admin username: ").strip()
    if not username:
        print("Username cannot be empty!")
        return False
    
    email = input("Enter admin email: ").strip()
    if not email:
        print("Email cannot be empty!")
        return False
    
    password = getpass("Enter admin password: ")
    if not password:
        print("Password cannot be empty!")
        return False
    
    confirm_password = getpass("Confirm admin password: ")
    if password != confirm_password:
        print("Passwords do not match!")
        return False
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists!")
            return False
        
        # Create admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"User ID: {admin_user.id}")
        print(f"Email: {admin_user.email}")
        print(f"Admin: {admin_user.is_admin}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def promote_user_to_admin():
    """Promote an existing user to admin"""
    
    print("=== Promote User to Admin ===")
    username_or_email = input("Enter username or email to promote: ").strip()
    
    if not username_or_email:
        print("Username/email cannot be empty!")
        return False
    
    db: Session = SessionLocal()
    
    try:
        # Find user
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user:
            print(f"User with username/email '{username_or_email}' not found!")
            return False
        
        if user.is_admin:
            print(f"User '{user.username}' is already an admin!")
            return False
        
        # Promote to admin
        user.is_admin = True
        user.is_verified = True
        db.commit()
        
        print(f"✅ User '{user.username}' promoted to admin successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def list_admin_users():
    """List all admin users"""
    
    print("=== Current Admin Users ===")
    
    db: Session = SessionLocal()
    
    try:
        admins = db.query(User).filter(User.is_admin == True).all()
        
        if not admins:
            print("No admin users found!")
            return
        
        print(f"Found {len(admins)} admin user(s):")
        print()
        
        for admin in admins:
            print(f"ID: {admin.id}")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            print(f"Active: {admin.is_active}")
            print(f"Verified: {admin.is_verified}")
            print(f"Created: {admin.created_at}")
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error listing admin users: {e}")
        
    finally:
        db.close()

def main():
    """Main function with menu"""
    
    while True:
        print("\n=== BulletDrop Admin Management ===")
        print("1. Create new admin user")
        print("2. Promote existing user to admin")
        print("3. List all admin users")
        print("4. Exit")
        print()
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            promote_user_to_admin()
        elif choice == "3":
            list_admin_users()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()