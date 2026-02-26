"""Questionnaire API — get answers, submit from web."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.database import async_session, User, QuestionnaireAnswer
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


@router.get("/answers")
async def get_answers(user: User = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(QuestionnaireAnswer).where(QuestionnaireAnswer.user_id == user.id)
        )
        answers = result.scalars().all()

    return [
        {
            "module": a.module,
            "question_key": a.question_key,
            "answer_value": a.answer_value,
        }
        for a in answers
    ]


class AnswerSubmit(BaseModel):
    module: str
    question_key: str
    answer_value: str


@router.post("/answers")
async def submit_answer(req: AnswerSubmit, user: User = Depends(get_current_user)):
    async with async_session() as session:
        qa = QuestionnaireAnswer(
            user_id=user.id,
            module=req.module,
            question_key=req.question_key,
            answer_value=req.answer_value,
        )
        session.add(qa)
        await session.commit()
    return {"status": "ok"}
