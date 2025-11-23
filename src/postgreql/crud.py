from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Claim


async def create_claim(db: AsyncSession, claim_id: str, decision: str, reason: str = None) -> Claim:
    db_claim = Claim(claim_id=claim_id, decision=decision, reason=reason)
    db.add(db_claim)
    await db.commit()
    await db.refresh(db_claim)
    return db_claim


async def get_claim_by_id(db: AsyncSession, claim_id: str) -> Claim:
    result = await db.execute(select(Claim).where(Claim.claim_id == claim_id))
    return result.scalar_one_or_none()


async def get_all_claims(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Claim).offset(skip).limit(limit))
    return result.scalars().all()


async def update_claim(db: AsyncSession, claim_id: str, decision: str, reason: str = None) -> Claim:
    db_claim = await get_claim_by_id(db, claim_id)
    if db_claim:
        db_claim.decision = decision
        if reason is not None:
            db_claim.reason = reason
        await db.commit()
        await db.refresh(db_claim)
    return db_claim


async def delete_claim(db: AsyncSession, claim_id: str) -> bool:
    db_claim = await get_claim_by_id(db, claim_id)
    if db_claim:
        await db.delete(db_claim)
        await db.commit()
        return True
    return False


async def get_claims_by_decision(db: AsyncSession, decision: str, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Claim).where(Claim.decision == decision).offset(skip).limit(limit)
    )
    return result.scalars().all()
