import logging
from fpdf import FPDF 
import json
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditoriaPDF(FPDF):
    """
    Subclasse da fpdf2 para controle autônomo de Header e Footer do Relatório de Auditoria.
    """
    def header(self):
        # Fonte Padrão (helvetica já vem embutida no fpdf2)
        self.set_font("helvetica", "B", 14)
        # Cor Primária da EJ Unicap (Azul Escuro / Indigo)
        self.set_text_color(17, 34, 85)
        # Cabeçalho baseado na documentação
        self.cell(0, 10, "Relatório de Auditoria Semestral - EJ Unicap", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("helvetica", "I", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Módulo: Quadro de Avisos & Chamados Formais", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        # Posicionamento a 1.5cm do fundo
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        # O FPDF2 usa {nb} para o total de páginas automaticamente quando chamado alias_nb_pages
        self.cell(0, 10, f"EJ Unicap - Governança de Dados | Página {self.page_no()}/{{nb}}", align="C")


class TicketAuditPdfService:
    """
    Serviço que gera o arquivo binário do PDF a partir dos dados extraídos do PostgreSQL/SQLite.
    """

    @staticmethod
    def build_audit_pdf(periodo_str: str, metricas: dict, estado_chamados: list, membros_engajados: list, hash_referencia: str) -> bytes:
        """
        Recebe os dados brutos e renderiza o PDF. Retorna a string de bytes do documento final.
        """
        pdf = AuditoriaPDF()
        # Opcional para habilitar a tag {nb}
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # --- BLOCO 1: INTRODUÇÃO E COMPLIANCE ---
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"Período Analisado: {periodo_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        
        texto_compliance = (
            "Este documento constitui o artefato oficial de auditoria estática da infraestrutura de "
            "comunicação da EJ Unicap. Conforme as políticas corporativas de retenção de dados, "
            "os registros ativos foram consolidados e expurgados do banco de dados transacional "
            "para preservação de performance e espaço em disco."
        )
        # Multi_cell lida com quebra de linhas automáticas no fpdf2
        pdf.multi_cell(0, 6, texto_compliance)
        pdf.ln(8)
        
        # --- BLOCO 2: MÉTRICAS GLOBAIS DE VOLUME ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(17, 34, 85)
        pdf.cell(0, 8, "Métricas Consolidadas de Volume", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Formatação de "Cards" numa tabela de linha única
        pdf.set_font("helvetica", "B", 8)
        pdf.set_fill_color(240, 240, 245)
        pdf.set_text_color(0, 0, 0)
        # Largura das colunas (4 colunas dividindo 190mm da página A4 com margens padrão)
        col_w = 47.5 
        
        # Linha de Cabeçalho da Tabela
        pdf.cell(col_w, 8, "MENSAGENS BÁSICAS", border=1, align="C", fill=True)
        pdf.cell(col_w, 8, "CHAMADOS FORMAIS", border=1, align="C", fill=True)
        pdf.cell(col_w, 8, "USUÁRIOS ENGAJADOS", border=1, align="C", fill=True)
        pdf.cell(col_w, 8, "MÍDIAS NO R2", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        # Linha de Dados da Tabela
        pdf.set_font("helvetica", "", 10)
        pdf.cell(col_w, 8, str(metricas.get("mensagens", 0)), border=1, align="C")
        pdf.cell(col_w, 8, str(metricas.get("chamados", 0)), border=1, align="C")
        pdf.cell(col_w, 8, str(metricas.get("usuarios", 0)), border=1, align="C")
        pdf.cell(col_w, 8, str(metricas.get("midias", 0)), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        
        # --- BLOCO 3: COMPLIANCE E RESOLUÇÕES ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(17, 34, 85)
        pdf.cell(0, 8, "Eficiência Operacional (Compliance)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Tabela de Eficiência
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 8, "Estado do Chamado", border=1, align="C", fill=True)
        pdf.cell(40, 8, "Volume Bruto", border=1, align="C", fill=True)
        pdf.cell(60, 8, "Percentual de Representação", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 10)
        for estado in estado_chamados:
            pdf.cell(60, 8, str(estado.get("status", "N/A")), border=1, align="L")
            pdf.cell(40, 8, str(estado.get("volume", 0)), border=1, align="C")
            pdf.cell(60, 8, str(estado.get("percentual", "0%")), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        
        # --- BLOCO 4: MEMBROS ENGAJADOS ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(17, 34, 85)
        pdf.cell(0, 8, "Membros de Maior Volumetria", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Tabela de Membros
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(70, 8, "Nome do Colaborador", border=1, align="C", fill=True)
        pdf.cell(60, 8, "Cargo / Núcleo", border=1, align="C", fill=True)
        pdf.cell(50, 8, "Volume de Iterações", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 10)
        for membro in membros_engajados:
            # Corta nomes muito grandes para não quebrar a tabela
            nome = str(membro.get("nome", ""))[:30]
            cargo = str(membro.get("cargo", ""))[:25]
            volume = f"{membro.get('volume', 0)} msgs"
            
            pdf.cell(70, 8, nome, border=1, align="L")
            pdf.cell(60, 8, cargo, border=1, align="C")
            pdf.cell(50, 8, volume, border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(15)
        
        # --- BLOCO FINAL: ASSINATURA DE INTEGRIDADE ---
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(220, 38, 38) # Vermelho Alerta
        
        nota_cripto = (
            "Nota de Integridade Criptográfica: O arquivo de log compactado anexo de codinome "
            "logs_mensagens_backup.zip contém o mapeamento serializado (JSON) de todas as interações. "
            f"O hash SHA-256 da base extraída (Referência: {hash_referencia}) foi registrado no ledger "
            "de governança para fins de não-repúdio."
        )
        pdf.multi_cell(0, 5, nota_cripto)
        
        # Retorna o arquivo formatado em bytes
        return bytes(pdf.output())
import logging
from fpdf import FPDF 
import json
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditoriaPDF(FPDF):
    """
    Subclasse da fpdf2 para controle autônomo de Header e Footer do Relatório de Auditoria.
    """
    def header(self):
        # Fonte Padrão (helvetica já vem embutida no fpdf2)
        self.set_font("helvetica", "B", 14)
        # Cor Primária da EJ Unicap (Azul Escuro / Indigo)
        self.set_text_color(17, 34, 85)
        # Cabeçalho baseado na documentação
        self.cell(0, 10, "Relatório de Auditoria Semestral - EJ Unicap", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("helvetica", "I", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Módulo: Quadro de Avisos & Chamados Formais", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        # Posicionamento a 1.5cm do fundo
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        # O FPDF2 usa {nb} para o total de páginas automaticamente quando chamado alias_nb_pages
        self.cell(0, 10, f"EJ Unicap - Governança de Dados | Página {self.page_no()}/{{nb}}", align="C")


class TicketAuditPdfService:
    """
    Serviço que gera o arquivo binário do PDF a partir dos dados extraídos do PostgreSQL/SQLite.
    """

    @staticmethod
    def build_audit_pdf(periodo_str: str, metricas: dict, estado_chamados: list, membros_engajados: list, hash_referencia: str) -> bytes:
        """
        Recebe os dados brutos e renderiza o PDF. Retorna a string de bytes do documento final.
        """
        pdf = AuditoriaPDF()
        # Opcional para habilitar a tag {nb}
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # --- BLOCO 1: INTRODUÇÃO E COMPLIANCE ---
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"Período Analisado: {periodo_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        
        texto_compliance = (
            "Este documento constitui o artefato oficial de auditoria estática da infraestrutura de "
            "comunicação da EJ Unicap. Conforme as políticas corporativas de retenção de dados, "
            "os registros ativos foram consolidados e expurgados do banco de dados transacional "
            "para preservação de performance e espaço em disco."
        )
        # Multi_cell lida com quebra de linhas automáticas no fpdf2
        pdf.multi_cell(0, 6, texto_compliance)
        pdf.ln(8)
        
        # --- BLOCO 2: MÉTRICAS GLOBAIS DE VOLUME ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(17, 34, 85)
        pdf.cell(0, 8, "Métricas Consolidadas de Volume", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Formatação de "Cards" numa tabela de linha única
        pdf.set_font("helvetica", "B", 8)
        pdf.set_fill_color(240, 240, 245)
        pdf.set_text_color(0, 0, 0)
        # Largura das colunas (4 colunas dividindo 190mm da página A4 com margens padrão)
        col_w = 47.5 
        
        # Linha de Cabeçalho da Tabela
        pdf.cell(col_w, 8, "MENSAGENS BÁSICAS", border=1, align="C", fill=True)
        pdf.cell(col_w, 8, "CHAMADOS FORMAIS", border=1, align="C", fill=True)
        pdf.cell(col_w, 8, "USUÁRIOS ENGAJADOS", border=1, align="C", fill=True)
        pdf.cell(col_w, 8, "MÍDIAS NO R2", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        # Linha de Dados da Tabela
        pdf.set_font("helvetica", "", 10)
        pdf.cell(col_w, 8, str(metricas.get("mensagens", 0)), border=1, align="C")
        pdf.cell(col_w, 8, str(metricas.get("chamados", 0)), border=1, align="C")
        pdf.cell(col_w, 8, str(metricas.get("usuarios", 0)), border=1, align="C")
        pdf.cell(col_w, 8, str(metricas.get("midias", 0)), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        
        # --- BLOCO 3: COMPLIANCE E RESOLUÇÕES ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(17, 34, 85)
        pdf.cell(0, 8, "Eficiência Operacional (Compliance)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Tabela de Eficiência
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 8, "Estado do Chamado", border=1, align="C", fill=True)
        pdf.cell(40, 8, "Volume Bruto", border=1, align="C", fill=True)
        pdf.cell(60, 8, "Percentual de Representação", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 10)
        for estado in estado_chamados:
            pdf.cell(60, 8, str(estado.get("status", "N/A")), border=1, align="L")
            pdf.cell(40, 8, str(estado.get("volume", 0)), border=1, align="C")
            pdf.cell(60, 8, str(estado.get("percentual", "0%")), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        
        # --- BLOCO 4: MEMBROS ENGAJADOS ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(17, 34, 85)
        pdf.cell(0, 8, "Membros de Maior Volumetria", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Tabela de Membros
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(70, 8, "Nome do Colaborador", border=1, align="C", fill=True)
        pdf.cell(60, 8, "Cargo / Núcleo", border=1, align="C", fill=True)
        pdf.cell(50, 8, "Volume de Iterações", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 10)
        for membro in membros_engajados:
            # Corta nomes muito grandes para não quebrar a tabela
            nome = str(membro.get("nome", ""))[:30]
            cargo = str(membro.get("cargo", ""))[:25]
            volume = f"{membro.get('volume', 0)} msgs"
            
            pdf.cell(70, 8, nome, border=1, align="L")
            pdf.cell(60, 8, cargo, border=1, align="C")
            pdf.cell(50, 8, volume, border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(15)
        
        # --- BLOCO FINAL: ASSINATURA DE INTEGRIDADE ---
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(220, 38, 38) # Vermelho Alerta
        
        nota_cripto = (
            "Nota de Integridade Criptográfica: O arquivo de log compactado anexo de codinome "
            "logs_mensagens_backup.zip contém o mapeamento serializado (JSON) de todas as interações. "
            f"O hash SHA-256 da base extraída (Referência: {hash_referencia}) foi registrado no ledger "
            "de governança para fins de não-repúdio."
        )
        pdf.multi_cell(0, 5, nota_cripto)
        
        # Retorna o arquivo formatado em bytes
        return bytes(pdf.output())
