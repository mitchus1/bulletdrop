import stripe
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from typing import Optional, Dict, Any

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    def create_customer(user: User) -> Optional[Dict[str, Any]]:
        """Create a Stripe customer for the user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "user_id": str(user.id),
                    "username": user.username
                }
            )
            return customer
        except Exception as e:
            print(f"Error creating Stripe customer: {e}")
            return None
    
    @staticmethod
    def create_subscription(customer_id: str, price_id: str) -> Optional[Dict[str, Any]]:
        """Create a subscription for a customer"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"]
            )
            return subscription
        except Exception as e:
            print(f"Error creating subscription: {e}")
            return None
    
    @staticmethod
    def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except Exception as e:
            print(f"Error retrieving subscription: {e}")
            return None
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription
        except Exception as e:
            print(f"Error canceling subscription: {e}")
            return None
    
    @staticmethod
    def reactivate_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """Reactivate a canceled subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return subscription
        except Exception as e:
            print(f"Error reactivating subscription: {e}")
            return None
    
    @staticmethod
    def create_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str) -> Optional[Dict[str, Any]]:
        """Create a Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url
            )
            return session
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None
    
    @staticmethod
    def get_customer_portal_url(customer_id: str, return_url: str) -> Optional[str]:
        """Create a customer portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except Exception as e:
            print(f"Error creating portal session: {e}")
            return None
    
    @staticmethod
    def process_webhook_event(payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Process and verify webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            print(f"Invalid payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature: {e}")
            return None
    
    @staticmethod
    def update_user_premium_status(db: Session, user: User, subscription_data: Dict[str, Any]) -> bool:
        """Update user premium status based on subscription data"""
        try:
            # Check if subscription is active
            status = subscription_data.get("status")
            current_period_end = subscription_data.get("current_period_end")
            
            if status in ["active", "trialing"]:
                user.is_premium = True
                if current_period_end:
                    user.premium_expires_at = datetime.fromtimestamp(current_period_end)
                user.stripe_subscription_id = subscription_data.get("id")
            else:
                user.is_premium = False
                user.premium_expires_at = None
            
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating user premium status: {e}")
            db.rollback()
            return False