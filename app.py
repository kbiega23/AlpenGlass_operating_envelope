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
- **Minimum Size**: At least one edge must be 16" or greater
""")

# Load data
@st.cache_data
def load_data():
    """Load the glass configuration data from Excel file"""
    import os
    
    # List of possible filenames to try
    possible_names = [
        'AlpenGlass max sizing data.xlsx',
        'AlpenGlass_max_sizing_data.xlsx',
        'alpenglass_max_sizing_data.xlsx',
    ]
    
    # Debug: show what files are available
    current_dir = os.getcwd()
    files_in_dir = os.listdir(current_dir)
    
    for filename in possible_names:
        if os.path.exists(filename):
            try:
                df = pd.read_excel(filename)
                return df
            except Exception as e:
                st.error(f"Error reading {filename}: {str(e)}")
                return None
    
    # If we get here, file wasn't found
    st.error(f"Excel file not found. Looking in: {current_dir}")
    st.error(f"Files available: {', '.join(files_in_dir)}")
    st.error("Please ensure 'AlpenGlass max sizing data.xlsx' is in your GitHub repository.")
    return None

# Create the envelope visualization for specific configuration
def create_envelope_plot(config_data, min_edge=16):
    """Create a plotly figure showing the core range and technical limit envelopes"""
    
    if config_data.empty:
        return None
    
    # Extract values
    core_long = config_data['CoreRange_ maxlongedge'].values[0]
    core_short = config_data['CoreRange_maxshortedge'].values[0]
    tech_long = config_data['Technical limit_long edge'].values[0]
    tech_short = config_data['Technical limit_short edge'].values[0]
    
    fig = go.Figure()
    
    # Create a custom data mesh for hover information
    max_dim = max(tech_long, tech_short)
    x_range = np.linspace(0, max_dim * 1.1, 100)
    y_range = np.linspace(0, max_dim * 1.1, 100)
    X, Y = np.meshgrid(x_range, y_range)
    
    # Determine which region each point is in
    Z = np.zeros_like(X)
    hover_text = []
    
    for i in range(len(y_range)):
        row_text = []
        for j in range(len(x_range)):
            x, y = X[i, j], Y[i, j]
            
            # Check if point is valid (meets minimum size constraint)
            meets_min = (x >= min_edge or y >= min_edge)
            
            # Check if in technical limit
            in_tech = ((x <= tech_long and y <= tech_short) or 
                      (x <= tech_short and y <= tech_long)) and meets_min
            
            # Check if in core range
            in_core = ((x <= core_long and y <= core_short) or 
                      (x <= core_short and y <= core_long)) and meets_min
            
            area_sqft = (x * y) / 144  # Convert sq inches to sq feet
            
            if in_core:
                Z[i, j] = 2
                row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br>Area: {area_sqft:.1f} sq ft<br><b>Core Range</b>")
            elif in_tech:
                Z[i, j] = 1
                row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br>Area: {area_sqft:.1f} sq ft<br><b>⚠️ Extra charges may apply for extreme sizes</b>")
            else:
                Z[i, j] = 0
                if not meets_min:
                    row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br><b>Below minimum size</b>")
                else:
                    row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br><b>Outside technical limits</b>")
        hover_text.append(row_text)
    
    # Add invisible heatmap for hover functionality
    fig.add_trace(go.Heatmap(
        x=x_range,
        y=y_range,
        z=Z,
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
        showscale=False,
        hoverinfo='text',
        text=hover_text,
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Technical Limit envelope (larger, outer rectangle)
    tech_x = [0, tech_long, tech_long, tech_short, tech_short, 0, 0]
    tech_y = [0, 0, tech_short, tech_short, tech_long, tech_long, 0]
    
    fig.add_trace(go.Scatter(
        x=tech_x,
        y=tech_y,
        fill='toself',
        fillcolor='rgba(255, 152, 0, 0.2)',
        line=dict(color='rgba(255, 152, 0, 0.8)', width=2, dash='dash'),
        name='Technical Limit',
        hoverinfo='skip'
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
        hoverinfo='skip'
    ))
    
    # Add minimum size constraint lines (16" minimum on at least one edge)
    fig.add_trace(go.Scatter(
        x=[min_edge, min_edge],
        y=[0, max_dim * 1.1],
        line=dict(color='rgba(255, 0, 0, 0.5)', width=2, dash='dot'),
        name=f'Min Size ({min_edge}")',
        hoverinfo='skip',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[0, max_dim * 1.1],
        y=[min_edge, min_edge],
        line=dict(color='rgba(255, 0, 0, 0.5)', width=2, dash='dot'),
        name=f'Min Size ({min_edge}")',
        hoverinfo='skip',
        showlegend=False
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
    max_dim_plot = max(tech_long, tech_short) * 1.1
    
    fig.update_layout(
        xaxis_title="Width (inches)",
        yaxis_title="Height (inches)",
        xaxis=dict(range=[0, max_dim_plot], showgrid=True, gridcolor='lightgray'),
        yaxis=dict(range=[0, max_dim_plot], showgrid=True, gridcolor='lightgray', scaleanchor="x", scaleratio=1),
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

# Create overall max sizes plot
def create_overall_max_plot(df, min_edge=16):
    """Create a plot showing the absolute maximum sizes across all configurations"""
    
    # Find overall maximums
    core_long_max = df['CoreRange_ maxlongedge'].max()
    core_short_max = df['CoreRange_maxshortedge'].max()
    tech_long_max = df['Technical limit_long edge'].max()
    tech_short_max = df['Technical limit_short edge'].max()
    
    fig = go.Figure()
    
    # Create hover mesh
    max_dim = max(tech_long_max, tech_short_max)
    x_range = np.linspace(0, max_dim * 1.1, 100)
    y_range = np.linspace(0, max_dim * 1.1, 100)
    X, Y = np.meshgrid(x_range, y_range)
    
    Z = np.zeros_like(X)
    hover_text = []
    
    for i in range(len(y_range)):
        row_text = []
        for j in range(len(x_range)):
            x, y = X[i, j], Y[i, j]
            
            meets_min = (x >= min_edge or y >= min_edge)
            
            in_tech = ((x <= tech_long_max and y <= tech_short_max) or 
                      (x <= tech_short_max and y <= tech_long_max)) and meets_min
            
            in_core = ((x <= core_long_max and y <= core_short_max) or 
                      (x <= core_short_max and y <= core_long_max)) and meets_min
            
            area_sqft = (x * y) / 144
            
            if in_core:
                Z[i, j] = 2
                row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br>Area: {area_sqft:.1f} sq ft<br><b>Core Range</b>")
            elif in_tech:
                Z[i, j] = 1
                row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br>Area: {area_sqft:.1f} sq ft<br><b>⚠️ Extra charges may apply for extreme sizes</b>")
            else:
                Z[i, j] = 0
                if not meets_min:
                    row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br><b>Below minimum size</b>")
                else:
                    row_text.append(f"Width: {x:.1f}\"<br>Height: {y:.1f}\"<br><b>Outside technical limits</b>")
        hover_text.append(row_text)
    
    # Add invisible heatmap for hover
    fig.add_trace(go.Heatmap(
        x=x_range,
        y=y_range,
        z=Z,
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
        showscale=False,
        hoverinfo='text',
        text=hover_text,
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Technical Limit envelope
    tech_x = [0, tech_long_max, tech_long_max, tech_short_max, tech_short_max, 0, 0]
    tech_y = [0, 0, tech_short_max, tech_short_max, tech_long_max, tech_long_max, 0]
    
    fig.add_trace(go.Scatter(
        x=tech_x,
        y=tech_y,
        fill='toself',
        fillcolor='rgba(255, 152, 0, 0.2)',
        line=dict(color='rgba(255, 152, 0, 0.8)', width=2, dash='dash'),
        name='Technical Limit',
        hoverinfo='skip'
    ))
    
    # Core Range envelope
    core_x = [0, core_long_max, core_long_max, core_short_max, core_short_max, 0, 0]
    core_y = [0, 0, core_short_max, core_short_max, core_long_max, core_long_max, 0]
    
    fig.add_trace(go.Scatter(
        x=core_x,
        y=core_y,
        fill='toself',
        fillcolor='rgba(33, 150, 243, 0.3)',
        line=dict(color='rgba(33, 150, 243, 1)', width=3),
        name='Core Range',
        hoverinfo='skip'
    ))
    
    # Minimum size constraint lines
    fig.add_trace(go.Scatter(
        x=[min_edge, min_edge],
        y=[0, max_dim * 1.1],
        line=dict(color='rgba(255, 0, 0, 0.5)', width=2, dash='dot'),
        name=f'Min Size ({min_edge}")',
        hoverinfo='skip',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[0, max_dim * 1.1],
        y=[min_edge, min_edge],
        line=dict(color='rgba(255, 0, 0, 0.5)', width=2, dash='dot'),
        name=f'Min Size ({min_edge}")',
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Annotations
    annotations = [
        dict(x=core_long_max, y=core_short_max, text=f"{core_long_max}\" × {core_short_max}\"",
             showarrow=True, arrowhead=2, ax=20, ay=-20,
             bgcolor="rgba(33, 150, 243, 0.8)", font=dict(color="white", size=10)),
        dict(x=core_short_max, y=core_long_max, text=f"{core_short_max}\" × {core_long_max}\"",
             showarrow=True, arrowhead=2, ax=-20, ay=20,
             bgcolor="rgba(33, 150, 243, 0.8)", font=dict(color="white", size=10)),
        dict(x=tech_long_max, y=tech_short_max, text=f"{tech_long_max}\" × {tech_short_max}\"",
             showarrow=True, arrowhead=2, ax=30, ay=-30,
             bgcolor="rgba(255, 152, 0, 0.8)", font=dict(color="white", size=10)),
        dict(x=tech_short_max, y=tech_long_max, text=f"{tech_short_max}\" × {tech_long_max}\"",
             showarrow=True, arrowhead=2, ax=-30, ay=30,
             bgcolor="rgba(255, 152, 0, 0.8)", font=dict(color="white", size=10))
    ]
    
    max_dim_plot = max(tech_long_max, tech_short_max) * 1.1
    
    fig.update_layout(
        xaxis_title="Width (inches)",
        yaxis_title="Height (inches)",
        xaxis=dict(range=[0, max_dim_plot], showgrid=True, gridcolor='lightgray'),
        yaxis=dict(range=[0, max_dim_plot], showgrid=True, gridcolor='lightgray', scaleanchor="x", scaleratio=1),
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
    
    # View mode selector
    view_mode = st.radio(
        "Select View Mode:",
        ["Specific Configuration", "Overall Maximum Sizes"],
        horizontal=True
    )
    
    if view_mode == "Specific Configuration":
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
                - Max Area: **{core_long * core_short} sq in** ({(core_long * core_short)/144:.1f} sq ft)
                """)
                
                # Technical Limit specifications
                st.markdown("**Technical Limit** (Premium Cost)")
                tech_long = filtered_df['Technical limit_long edge'].values[0]
                tech_short = filtered_df['Technical limit_short edge'].values[0]
                st.warning(f"""
                - Maximum Long Edge: **{tech_long}\"**
                - Maximum Short Edge: **{tech_short}\"**
                - Max Size: **{tech_long}\" × {tech_short}\"**
                - Max Area: **{tech_long * tech_short} sq in** ({(tech_long * tech_short)/144:.1f} sq ft)
                """)
                
                # Minimum size
                st.markdown("**Minimum Size Constraint**")
                st.error(f"""
                - At least one edge must be **16\"** or greater
                """)
                
                # Additional notes
                st.markdown("---")
                st.markdown("### 📝 Notes")
                st.markdown("""
                - Hover over the chart to see dimensions and pricing info
                - The chart shows both possible orientations (portrait and landscape)
                - Core Range represents the most cost-effective production envelope
                - Technical Limit sizes will incur a cost premium
                - All dimensions are in inches
                """)
        else:
            st.error("No configuration found for the selected parameters. Please check your data file.")
    
    else:  # Overall Maximum Sizes view
        st.subheader("Overall Maximum Sizes Across All Configurations")
        
        # Calculate overall stats
        core_long_max = df['CoreRange_ maxlongedge'].max()
        core_short_max = df['CoreRange_maxshortedge'].max()
        tech_long_max = df['Technical limit_long edge'].max()
        tech_short_max = df['Technical limit_short edge'].max()
        
        # Create two columns
        plot_col, specs_col = st.columns([2, 1])
        
        with plot_col:
            fig = create_overall_max_plot(df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with specs_col:
            st.markdown("### Maximum Specifications")
            
            st.markdown("**Core Range Maximum** (Efficient Production)")
            st.info(f"""
            - Maximum Long Edge: **{core_long_max}\"**
            - Maximum Short Edge: **{core_short_max}\"**
            - Max Size: **{core_long_max}\" × {core_short_max}\"**
            - Max Area: **{core_long_max * core_short_max} sq in** ({(core_long_max * core_short_max)/144:.1f} sq ft)
            """)
            
            st.markdown("**Technical Limit Maximum** (Premium Cost)")
            st.warning(f"""
            - Maximum Long Edge: **{tech_long_max}\"**
            - Maximum Short Edge: **{tech_short_max}\"**
            - Max Size: **{tech_long_max}\" × {tech_short_max}\"**
            - Max Area: **{tech_long_max * tech_short_max} sq in** ({(tech_long_max * tech_short_max)/144:.1f} sq ft)
            """)
            
            st.markdown("**Minimum Size Constraint**")
            st.error(f"""
            - At least one edge must be **16\"** or greater
            """)
            
            st.markdown("---")
            st.markdown("### 📝 Notes")
            st.markdown("""
            - These represent the absolute maximum sizes across ALL configurations
            - Hover over the chart to see dimensions and pricing info
            - Specific configurations may have smaller limits
            - Use "Specific Configuration" view to see exact limits for your glass type
            """)
