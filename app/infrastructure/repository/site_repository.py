from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone

from app.infrastructure.database import get_session
from app.infrastructure.models.meli_site import MeliSite

class SiteRepository:
    def get_sites(self) -> dict | None:
        """
        Retrieve all the sites from the database.
        """
        try:
            with get_session() as session:
                sites = session.scalars(select(MeliSite)).all()
                return [site.to_dict() for site in sites]
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to retrieve the sites: {e}")

    
    def save_sites(self, sites: list[dict]):
        """
        Insert or update multiple MeLi sites from a list of dicts.
        Each dict should have keys: id, name, default_currency_id
        """
        try:
            with get_session() as session:
                # Delete all the existing rows, since new one and full will arrive
                session.execute(delete(MeliSite))
                now = datetime.now(timezone.utc)

                # Prepare new site objects
                refreshed_sites = [
                    MeliSite(
                        default_currency_id=site.get("default_currency_id"),
                        id=site.get("id"),
                        name=site.get("name"),
                        updated_at=now,
                    )
                    for site in sites
                ]

                # Bulk insert
                session.bulk_save_objects(refreshed_sites)
                session.commit()
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to persist the sites: {e}")
