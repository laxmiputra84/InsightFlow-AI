from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.agent import AgentModel


class AgentService:
    @staticmethod
    def get_all_agents(db: Session) -> List[AgentModel]:
        """
        Retrieves all registered Autonomous BI agents and their current statuses.
        """
        return db.query(AgentModel).all()

    @staticmethod
    def get_agent_by_id(db: Session, agent_id: str) -> Optional[AgentModel]:
        """
        Retrieves a single agent by unique identifier.
        """
        return db.query(AgentModel).filter(AgentModel.id == agent_id).first()
