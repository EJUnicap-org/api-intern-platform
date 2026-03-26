from pydantic import BaseModel, Field, model_validator
from typing import List, Dict

class TaskInput(BaseModel):
    desc: str = Field(..., min_length=1, max_length=500)
    pred: List[str]
    O: float
    M: float
    P: float

    @model_validator(mode='after')
    def validar_estimativas_pert(self) -> 'TaskInput':
        if not (self.O <= self.M <= self.P):
            raise ValueError(
                f"Erro lógico na tarefa '{self.desc}': "
                f"As estimativas devem respeitar a regra Otimista ({self.O}) <= "
                f"Mais Provável ({self.M}) <= Pessimista ({self.P})."
            )
        return self

class ProjetoInput(BaseModel):
    tasks: Dict[str, TaskInput]