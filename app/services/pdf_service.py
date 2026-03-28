import logging
from fpdf import FPDF

logger = logging.getLogger(__name__)

# Classe customizada para ter Cabeçalho e Rodapé automáticos em todas as páginas
class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        # O FPDF2 exige new_x e new_y para controlar a quebra de linha
        self.cell(0, 10, "Diagnóstico PERT/CPM - EJ Unicap", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

class PdfService:
    """
    Serviço puro de CPU para renderização de PDFs.
    """
    
    @staticmethod
    def build_pert_pdf(project_title: str, pert_data: dict) -> bytes:
        pdf = PDF()
        pdf.add_page()
        
        # Isolamento de Escopos
        pert_classico = pert_data.get("pert_classico", {})
        ccpm = pert_data.get("corrente_critica", {})
        
        # 1. Título do Projeto
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Projeto: {project_title}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # 2. Visão PERT (Conservadora)
        metricas_pert = pert_classico.get("metricas_globais", {})
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, "Visão PERT Clássico (Estatística)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 6, f"Tempo Enxuto (Gargalo): {metricas_pert.get('tempo_enxuto_horas', 0)}h", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Prazo Final Seguro (Com Margem): {metricas_pert.get('prazo_final_seguro_horas', 0)}h", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
        # 3. Visão Corrente Crítica (Agressiva)
        metricas_ccpm = ccpm.get("metricas_ccpm", {})
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, "Visão Corrente Crítica (Gestão por Pulmão)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 6, f"Meta Agressiva de Entrega: {metricas_ccpm.get('tempo_agressivo_projeto_horas', 0)}h", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Pulmão de Projeto (Buffer): {metricas_ccpm.get('project_buffer_horas', 0)}h", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        
        # 4. Caminho Crítico
        critico_str = " -> ".join(pert_classico.get("caminho_critico", []))
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 8, f"Cadeia Principal: {critico_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
        # 5. Tabela de Tarefas - Cabeçalho
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(10, 8, "ID", border=1, align="C")
        pdf.cell(70, 8, "Descrição", border=1, align="C")
        pdf.cell(25, 8, "Tempo PERT", border=1, align="C")
        pdf.cell(25, 8, "Tempo CCPM", border=1, align="C")
        pdf.cell(30, 8, "Feeding Buffer", border=1, align="C")
        pdf.cell(30, 8, "Status", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # 6. Tabela de Tarefas - Linhas
        pdf.set_font("helvetica", "", 9)
        detalhes = pert_classico.get("detalhes_tarefas", {})
        feeding_buffers = ccpm.get("feeding_buffers", {})
        tarefas_cortadas = ccpm.get("tarefas_cortadas", {})
        
        for task_id, info in detalhes.items():
            desc = str(info.get("desc", ""))[:35] 
            tempo_pert = f"{info.get('Te', 0)}h"
            tempo_ccpm = f"{tarefas_cortadas.get(task_id, {}).get('tempo_ccpm', 0)}h"
            
            # Se a tarefa tem Feeding Buffer, nós mostramos. Se não, é o Gargalo.
            fb_val = feeding_buffers.get(task_id)
            buffer_str = f"{fb_val}h" if fb_val else "-"
            status = "CADEIA CRÍTICA" if info.get("is_critico") else "ALIMENTADORA"
            
            pdf.cell(10, 8, task_id, border=1, align="C")
            pdf.cell(70, 8, desc, border=1, align="L")
            pdf.cell(25, 8, tempo_pert, border=1, align="C")
            pdf.cell(25, 8, tempo_ccpm, border=1, align="C")
            pdf.cell(30, 8, buffer_str, border=1, align="C")
            pdf.cell(30, 8, status, border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        
        return bytes(pdf.output())