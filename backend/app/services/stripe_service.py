import stripe
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from typing import Optional, Dict, Any, Tuple

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Stripe customer by ID."""
        try:
            return stripe.Customer.retrieve(customer_id)
        except Exception as e:
            print(f"Error retrieving Stripe customer: {e}")
            return None
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
    def cancel_subscription_immediately(subscription_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a subscription immediately (no grace period)."""
        try:
            # In Stripe's Python SDK, deleting a subscription cancels it immediately
            subscription = stripe.Subscription.delete(subscription_id)
            return subscription
        except Exception as e:
            print(f"Error immediately canceling subscription: {e}")
            return None

    @staticmethod
    def cancel_subscription_safe(subscription_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Like cancel_subscription but returns (result, error_message)."""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def cancel_subscription_immediately_safe(subscription_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Like cancel_subscription_immediately but returns (result, error_message)."""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return subscription, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def find_active_subscription_for_customer(customer_id: str) -> Optional[Dict[str, Any]]:
        """Find an active or trialing subscription for a given customer"""
        try:
            subs = stripe.Subscription.list(customer=customer_id, status="all", limit=10)
            for s in subs.get("data", []):
                if s.get("status") in ("active", "trialing"):
                    return s
            return None
        except Exception as e:
            print(f"Error listing subscriptions: {e}")
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
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        client_reference_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
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
                client_reference_id=client_reference_id,
                metadata=metadata or {},
                success_url=success_url,
                cancel_url=cancel_url
            )
            return session
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None

    @staticmethod
    def get_checkout_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a checkout session."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except Exception as e:
            print(f"Error retrieving checkout session: {e}")
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
            try:
                # Stripe provides rich error info; surface the helpful parts
                msg = getattr(e, "user_message", None) or str(e)
                body = getattr(e, "json_body", None)
                code = getattr(e, "code", None)
                param = getattr(e, "param", None)
                print(f"Error creating portal session: message={msg}, code={code}, param={param}, return_url={return_url}, customer={customer_id}")
                if body:
                    print(f"Stripe error body: {body}")
            except Exception:
                print(f"Error creating portal session: {e}")
            return None
    
    @staticmethod
    def process_webhook_event(payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Process and verify webhook events"""
        try:
            # Support multiple secrets (comma-separated) to ease live/test transitions
            # Also look for common alternative env vars to avoid deployment mismatches
            import os
            configured = [s.strip() for s in (settings.STRIPE_WEBHOOK_SECRET or "").split(",") if s.strip()]
            extras = []
            for key in ("STRIPE_LIVE_WEBHOOK_SECRET", "STRIPE_TEST_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRETS"):
                val = os.environ.get(key, "")
                if val:
                    extras.extend([s.strip() for s in val.split(",") if s.strip()])
            # Merge and dedupe, preserve order: configured first, then extras
            seen = set()
            secrets = []
            for s in configured + extras:
                if s and s not in seen:
                    secrets.append(s)
                    seen.add(s)
            try:
                print(f"Webhook verification: attempting {len(secrets)} secret(s)")
            except Exception:
                pass
            last_err = None
            for secret in secrets or [""]:
                try:
                    if not secret:
                        continue
                    event = stripe.Webhook.construct_event(payload, sig_header, secret)
                    return event
                except Exception as inner_e:
                    last_err = inner_e
                    continue
            if last_err:
                raise last_err
            # If we got here, no valid secret configured
            raise ValueError("No Stripe webhook secret configured (set STRIPE_WEBHOOK_SECRET or *_WEBHOOK_SECRET env vars)")
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