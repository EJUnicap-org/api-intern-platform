import networkx
import math
from typing import Dict, Any

def calc_grafo_pert(data_tasks: Dict[str, Any]) -> Dict[str, Any]:
    grafo = nx.DiGraph()
    result_task = {}
    
    grafo.add_node('Start')
    grafo.add_node('End')
    
    for id_task, datas in data_tasks.items():
        te = (datas.O + 4 * datas.M + datas.P) / 6
        var = ((datas.P - datas.O) / 6) ** 2
        
        result_task[id_task] = {
            "desc": datas.desc,
            "Te": round(te, 2),
            "Var": round(var, 2)
        }
        grafo.add_node(id_task)
    
    for id_task, datas in data_tasks.items():
        weight_task = result_task[id_task]['Te']
        
        if not datas.pred:
            grafo.add_edge('Start', id_task, weight = weight_task)
        else:
            for pred in datas.pred:
                if pred not in data_tasks:
                    raise ValueError(f"Predecessora '{pred}' da tarefa '{id_task}' não existe no projeto.")
                grafo.add_edge(pred, id_task, weight =  weight_task)
    nos_folha = [node for node, out_degree in grafo.out_degree() if out_degree == 0 and node != 'End']
    
    if not nos_folha:
        raise ValueError("O projeto não possui um fim claro ou contém uma dependência circular isolada.")

    for folha in nos_folha:
        grafo.add_edge(folha, 'End', weight=0)
        
    try:
        caminho_bruto = nx.dag_longest_path(grafo, weight='weight')
    except nx.NetworkXUnfeasible:
        try:
            cycle = nx.find_cycle(grafo, orientation ='directed')
            on_loop_task = " -> ".join([edge[0] for edge in cycle])
            raise ValueError(f"Dependência Circular detectada nas tarefas: {on_loop_task}. Corrija o planejamento.")
        except nx.NetworkXNoCycle:
            raise ValueError("Erro estrutural desconhecido no grafo do projeto.")
    critic_path = [no for no in caminho_bruto if no not in ('start', 'End')]
    
    project_time = sum(task_result[t]['Te'] for t in critic_path)
    variance_project = sum(result_task[t]['Var'] for t in critic_path)
    default_diversion = math.sqrt(variance_project)
    secure_time = project_time + default_diversion
    
    return {
        "metricas_globais": {
            "tempo_enxuto_horas": round(project_time, 2),
            "margem_seguranca_horas": round(default_diversion, 2),
            "prazo_final_seguro_horas": math.ceil(secure_time)
        },
        "caminho_critico": critic_path,
        "detalhes_tarefas": result_task
    }