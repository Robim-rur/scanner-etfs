import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# =============================================================================
# SETUP OPERACIONAL - ETFs & FIIs DE TIJOLO (EMA 69)
# =============================================================================
st.set_page_config(page_title="SCANNER ETFs & FIIs - ELITE", layout="wide")

def calcular_indicadores(df):
    df = df.copy()
    # Estocástico 14,3,3
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
    # DMI/ADX 14
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    return pd.concat([df, stoch, adx_df], axis=1).dropna()

def analisar_ativo(ticker):
    try:
        # Puxa 2 anos para garantir a EMA 69 Semanal
        df_diario = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df_diario is None or len(df_diario) < 100: return None
        
        df_diario.columns = [col[0] if isinstance(col, tuple) else col for col in df_diario.columns]
        
        # --- FILTRO 1: SEMANAL (EMA 69) ---
        df_semanal = df_diario.resample('W').last()
        df_s = calcular_indicadores(df_semanal)
        df_s['EMA69'] = ta.ema(df_s['Close'], length=69)
        
        s = df_s.iloc[-1]
        
        # Regras Semanal: Preço > EMA69 + K > D + DMI Positivo + ADX > 15
        semanal_ok = (s['Close'] > s['EMA69']) and \
                     (s['STOCHk_14_3_3'] > s['STOCHd_14_3_3']) and \
                     (s['DMP_14'] > s['DMN_14']) and \
                     (s['ADX_14'] > 15)
        
        if not semanal_ok: return None

        # --- FILTRO 2: DIÁRIO (GATILHO < 35) ---
        df_d = calcular_indicadores(df_diario)
        d_atual = df_d.iloc[-1]
        d_anterior = df_d.iloc[-2]
        
        dmi_diario_ok = (d_atual['DMP_14'] > d_atual['DMN_14']) and (d_atual['ADX_14'] > 15)
        
        # Gatilho: Cruzamento hoje (K > D) e K <= 35
        cruzou_hoje = (d_atual['STOCHk_14_3_3'] > d_atual['STOCHd_14_3_3']) and \
                      (d_anterior['STOCHk_14_3_3'] <= d_anterior['STOCHd_14_3_3'])
        
        gatilho_ok = cruzou_hoje and (d_atual['STOCHk_14_3_3'] <= 35)

        if dmi_diario_ok and gatilho_ok:
            return {
                "Preço": round(float(d_atual['Close']), 2),
                "ADX_D": round(d_atual['ADX_14'], 1),
                "StochK": round(d_atual['STOCHk_14_3_3'], 1),
                "EMA69_S": round(float(s['EMA69']), 2)
            }
        return None
    except:
        return None

def main():
    st.title("📊 Scanner Híbrido: ETFs + FIIs de Tijolo")
    st.write("Estratégia: EMA 69 (Tendência) + Estocástico Diário < 35 (Gatilho)")

    # LISTA COMBINADA COM GARE11 INCLUÍDO
    ativos_lista = [
        # --- ETFs ---
        "BOVA11.SA", "IVVB11.SA", "SMAL11.SA", "HASH11.SA", "SPXI11.SA", "TECB11.SA", 
        "NASD11.SA", "GOLD11.SA", "DIVO11.SA", "PIBB11.SA",
        # --- FIIs DE TIJOLO (Incluso GARE11) ---
        "GARE11.SA", "HGLG11.SA", "XPLG11.SA", "VILG11.SA", "BRCO11.SA", "BTLG11.SA", 
        "XPML11.SA", "VISC11.SA", "HSML11.SA", "MALL11.SA",             
        "KNRI11.SA", "JSRE11.SA", "PVBI11.SA", "HGRE11.SA",             
        "BRCR11.SA", "RBRP11.SA", "ALZR11.SA", "GGRC11.SA",             
        "KNIP11.SA", "KNCR11.SA", "HCTR11.SA"                          
    ]

    if st.button('🚀 Iniciar Varredura de ETFs e FIIs'):
        hits = []
        barra = st.progress(0)
        status = st.empty()
        
        for i, ticker in enumerate(ativos_lista):
            nome = ticker.replace(".SA", "")
            status.text(f"Analisando: {nome}...")
            res = analisar_ativo(ticker)
            
            if res:
                hits.append({
                    "ATIVO": nome,
                    "PREÇO": res["Preço"],
                    "ADX DIÁRIO": res["ADX_D"],
                    "STOCH_K": res["StochK"],
                    "EMA 69 (Semanal)": res["EMA69_S"]
                })
            barra.progress((i + 1) / len(ativos_lista))
        
        status.success("Varredura concluída!")
        
        if hits:
            st.table(pd.DataFrame(hits))
        else:
            st.info("Nenhum ativo (ETF ou FII) cumpre os critérios técnicos agora.")

if __name__ == "__main__":
    main()
