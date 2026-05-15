import streamlit as st
import streamlit.components.v1 as components

def render_card(
    titulo,
    valor,
    subtitulo="",
    cor="#38BDF8",
    title_size="11px",
    value_size="22px",
    subtitle_size="10px",
    card_height=90
):

    # Evita recorte do raio inferior dentro do iframe do Streamlit.
    altura_card = max(int(card_height) - 6, 40)

    html = f"""
    <div style="
        background:#1E293B;
        padding:8px 10px;
        border-radius:10px;
        text-align:center;
        box-shadow:0 2px 5px rgba(0,0,0,0.32);
        height:{altura_card}px;
        min-height:{altura_card}px;
        box-sizing:border-box;
        display:flex;
        flex-direction:column;
        justify-content:center;
        overflow:hidden;
    ">

        <div style="
            font-size:{title_size};
            color:#94A3B8;
            display:flex;
            justify-content:center;
            align-items:center;
            gap:6px;
        ">

            {titulo}

        </div>

        <div style="
            font-size:{value_size};
            font-weight:700;
            color:white;
            margin-top:10px;
        ">
            {valor}
        </div>

        <div style="
            font-size:{subtitle_size};
            color:#CBD5E1;
            margin-top:2px;
        ">
            {subtitulo if subtitulo else "&nbsp;"}
        </div>

    </div>
    """

    components.html(html, height=card_height + 8)