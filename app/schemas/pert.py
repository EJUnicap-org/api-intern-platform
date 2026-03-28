from pydantic import BaseModel, Field, model_validator
from typing import List, Dict

class TaskInput(BaseModel):
    desc: str = Field(..., min_length=1, max_length=500, description="Descrição da tarefa")
    pred: List[str] = Field(default_factory=list, description="Lista de IDs das tarefas predecessoras")
    O: float = Field(..., description="Tempo Otimista (O)")
    M: float = Field(..., description="Tempo Mais Provável (M)")
    P: float = Field(..., description="Tempo Pessimista (P)")

    @model_validator(mode='after')
    def validar_estimativas_pert(self) -> 'TaskInput':
        # A regra de ouro do PERT: Otimista <= Mais Provável <= Pessimista
        if not (self.O <= self.M <= self.P):
            raise ValueError(
                f"Erro lógico na tarefa '{self.desc}': "
                f"As estimativas devem respeitar a regra matemática: Otimista ({self.O}) <= "
                f"Mais Provável ({self.M}) <= Pessimista ({self.P})."
            )
        return self

class ProjetoInput(BaseModel):
    tasks: Dict[str, TaskInput] = Field(
        ..., 
        description="Dicionário de tarefas onde a chave é o ID (ex: 'A', 'B') e o valor contém os dados da tarefa."
    )