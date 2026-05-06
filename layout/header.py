import base64
import streamlit.components.v1 as components


def get_logo():
    with open("assets/logo_claro.png", "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def card_html(titulo, valor, cor_bolinha, subtitulo=""):

    

    return f"""
    <div style="
        background:#1E293B;
        padding:12px 16px;
        border-radius:12px;
        min-width:110px;
        text-align:center;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
    ">

        <div style="
            font-size:11px;
            color:#94A3B8;
            display:flex;
            align-items:center;
            justify-content:center;
            gap:6px;
        ">

            <span style="
                width:9px;
                height:9px;
                background:{cor_bolinha};
                border-radius:50%;
                display:inline-block;
            "></span>

            {titulo}

        </div>

        <div style="
            font-size:22px;
            font-weight:700;
            color:white;
            margin-top:4px;
        ">
            {valor}
        </div>

        <div style="
            font-size:10px;
            color:#CBD5E1;
            margin-top:2px;
        ">
            {subtitulo if subtitulo else "&nbsp;"}
        </div>

    </div>
    """


def render_header(kpis, mostrar_cards=True):

    mostrar_card_parados = False  # 🔥 controle aqui

    logo_base64 = get_logo()

    total = kpis["total_projetos"]

    perc_novos = round((kpis["projetos_novos"] / total) * 100, 1) if total else 0
    perc_parcial = round((kpis["projetos_parcial"] / total) * 100, 1) if total else 0
    perc_concluido = round((kpis["projetos_concluido"] / total) * 100, 1) if total else 0

    html = f"""
    <div style="
        width:100%;
        background-color:#262730;
        padding:25px 18px 14px 18px;
        border-radius:12px;
        margin-bottom:20px;
        box-sizing:border-box;
        font-family:Segoe UI, Arial, sans-serif;
    ">
        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:16px;
            flex-wrap:wrap;
        ">

            <!-- LOGO + TITULO -->
            <div style="
                display:flex;
                align-items:center;
                gap:12px;
                min-width:280px;
            ">
                <img src="data:image/png;base64,{logo_base64}" width="36">

                <div style="
                    font-size:22px;
                    font-weight:700;
                    color:white;
                    white-space:nowrap;
                ">
                    Controle de Projetos GCC GOV
                </div>
            </div>

            {f"""
            <div style="
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                justify-content:flex-end;
                align-items:stretch;
                flex:1;
            ">
                {card_html("Total Projetos", kpis["total_projetos"], "#60A5FA")}
                {card_html("Novo", kpis["projetos_novos"], "#64748B", f"{perc_novos}%")}
                {card_html("Em Andamento", kpis["projetos_parcial"], "#FACC15", f"{perc_parcial}%")}
                {card_html("Concluído", kpis["projetos_concluido"], "#22C55E", f"{perc_concluido}%")}
                {card_html("Projetos Parados", kpis["projetos_parados"], "#EF4444", "+30 dias") if mostrar_card_parados else ""}
                {card_html("Atualização", kpis["ultima_atualizacao"], "#38BDF8")}
            </div>
            """ if mostrar_cards else ""}

        </div>
    </div>
    """

    components.html(html, height=140)