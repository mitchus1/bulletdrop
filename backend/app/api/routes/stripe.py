from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.stripe_service import StripeService
from app.core.config import settings

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for premium subscription"""
    try:
        # Create Stripe customer if not exists
        if not current_user.stripe_customer_id:
            customer = StripeService.create_customer(current_user)
            if not customer:
                raise HTTPException(status_code=500, detail="Failed to create customer")
            
            current_user.stripe_customer_id = customer["id"]
            db.commit()
        
        # Get base URL from request
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        
        # Create checkout session
        session = StripeService.create_checkout_session(
            customer_id=current_user.stripe_customer_id,
            price_id=settings.STRIPE_PRICE_ID,
            success_url=f"{base_url}/premium/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/premium"
        )
        
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
        
        return {"checkout_url": session["url"]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")

@router.get("/subscription-status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user)
):
    """Get current user's subscription status"""
    try:
        status = {
            "is_premium": current_user.is_premium,
            "premium_expires_at": current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None,
            "has_active_premium": current_user.has_active_premium(),
            "stripe_customer_id": current_user.stripe_customer_id,
            "stripe_subscription_id": current_user.stripe_subscription_id
        }
        
        # If user has a subscription, get details from Stripe
        if current_user.stripe_subscription_id:
            subscription = StripeService.get_subscription(current_user.stripe_subscription_id)
            if subscription:
                status.update({
                    "subscription_status": subscription.get("status"),
                    "current_period_end": subscription.get("current_period_end"),
                    "cancel_at_period_end": subscription.get("cancel_at_period_end")
                })
        
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting subscription status: {str(e)}")

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel the user's subscription (at period end)"""
    try:
        if not current_user.stripe_subscription_id:
            raise HTTPException(status_code=400, detail="No active subscription found")
        
        subscription = StripeService.cancel_subscription(current_user.stripe_subscription_id)
        if not subscription:
            raise HTTPException(status_code=500, detail="Failed to cancel subscription")
        
        return {"message": "Subscription will be canceled at the end of the current period"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error canceling subscription: {str(e)}")

@router.post("/reactivate-subscription")
async def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reactivate a canceled subscription"""
    try:
        if not current_user.stripe_subscription_id:
            raise HTTPException(status_code=400, detail="No subscription found")
        
        subscription = StripeService.reactivate_subscription(current_user.stripe_subscription_id)
        if not subscription:
            raise HTTPException(status_code=500, detail="Failed to reactivate subscription")
        
        return {"message": "Subscription reactivated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reactivating subscription: {str(e)}")

@router.get("/customer-portal")
async def get_customer_portal(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get Stripe customer portal URL for billing management"""
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No customer account found")
        
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        portal_url = StripeService.get_customer_portal_url(
            customer_id=current_user.stripe_customer_id,
            return_url=f"{base_url}/settings"
        )
        
        if not portal_url:
            raise HTTPException(status_code=500, detail="Failed to create portal session")
        
        return {"portal_url": portal_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating portal session: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        event = StripeService.process_webhook_event(payload, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        print(f"Received webhook event: {event['type']}")
        
        # Handle different event types
        if event["type"] == "customer.subscription.created":
            print("Handling subscription created")
            await handle_subscription_updated(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.updated":
            print("Handling subscription updated")
            await handle_subscription_updated(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.deleted":
            print("Handling subscription deleted")
            await handle_subscription_deleted(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_succeeded":
            print("Handling payment succeeded")
            await handle_payment_succeeded(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_failed":
            print("Handling payment failed")
            await handle_payment_failed(event["data"]["object"], db)
        else:
            print(f"Unhandled webhook event type: {event['type']}")
        
        return {"status": "success"}
    
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

async def handle_subscription_updated(subscription: Dict[str, Any], db: Session):
    """Handle subscription updated webhook"""
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")
    
    print(f"Subscription updated - Customer: {customer_id}, Subscription: {subscription_id}")
    
    # Find user by stripe_customer_id
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        print(f"Found user: {user.username}")
        user.stripe_subscription_id = subscription_id
        result = StripeService.update_user_premium_status(db, user, subscription)
        print(f"Updated premium status: {result}, is_premium: {user.is_premium}")
    else:
        print(f"No user found with stripe_customer_id: {customer_id}")

async def handle_subscription_deleted(subscription: Dict[str, Any], db: Session):
    """Handle subscription deleted webhook"""
    customer_id = subscription.get("customer")
    
    print(f"Subscription deleted - Customer: {customer_id}")
    
    # Find user by stripe_customer_id
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        print(f"Found user: {user.username}, removing premium status")
        user.is_premium = False
        user.premium_expires_at = None
        user.stripe_subscription_id = None
        db.commit()
    else:
        print(f"No user found with stripe_customer_id: {customer_id}")

async def handle_payment_succeeded(invoice: Dict[str, Any], db: Session):
    """Handle successful payment webhook"""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")
    
    print(f"Payment succeeded - Customer: {customer_id}, Subscription: {subscription_id}")
    
    if subscription_id:
        subscription = StripeService.get_subscription(subscription_id)
        if subscription:
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                print(f"Found user: {user.username}, updating premium status from payment")
                result = StripeService.update_user_premium_status(db, user, subscription)
                print(f"Updated premium status: {result}, is_premium: {user.is_premium}")
            else:
                print(f"No user found with stripe_customer_id: {customer_id}")

async def handle_payment_failed(invoice: Dict[str, Any], db: Session):
    """Handle failed payment webhook"""
    customer_id = invoice.get("customer")
    
    print(f"Payment failed for customer: {customer_id}")
    # You might want to send an email notification here
    # For now, we'll just log it