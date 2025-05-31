from flask import send_file, make_response
from io import BytesIO
import csv
from fpdf import FPDF

# Dados para o gráfico
def gerar_dados_grafico(registros):
    return [
        {
            "data": r["data_trabalho"],
            "normais": r.get("horas_normais", 0),
            "extras": r.get("horas_extras", 0),
            "noturnas": r.get("adicional_noturno", 0),
        }
        for r in registros
    ]

@relatorios_bp.route("/exportar_pdf", methods=["POST"])
def exportar_pdf():
    funcionario_id = request.form.get("funcionario_id", "")
    mes_ano = request.form.get("mes", "")

    query = supabase.table("registros_horas").select("*")
    if funcionario_id:
        query = query.eq("funcionario_id", funcionario_id)
    if mes_ano:
        ano, mes = mes_ano.split("-")
        query = query.gte("data_trabalho", f"{ano}-{mes}-01")
        query = query.lte("data_trabalho", f"{ano}-{mes}-31")

    registros = query.order("data_trabalho").execute().data

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="Relatório de Horas Trabalhadas", ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    for r in registros:
        linha = f"{r['data_trabalho']} - {r['hora_entrada']} > {r['hora_saida']} | Normais: {r.get('horas_normais', 0)} | Extras: {r.get('horas_extras', 0)} | Noturno: {r.get('adicional_noturno', 0)}"
        pdf.cell(200, 8, txt=linha, ln=True)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="relatorio.pdf", mimetype="application/pdf")

@relatorios_bp.route('/', methods=['GET'])
def relatorios():
    filtro_id = request.args.get("funcionario_id", "")
    mes_ano = request.args.get("mes", datetime.now().strftime("%Y-%m"))

    query = supabase.table("registros_horas").select("*")
    if filtro_id:
        query = query.eq("funcionario_id", filtro_id)
    if mes_ano:
        ano, mes = mes_ano.split("-")
        query = query.gte("data_trabalho", f"{ano}-{mes}-01")
        query = query.lte("data_trabalho", f"{ano}-{mes}-31")

    registros = query.order("data_trabalho").execute().data
    totais = somar_horas(registros)
    grafico_data = gerar_dados_grafico(registros)

    funcionarios = supabase.table("funcionarios").select("*").eq("ativo", True).order("nome").execute().data

    return render_template("relatorios.html",
                           registros=registros,
                           totais=totais,
                           funcionarios=funcionarios,
                           filtro_id=filtro_id,
                           mes_ano=mes_ano,
                           grafico_data=grafico_data)
