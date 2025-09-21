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
        
        # Determine base URL (prefer frontend origin for multi-domain)
        origin = request.headers.get("origin")
        # Optionally allow explicit override via query param
        redirect_origin = request.query_params.get("redirect_origin")
        base_url = (redirect_origin or origin or settings.FRONTEND_URL or f"{request.url.scheme}://{request.url.netloc}").rstrip('/')
        
        # Create checkout session (tag with user id for verification)
        session = StripeService.create_checkout_session(
            customer_id=current_user.stripe_customer_id,
            price_id=settings.STRIPE_PRICE_ID,
            success_url=f"{base_url}/premium/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/premium",
            client_reference_id=str(current_user.id),
            metadata={"user_id": str(current_user.id), "username": current_user.username}
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
        subscription = None
        if current_user.stripe_subscription_id:
            subscription = StripeService.get_subscription(current_user.stripe_subscription_id)
        elif current_user.stripe_customer_id:
            # Try to infer active subscription if missing locally
            subscription = StripeService.find_active_subscription_for_customer(current_user.stripe_customer_id)
            if subscription:
                status["stripe_subscription_id"] = subscription.get("id")

        if subscription:
            status.update({
                "subscription_status": subscription.get("status"),
                "current_period_end": subscription.get("current_period_end"),
                "cancel_at_period_end": subscription.get("cancel_at_period_end")
            })
        
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting subscription status: {str(e)}")

@router.get("/checkout-success")
async def checkout_success(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify checkout session post-redirect and update premium immediately."""
    try:
        session = StripeService.get_checkout_session(session_id)
        if not session:
            raise HTTPException(status_code=400, detail="Invalid checkout session")

        # Validate that this session belongs to this user via customer match when possible
        # session.customer can be string or object depending on expansion; we didn't expand
        sess_customer = session.get("customer")
        # Enforce user linkage via client_reference_id
        client_ref = session.get("client_reference_id")
        if not client_ref or client_ref != str(current_user.id):
            raise HTTPException(status_code=403, detail="Session not linked to this user")

        if current_user.stripe_customer_id and sess_customer and sess_customer != current_user.stripe_customer_id:
            # Mismatch: do not update someone else’s record
            raise HTTPException(status_code=403, detail="Session does not belong to the current user")

        # If user didn't have a customer saved (edge case), store it
        if not current_user.stripe_customer_id and sess_customer:
            current_user.stripe_customer_id = sess_customer
            db.commit()

        # Additional safety checks: session must be subscription mode and completed/paid
        if session.get("mode") != "subscription":
            raise HTTPException(status_code=400, detail="Invalid session mode")
        if session.get("status") != "complete" and session.get("payment_status") != "paid":
            # Not completed/paid yet
            return {"message": "Payment not completed yet; please wait a moment."}

        # If a subscription was created, retrieve it and update user immediately
        subscription_id = session.get("subscription")
        if subscription_id:
            sub = StripeService.get_subscription(subscription_id)
            if sub:
                current_user.stripe_subscription_id = sub.get("id")
                # Update premium flags from subscription data
                StripeService.update_user_premium_status(db, current_user, sub)
                return {"message": "Premium activated", "subscription_status": sub.get("status")}

        # If no subscription present (e.g., async), fall back to success message; webhooks will update soon
        return {"message": "Payment verified; premium will activate shortly if not already."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying checkout: {str(e)}")

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel the user's subscription (at period end)"""
    try:
        # Ensure we have a subscription id; if missing, attempt to resolve via Stripe
        subscription_id = current_user.stripe_subscription_id
        if not subscription_id:
            if not current_user.stripe_customer_id:
                raise HTTPException(status_code=400, detail="No customer or subscription found")
            sub = StripeService.find_active_subscription_for_customer(current_user.stripe_customer_id)
            if not sub:
                raise HTTPException(status_code=400, detail="No active subscription found")
            subscription_id = sub.get("id")
            current_user.stripe_subscription_id = subscription_id
            db.commit()
        # Retrieve current subscription to determine state
        current_sub = StripeService.get_subscription(subscription_id)
        if not current_sub:
            # If switching from test to live (or vice versa), the local DB may have stale Stripe IDs
            # Treat this as already-canceled from Stripe's perspective and clean up local state
            current_user.stripe_subscription_id = None
            db.commit()
            return {"message": "No matching subscription in current Stripe environment; local record cleared."}

        status = current_sub.get("status")
        cancel_at_period_end = current_sub.get("cancel_at_period_end")

        # Idempotency: if already canceled or set to cancel at period end, acknowledge success
        if status in ("canceled",) or cancel_at_period_end:
            return {"message": "Subscription already scheduled to cancel or canceled"}

        # Try to schedule cancellation at period end
        scheduled = StripeService.cancel_subscription(subscription_id)
        if scheduled:
            return {"message": "Subscription will be canceled at the end of the current period"}

        # If scheduling failed (e.g., incomplete/trialing states), attempt immediate cancellation
        immediate = StripeService.cancel_subscription_immediately(subscription_id)
        if immediate:
            return {"message": "Subscription canceled immediately"}

        # If both attempts failed
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Stripe customer portal URL for billing management"""
    try:
        # Ensure Stripe secret is configured
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(status_code=500, detail="Stripe is not configured on the server")

        # Ensure we have a Stripe customer ID; create if missing
        created_customer = False
        if not current_user.stripe_customer_id:
            customer = StripeService.create_customer(current_user)
            if not customer:
                raise HTTPException(status_code=500, detail="Failed to create customer")
            # Persist the new customer id
            current_user.stripe_customer_id = customer["id"]
            created_customer = True
            db.commit()
        
        origin = request.headers.get("origin")
        redirect_origin = request.query_params.get("redirect_origin")
        base_url = (redirect_origin or origin or settings.FRONTEND_URL or f"{request.url.scheme}://{request.url.netloc}").rstrip('/')
        portal_url = StripeService.get_customer_portal_url(
            customer_id=current_user.stripe_customer_id,
            return_url=f"{base_url}/settings"
        )
        
        # If creating a portal session failed (e.g., stale/invalid customer), try once to recreate the customer and retry
        if not portal_url and not created_customer:
            try:
                print(f"Customer portal 400? return_url={base_url}/settings, customer={current_user.stripe_customer_id}")
            except Exception:
                pass
            customer = StripeService.create_customer(current_user)
            if customer:
                current_user.stripe_customer_id = customer["id"]
                db.commit()
                portal_url = StripeService.get_customer_portal_url(
                    customer_id=current_user.stripe_customer_id,
                    return_url=f"{base_url}/settings"
                )
        
        if not portal_url:
            try:
                print(f"Customer portal failed for customer={current_user.stripe_customer_id}, return_url={base_url}/settings")
            except Exception:
                pass
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
        # Be tolerant of header casing
        sig_header = request.headers.get("stripe-signature") or request.headers.get("Stripe-Signature")
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
        
        event = StripeService.process_webhook_event(payload, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature or payload")
        
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
        elif event["type"] == "checkout.session.completed":
            print("Handling checkout session completed")
            await handle_checkout_completed(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_failed":
            print("Handling payment failed")
            await handle_payment_failed(event["data"]["object"], db)
        else:
            print(f"Unhandled webhook event type: {event['type']}")
        
        return {"status": "success"}
    
    except Exception as e:
        err_name = type(e).__name__
        err_msg = str(e) or repr(e)
        print(f"Webhook error [{err_name}]: {err_msg}")
        raise HTTPException(status_code=400, detail=f"Webhook error [{err_name}]: {err_msg}")

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

async def handle_checkout_completed(session: Dict[str, Any], db: Session):
    """Handle checkout.session.completed webhook to set premium immediately."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    print(f"Checkout completed - Customer: {customer_id}, Subscription: {subscription_id}")
    if not (customer_id and subscription_id):
        return
    sub = StripeService.get_subscription(subscription_id)
    if not sub:
        return
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.stripe_subscription_id = subscription_id
        StripeService.update_user_premium_status(db, user, sub)