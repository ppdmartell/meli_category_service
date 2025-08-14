from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone

from app.infrastructure.database import get_session
from app.infrastructure.models.meli_access_token import MeliAccessToken

class AccessTokenRepository:
    def get_access_token(self) -> str | None:
        """Retrieve only the access_token from the stored row."""
        try:
            with get_session() as session:
                statement = select(MeliAccessToken.access_token)
                access_token = session.execute(statement).scalar_one_or_none()
                return access_token
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to retrieve access_token from the database: {e}")


    def check_convert(self, date):
        if isinstance(date, datetime):
            return date
        else:
            return datetime.fromisoformat(date)


    def save_access_token(self, token_data: dict) -> bool:
        """
        Save or update the whole access token info from the JSON.
        token_data: dict response from meli_auth_service
        """
        # Convert strings to datetime if needed
        created_at = self.check_convert(token_data["created_at"])
        access_token_expires_at = self.check_convert(token_data["access_token_expires_at"])
        refresh_token_expires_at = self.check_convert(token_data["refresh_token_expires_at"])

        new_access_token = MeliAccessToken(
            singleton_key=1,
            access_token=token_data["access_token"],
            created_at=created_at,
            expires_in_seconds=token_data["expires_in_seconds"],
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=refresh_token_expires_at,
        )

        try:
            with get_session() as session:
                # Delete the old token
                session.query(MeliAccessToken).delete()
                session.add(new_access_token)
                session.commit()
            return True
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to save the access_token: {e}")
            return False


    def get_access_token_full_row(self) -> MeliAccessToken | None:
        """Retrieve the full token row (record)."""
        try:
            with get_session() as session:
                statement = select(MeliAccessToken)
                return session.execute(statement).scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to retrieve the access_token full row (record): e")
    

    def is_existing_access_token_expired(self, grace_seconds: int = 120) -> bool:
        """
        Check if the stored access token is expired.
        grace_seconds: token is considered expired this many seconds before actual expiration.
        """
        access_token_record = self.get_access_token_full_row() # will always return a row
        now = datetime.now(timezone.utc)
        expire_time_with_grace = access_token_record.access_token_expires_at.replace(tzinfo=timezone.utc) - timedelta(seconds=grace_seconds)
        return now >= expire_time_with_grace
