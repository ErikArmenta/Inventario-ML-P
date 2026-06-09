import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página a todo lo ancho para un dashboard profesional
st.set_page_config(page_title="Dashboard de Inventario MVP", layout="wide", page_icon="📦")

st.title("📦 Análisis de Inventario y Desviaciones")
st.markdown("Sube el concentrado semanal para generar el reporte de materiales en tiempo real.")

# Uploader de archivos
uploaded_file = st.file_uploader("Carga el archivo Excel o CSV", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Lectura ultrarrápida usando pandas
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("¡Archivo cargado y procesado con éxito!")
        
        # Limpieza rápida: asegurar que las columnas numéricas no traigan strings raros
        cols_numericas = ['Lead Time', 'Cost', 'weekly use', 'Intransit', '1PPW', 'DOCK', 'PWIP', 'QCHH', 'SL2P', 'Total Weeks']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # ==========================================
        # MOTOR DE CÁLCULO (Fórmulas al pie de la letra)
        # ==========================================
        
        # R: Total PZ = Suma(L2:Q2)
        loc_cols = ['Intransit', '1PPW', 'DOCK', 'PWIP', 'QCHH', 'SL2P']
        df['Total PZ Calculado'] = df[[c for c in loc_cols if c in df.columns]].sum(axis=1)

        # S: Total amount = Cost * Total PZ
        df['Total Amount Calculado'] = df['Cost'] * df['Total PZ Calculado']

        # AA: Target (Óptimo) = (Lead Time + 7) / 7
        df['Target'] = (df['Lead Time'] + 7) / 7

        # AB: Target total = Target * weekly use * Cost
        df['Target Total USD'] = df['Target'] * df['weekly use'] * df['Cost']

        # Asumiendo que 'Total Weeks' (Columna Z) ya viene en el archivo o se suma de sus respectivas columnas (T:Y)
        if 'Total Weeks' in df.columns:
            # AC: Weeks out = Total Weeks - Target
            df['Weeks Out'] = df['Total Weeks'] - df['Target']
            
            # AD: Pz out = Weeks out * weekly use
            df['Pz Out'] = df['Weeks Out'] * df['weekly use']
            
            # AE: Total USD out = Pz out * Cost
            df['Total USD Out'] = df['Pz Out'] * df['Cost']

        # ==========================================
        # DASHBOARD & KPIs
        # ==========================================
        st.markdown("---")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_inventory_usd = df['Total Amount Calculado'].sum()
        total_target_usd = df['Target Total USD'].sum()
        total_usd_out = df['Total USD Out'].sum() if 'Total USD Out' in df.columns else 0
        total_pz = df['Total PZ Calculado'].sum()
        
        with col1:
            st.metric("Valor Total Inventario", f"${total_inventory_usd:,.2f}")
        with col2:
            st.metric("Valor Óptimo (Target Total)", f"${total_target_usd:,.2f}")
        with col3:
            # Si el USD Out es positivo, es un exceso crítico, lo mostramos como alerta
            st.metric("Total USD Out (Desviación)", f"${total_usd_out:,.2f}", delta="Exceso" if total_usd_out > 0 else "Faltante", delta_color="inverse")
        with col4:
            st.metric("Piezas Totales Físicas/Tránsito", f"{total_pz:,.0f}")

        st.markdown("---")

        # Gráficas con Plotly para humillar a Power BI
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("🚨 Top 15 Números de Parte Críticos (USD Out)")
            # Filtramos los que tienen mayor exceso de dinero y los ordenamos
            df_critical = df.nlargest(15, 'Total USD Out') if 'Total USD Out' in df.columns else df.head(15)
            fig_bar = px.bar(
                df_critical, 
                x='Total USD Out', 
                y='Number', 
                orientation='h',
                color='Total USD Out',
                color_continuous_scale='Reds',
                text_auto='.2s'
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_graf2:
            st.subheader("⚖️ Semanas Actuales vs Óptimo (Target) por N° Parte")
            # Un scatter plot para ver rápidamente qué partes están fuera del límite
            fig_scatter = px.scatter(
                df, 
                x='Target', 
                y='Total Weeks', 
                hover_data=['Number', 'Cost', 'weekly use'],
                color='Weeks Out',
                color_continuous_scale='RdYlGn_r' # Rojo para desviaciones altas
            )
            # Línea ideal donde Semanas = Target
            max_val = max(df['Target'].max(), df['Total Weeks'].max())
            fig_scatter.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode='lines', name='Ideal (Semanas=Target)', line=dict(color='white', dash='dash')))
            fig_scatter.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_scatter, use_container_width=True)

        # Vista de tabla interactiva al final para los analistas
        st.subheader("📑 Tabla Detallada (Data Entry Simulada)")
        # Mostramos las columnas más relevantes
        cols_to_show = ['Number', 'Description', 'Lead Time', 'Cost', 'weekly use', 'Total PZ Calculado', 'Target', 'Total Weeks', 'Weeks Out', 'Total USD Out']
        st.dataframe(df[[c for c in cols_to_show if c in df.columns]], use_container_width=True)

    except Exception as e:
        st.error(f"Error procesando el archivo. Asegúrate de que tenga el formato correcto. Detalles: {e}")

else:
    st.info("Esperando archivo... Sube el reporte exportado para comenzar.")