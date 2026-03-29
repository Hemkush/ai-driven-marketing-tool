from fastapi import APIRouter

from app.api.mvp.system import router as system_router
from app.api.mvp.questionnaire import router as questionnaire_router
from app.api.mvp.analysis import router as analysis_router
from app.api.mvp.positioning import router as positioning_router
from app.api.mvp.research import router as research_router
from app.api.mvp.personas import router as personas_router
from app.api.mvp.strategy import router as strategy_router
from app.api.mvp.content import router as content_router

router = APIRouter()

router.include_router(system_router)
router.include_router(questionnaire_router)
router.include_router(analysis_router)
router.include_router(positioning_router)
router.include_router(research_router)
router.include_router(personas_router)
router.include_router(strategy_router)
router.include_router(content_router)
