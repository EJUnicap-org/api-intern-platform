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
        
        # 1. Título do Projeto
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Projeto: {project_title}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # 2. Métricas Globais
        metricas = pert_data.get("metricas_globais", {})
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 8, f"Tempo Enxuto (Caminho Crítico): {metricas.get('tempo_enxuto_horas', 0)} horas", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Margem de Segurança (Variância): {metricas.get('margem_seguranca_horas', 0)} horas", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Prazo Final Seguro: {metricas.get('prazo_final_seguro_horas', 0)} horas", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # 3. Caminho Crítico Destacado
        critico_str = " -> ".join(pert_data.get("caminho_critico", []))
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, f"Gargalo do Projeto: {critico_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # 4. Tabela de Tarefas - Cabeçalho
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(15, 10, "ID", border=1, align="C")
        pdf.cell(85, 10, "Descrição", border=1, align="C")
        pdf.cell(30, 10, "Duração (h)", border=1, align="C")
        pdf.cell(30, 10, "Folga (h)", border=1, align="C")
        pdf.cell(30, 10, "Status", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # 5. Tabela de Tarefas - Linhas dinâmicas
        pdf.set_font("helvetica", "", 10)
        detalhes = pert_data.get("detalhes_tarefas", {})
        
        for task_id, info in detalhes.items():
            desc = str(info.get("desc", ""))[:40] 
            duracao = str(info.get("Te", 0))
            folga = str(info.get("folga_horas", 0))
            status = "GARGALO" if info.get("is_critico") else "OK"
            
            pdf.cell(15, 10, task_id, border=1, align="C")
            pdf.cell(85, 10, desc, border=1, align="L")
            pdf.cell(30, 10, duracao, border=1, align="C")
            pdf.cell(30, 10, folga, border=1, align="C")
            pdf.cell(30, 10, status, border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # O FPDF2 permite retornar o buffer diretamente como bytearray
        return bytes(pdf.output())