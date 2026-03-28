import networkx as nx
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
            grafo.add_edge('Start', id_task, weight=weight_task)
        else:
            for pred in datas.pred:
                if pred not in data_tasks:
                    raise ValueError(f"Predecessora '{pred}' da tarefa '{id_task}' não existe no projeto.")
                grafo.add_edge(pred, id_task, weight=weight_task)
                
    nos_folha = [node for node, out_degree in grafo.out_degree() if out_degree == 0 and node != 'End']
    
    if not nos_folha:
        raise ValueError("O projeto não possui um fim claro ou contém uma dependência circular isolada.")

    for folha in nos_folha:
        grafo.add_edge(folha, 'End', weight=0)
        
    try:
        caminho_bruto = nx.dag_longest_path(grafo, weight='weight')
        
        ef = {node: 0.0 for node in grafo.nodes()}
        for node in nx.topological_sort(grafo):
            for neighbors in grafo.successors(node):
                peso = grafo.edges[node, neighbors].get('weight', 0.0)
                if ef[node] + peso > ef[neighbors]:
                    ef[neighbors] = ef[node] + peso
                    
        total_time = ef['End']
        
        lf = {node: total_time for node in grafo.nodes()}
        for node in reversed(list(nx.topological_sort(grafo))):
            for predecessor in grafo.predecessors(node):
                peso = grafo.edges[predecessor, node].get('weight', 0.0)
                if lf[node] - peso < lf[predecessor]:
                    lf[predecessor] = lf[node] - peso
                    
        risk_path = []
        for id_task in data_tasks.keys(): 
            free_time = round(lf[id_task] - ef[id_task], 2)
            is_critico = free_time <= 0.01
            
            result_task[id_task]["folga_horas"] = free_time
            result_task[id_task]["is_critico"] = is_critico
            
            if is_critico:
                risk_path.append(id_task)

    except nx.NetworkXUnfeasible:
        try:
            cycle = nx.find_cycle(grafo, orientation='directed')
            on_loop_task = " -> ".join([edge[0] for edge in cycle])
            raise ValueError(f"Dependência Circular detectada nas tarefas: {on_loop_task}. Corrija o planejamento.")
        except nx.NetworkXNoCycle:
            raise ValueError("Erro estrutural desconhecido no grafo do projeto.")
            
    project_time = total_time 
    
    caminho_limpo = [no for no in caminho_bruto if no not in ('Start', 'End')]
    variance_project = sum(result_task[t]['Var'] for t in caminho_limpo)
    
    default_diversion = math.sqrt(variance_project)
    secure_time = project_time + default_diversion
    
    project_buffer = round(project_time / 2, 2)
    tempo_agressivo = round(project_time - project_buffer, 2)
    prazo_protegido = round(tempo_agressivo + project_buffer, 2)
    
    feeding_buffers = {}
    tarefas_cortadas = {}
    
    for id_task in data_tasks.keys():
        tempo_original = result_task[id_task]['Te']
        tempo_cortado  = round(tempo_original / 2, 2)
        tarefas_cortadas[id_task] = {"tempo_ccpm": tempo_cortado}
        
        if id_task not in risk_path:
            feeding_buffers[id_task] = tempo_cortado

    
    return {
        "pert_classico": {
            "metricas_globais": {
                "tempo_enxuto_horas": round(project_time, 2),
                "margem_seguranca_horas": round(default_diversion, 2),
                "prazo_final_seguro_horas": math.ceil(secure_time)
            },
            "caminho_critico": risk_path,
            "detalhes_tarefas": result_task
        },
        "corrente_critica": {
            "metricas_ccpm": {
                "tempo_agressivo_projeto_horas": tempo_agressivo,
                "project_buffer_horas": project_buffer,
                "prazo_final_protegido_horas": prazo_protegido
            },
            "feeding_buffers": feeding_buffers,
            "tarefas_cortadas": tarefas_cortadas
        }
    }
