import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.reimbursement import Reimbursement, StatusRefundEnum
from ..schemas.reimbursement import ReimbursementCreate

logger = logging.getLogger(__name__)

class ReimbursementService:
    
    @staticmethod
    async def create_reimbursement(
        data: ReimbursementCreate, user_id: int, db: AsyncSession
    ) -> Reimbursement:
        """
        Cria o registro financeiro apontando para a URL que já foi salva na nuvem.
        """
        new_reimb = Reimbursement(
            title=data.title,
            description=data.description,
            category=data.category,
            value=data.value,
            pix_key=data.pix_key,
            receipt=data.file_url,  # Aqui nós salvamos a URL limpa que o front-end mandou
            status=StatusRefundEnum.AWAITING,
            user_id=user_id
        )
        
        db.add(new_reimb)
        await db.commit()
        await db.refresh(new_reimb)

        return new_reimb