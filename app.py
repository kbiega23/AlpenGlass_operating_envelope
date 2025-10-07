import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="AlpenGlass Window Size Visualizer",
    page_icon="🪟",
    layout="wide"
)

# Title and description
st.title("🪟 AlpenGlass Window Size Envelope")
st.markdown("""
This tool visualizes the maximum window sizes for different glass configurations.
- **Core Range** (blue): Efficient, low-cost production range
- **Technical Limit** (orange): Maximum physically achievable size (premium cost)
""")

# Load data
@st.cache_data
def load_data():
    """Load the glass configuration data from Excel file"""
    try:
        df = pd.read_excel('AlpenGlass max sizing data.xlsx')
        return df
    except FileNotFoundError:
        st.error("Error: 'AlpenGlass max sizing data.xlsx' not found. Please ensure the file is in the same directory.")
        return None

# Create the envelope visualization
def create_envelope_plot(config_data):
    """Create a plotly figure showing the core range and technical limit envelopes"""
    
    if config_data.empty:
        return None
    
    # Extract values
    core_long = config_data['CoreRange_ maxlongedge'].values[0]
    core_short = config_data['CoreRange_maxshortedge'].values[0]
    tech_long = config_data['Technical limit_long edge'].values[0]
    tech_short = config_data['Technical limit_short edge'].values[0]
    
    fig = go.Figure()
    
    # Technical Limit envelope (larger, outer rectangle)
    # We create both orientations: long edge as width or as height
    tech_x = [0, tech_long, tech_long, tech_short, tech_short, 0, 0]
    tech_y = [0, 0, tech_short, tech_short, tech_long, tech_long, 0]
    
    fig.add_trace(go.Scatter(
        x=tech_x,
        y=tech_y,
        fill='toself',
        fillcolor='rgba(255, 152, 0, 0.2)',
        line=dict(color='rgba(255, 152, 0, 0.8)', width=2, dash='dash'),
        name='Technical Limit',
        hovertemplate='<b>Technical Limit</b><br>Width: %{x} inches<br>Height: %{y} inches<extra></extra>'
    ))
    
    # Core Range envelope (smaller, inner rectangle)
    core_x = [0, core_long, core_long, core_short, core_short, 0, 0]
    core_y = [0, 0, core_short, core_short, core_long, core_long, 0]
    
    fig.add_trace(go.Scatter(
        x=core_x,
        y=core_y,
        fill='toself',
        fillcolor='rgba(33, 150, 243, 0.3)',
        line=dict(color='rgba(33, 150, 243, 1)', width=3),
        name='Core Range',
        hovertemplate='<b>Core Range</b><br>Width: %{x} inches<br>Height: %{y} inches<extra></extra>'
    ))
    
    # Add corner labels for key dimensions
    annotations = [
        dict(x=core_long, y=core_short, text=f"{core_long}\" × {core_short}\"",
             showarrow=True, arrowhead=2, ax=20, ay=-20,
             bgcolor="rgba(33, 150, 243, 0.8)", font=dict(color="white", size=10)),
        dict(x=core_short, y=core_long, text=f"{core_short}\" × {core_long}\"",
             showarrow=True, arrowhead=2, ax=-20, ay=20,
             bgcolor="rgba(33, 150, 243, 0.8)", font=dict(color="white", size=10)),
        dict(x=tech_long, y=tech_short, text=f"{tech_long}\" × {tech_short}\"",
             showarrow=True, arrowhead=2, ax=30, ay=-30,
             bgcolor="rgba(255, 152, 0, 0.8)", font=dict(color="white", size=10)),
        dict(x=tech_short, y=tech_long, text=f"{tech_short}\" × {tech_long}\"",
             showarrow=True, arrowhead=2, ax=-30, ay=30,
             bgcolor="rgba(255, 152, 0, 0.8)", font=dict(color="white", size=10))
    ]
    
    # Update layout
    max_dim = max(tech_long, tech_short) * 1.1
    
    fig.update_layout(
        xaxis_title="Width (inches)",
        yaxis_title="Height (inches)",
        xaxis=dict(range=[0, max_dim], showgrid=True, gridcolor='lightgray'),
        yaxis=dict(range=[0, max_dim], showgrid=True, gridcolor='lightgray', scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        hovermode='closest',
        height=600,
        annotations=annotations,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Main app logic
def main():
    # Load data
    df = load_data()
    
    if df is None:
        st.stop()
    
    # Create three columns for selectors
    col1, col2, col3 = st.columns(3)
    
    with col1:
        outer_lite_options = sorted(df['Outer Lites'].unique())
        outer_lite = st.selectbox(
            "Outer Lites Thickness",
            outer_lite_options,
            format_func=lambda x: f"{x}mm"
        )
    
    with col2:
        inner_lite_options = sorted(df['Inner Lite'].unique())
        inner_lite = st.selectbox(
            "Center Lite Thickness",
            inner_lite_options,
            format_func=lambda x: f"{x}mm"
        )
    
    with col3:
        tempered_options = sorted(df['Tempered or Annealed'].unique())
        tempered = st.selectbox(
            "Glass Treatment",
            tempered_options
        )
    
    # Filter data based on selection
    filtered_df = df[
        (df['Outer Lites'] == outer_lite) &
        (df['Inner Lite'] == inner_lite) &
        (df['Tempered or Annealed'] == tempered)
    ]
    
    # Display configuration name
    if not filtered_df.empty:
        config_name = filtered_df['Name'].values[0]
        st.subheader(f"Configuration: {config_name}")
        
        # Create two columns for the plot and specifications
        plot_col, specs_col = st.columns([2, 1])
        
        with plot_col:
            # Create and display the plot
            fig = create_envelope_plot(filtered_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with specs_col:
            st.markdown("### Specifications")
            
            # Core Range specifications
            st.markdown("**Core Range** (Efficient Production)")
            core_long = filtered_df['CoreRange_ maxlongedge'].values[0]
            core_short = filtered_df['CoreRange_maxshortedge'].values[0]
            st.info(f"""
            - Maximum Long Edge: **{core_long}\"**
            - Maximum Short Edge: **{core_short}\"**
            - Max Size: **{core_long}\" × {core_short}\"**
            - Max Area: **{core_long * core_short} sq in**
            """)
            
            # Technical Limit specifications
            st.markdown("**Technical Limit** (Premium Cost)")
            tech_long = filtered_df['Technical limit_long edge'].values[0]
            tech_short = filtered_df['Technical limit_short edge'].values[0]
            st.warning(f"""
            - Maximum Long Edge: **{tech_long}\"**
            - Maximum Short Edge: **{tech_short}\"**
            - Max Size: **{tech_long}\" × {tech_short}\"**
            - Max Area: **{tech_long * tech_short} sq in**
            """)
            
            # Additional notes
            st.markdown("---")
            st.markdown("### 📝 Notes")
            st.markdown("""
            - The chart shows both possible orientations (portrait and landscape)
            - Core Range represents the most cost-effective production envelope
            - Technical Limit sizes will incur a cost premium
            - All dimensions are in inches
            """)
    else:
        st.error("No configuration found for the selected parameters. Please check your data file.")

if __name__ == "__main__":
    main()
