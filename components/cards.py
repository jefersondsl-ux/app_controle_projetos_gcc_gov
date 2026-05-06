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

    html = f"""
    <div style="
        background:#1E293B;
        padding:8px 10px;
        border-radius:10px;
        text-align:center;
        box-shadow:0 2px 5px rgba(0,0,0,0.32);
        height:{card_height}px;
        min-height:{card_height}px;
        box-sizing:border-box;
        display:flex;
        flex-direction:column;
        justify-content:center;
    ">

        <div style="
            font-size:{title_size};
            color:#94A3B8;
            display:flex;
            justify-content:center;
            align-items:center;
            gap:6px;
        ">

            <span style="
                width:8px;
                height:8px;
                background:{cor};
                border-radius:50%;
                display:inline-block;
            "></span>

            {titulo}

        </div>

        <div style="
            font-size:{value_size};
            font-weight:700;
            color:white;
            margin-top:4px;
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

    components.html(html, height=card_height)