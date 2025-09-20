from authlib.integrations.starlette_client import OAuth
from fastapi import Request, HTTPException
from app.core.config import settings
import httpx

oauth = OAuth()

# Register OAuth providers
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

oauth.register(
    name='discord',
    client_id=settings.DISCORD_CLIENT_ID,
    client_secret=settings.DISCORD_CLIENT_SECRET,
    access_token_url='https://discord.com/api/oauth2/token',
    access_token_params=None,
    authorize_url='https://discord.com/api/oauth2/authorize',
    authorize_params=None,
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify email'},
)

async def get_google_user_info(token: str) -> dict:
    """Get user info from Google using access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v1/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        return response.json()

async def get_github_user_info(token: str) -> dict:
    """Get user info from GitHub using access token."""
    async with httpx.AsyncClient() as client:
        # Get user info
        user_response = await client.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {token}'}
        )
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from GitHub")

        user_data = user_response.json()

        # Get user email if not public
        if not user_data.get('email'):
            email_response = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {token}'}
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                primary_email = next((email['email'] for email in emails if email['primary']), None)
                if primary_email:
                    user_data['email'] = primary_email

        return user_data

async def get_discord_user_info(token: str) -> dict:
    """Get user info from Discord using access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://discord.com/api/v10/users/@me',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Discord")
        return response.json()