import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# =============================================================================
# SCANNER ETFs & FIIs DE TIJOLO - SETUP EMA 69 (MANUAL DEFINITIVO)
# =============================================================================
st.set_page_config(page_title="SCANNER ETFs & FIIs - ELITE", layout="wide")

# -----------------------------------------------------------------------------
# FUNÇÃO DE INDICADORES
# -----------------------------------------------------------------------------
def calcular_indicadores(df):
    df = df.copy()

    # Estocástico 14,3,3
    stoch = ta.stoch(
        df['High'], df['Low'], df['Close'],
        k=14, d=3, smooth_k=3
    )

    # DMI / ADX 14
    dmi = ta.adx(
        df['High'], df['Low'], df['Close'],
        length=14
    )

    return pd.concat([df, stoch, dmi], axis=1).dropna()

# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL DE ANÁLISE
# -----------------------------------------------------------------------------
def analisar_ativo(ticker):
    try:
        df_diario = yf.download(
            ticker,
            period="2y",
            interval="1d",
            progress=False
        )

        if df_diario is None or len(df_diario) < 120:
            return None

        df_diario.columns = [
            col[0] if isinstance(col, tuple) else col
            for col in df_diario.columns
        ]

        # =========================
        # FILTRO SEMANAL (TENDÊNCIA)
        # =========================
        df_semanal = df_diario.resample('W').last()
        df_s = calcular_indicadores(df_semanal)
        df_s['EMA69'] = ta.ema(df_s['Close'], length=69)

        s = df_s.iloc[-1]

        semanal_ok = (
            s['Close'] > s['EMA69'] and
            s['STOCHk_14_3_3'] > s['STOCHd_14_3_3'] and
            s['DMP_14'] > s['DMN_14'] and
            s['ADX_14'] > 15
        )

        if not semanal_ok:
            return None

        # =========================
        # FILTRO DIÁRIO (GATILHO)
        # =========================
        df_d = calcular_indicadores(df_diario)
        df_d['EMA69'] = ta.ema(df_d['Close'], length=69)

        d_atual = df_d.iloc[-1]
        d_anterior = df_d.iloc[-2]

        diario_ok = (
            d_atual['Close'] > d_atual['EMA69'] and
            d_atual['DMP_14'] > d_atual['DMN_14'] and
            d_atual['ADX_14'] > 15
        )

        cruzou_hoje = (
            d_atual['STOCHk_14_3_3'] > d_atual['STOCHd_14_3_3'] and
            d_anterior['STOCHk_14_3_3'] <= d_anterior['STOCHd_14_3_3']
        )

        estocastico_ok = (
            cruzou_hoje and
            d_atual['STOCHk_14_3_3'] <= 35 and
            d_atual['STOCHk_14_3_3'] > d_anterior['STOCHk_14_3_3']
        )

        if diario_ok and estocastico_ok:
            return {
                "Preço": round(float(d_atual['Close']), 2),
                "ADX Diário": round(d_atual['ADX_14'], 1),
                "Stoch K": round(d_atual['STOCHk_14_3_3'], 1),
                "EMA 69 Semanal": round(float(s['EMA69']), 2)
            }

        return None

    except:
        return None

# -----------------------------------------------------------------------------
# APP STREAMLIT
# -----------------------------------------------------------------------------
def main():
    st.title("📊 Scanner Profissional — ETFs & FIIs de Tijolo")
    st.write("Setup: Tendência EMA 69 (Semanal) + Gatilho Diário Estocástico ≤ 35")

    ativos_lista = [
        # =====================
        # ETFs ORIGINAIS
        # =====================
        "BOVA11.SA", "IVVB11.SA", "SMAL11.SA", "HASH11.SA",
        "SPXI11.SA", "TECB11.SA", "NASD11.SA", "GOLD11.SA",
        "DIVO11.SA", "PIBB11.SA",

        # =====================
        # ETFs ADICIONAIS RELEVANTES
        # =====================
        "BOVV11.SA", "BBOV11.SA", "B5P211.SA",

        # =====================
        # FIIs DE TIJOLO (ORIGINAIS)
        # =====================
        "GARE11.SA", "HGLG11.SA", "XPLG11.SA", "VILG11.SA",
        "BRCO11.SA", "BTLG11.SA", "XPML11.SA", "VISC11.SA",
        "HSML11.SA", "MALL11.SA", "KNRI11.SA", "JSRE11.SA",
        "PVBI11.SA", "HGRE11.SA", "BRCR11.SA", "RBRP11.SA",
        "ALZR11.SA", "GGRC11.SA"
    ]

    if st.button("🚀 Iniciar Varredura"):
        hits = []
        barra = st.progress(0)
        status = st.empty()

        for i, ticker in enumerate(ativos_lista):
            nome = ticker.replace(".SA", "")
            status.text(f"Analisando {nome}...")
            res = analisar_ativo(ticker)

            if res:
                hits.append({
                    "ATIVO": nome,
                    "PREÇO": res["Preço"],
                    "ADX D": res["ADX Diário"],
                    "STOCH K": res["Stoch K"],
                    "EMA 69 (Semanal)": res["EMA 69 Semanal"]
                })

            barra.progress((i + 1) / len(ativos_lista))

        status.success("Varredura concluída.")

        if hits:
            st.table(pd.DataFrame(hits))
        else:
            st.info("Nenhum ativo atende aos critérios no fechamento atual.")

if __name__ == "__main__":
    main()

