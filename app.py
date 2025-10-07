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
st.title("🪟 AlpenGlass Sizing Limits")
st.markdown("""
This tool visualizes the maximum window sizes for different glass configurations.
- **Core Range** (blue): Efficient, low-cost production range
- **Technical Limit** (orange): Maximum physically achievable size (premium cost)
- **Minimum Size**: At least one edge must be 16" or greater
- **White areas**: Do not meet minimum size requirements
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
    
    for filename in possible_names:
        if os.path.exists(filename):
            try:
                df = pd.read_excel(filename)
                return df
            except Exception as e:
                st.error(f"Error reading {filename}: {str(e)}")
                return None
    
    # If we get here, file wasn't found
    st.error("Excel file not found. Please ensure 'AlpenGlass max sizing data.xlsx' is in your GitHub repository.")
    return None

# Create the envelope visualization
def create_envelope_plot(config_data, min_edge=16, show_all=False, all_configs_df=None):
    """Create a plotly figure showing the core range and technical limit envelopes
    
    Args:
        config_data: DataFrame with single config or aggregated values for bounds
        min_edge: Minimum edge constraint
        show_all: If True, draw all configurations from all_configs_df
        all_configs_df: DataFrame with all matching configurations to display
    """
    
    if config_data.empty:
        return None
    
    # Extract values for bounds
    if show_all and all_configs_df is not None and not all_configs_df.empty:
        core_long = all_configs_df['CoreRange_ maxlongedge'].max()
        core_short = all_configs_df['CoreRange_maxshortedge'].max()
        tech_long = all_configs_df['Technical limit_long edge'].max()
        tech_short = all_configs_df['Technical limit_short edge'].max()
    else:
        core_long = config_data['CoreRange_ maxlongedge'].values[0]
        core_short = config_data['CoreRange_maxshortedge'].values[0]
        tech_long = config_data['Technical limit_long edge'].values[0]
        tech_short = config_data['Technical limit_short edge'].values[0]
    
    fig = go.Figure()
    
    # Create a grid snapped to 1" increments for hover
    max_dim = max(tech_long, tech_short)
    x_range = np.arange(0, max_dim * 1.1 + 1, 1)  # 1" increments
    y_range = np.arange(0, max_dim * 1.1 + 1, 1)  # 1" increments
    X, Y = np.meshgrid(x_range, y_range)
    
    # Determine which region each point is in
    Z = np.zeros_like(X, dtype=float)
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
                row_text.append(f"Width: {int(x)}\"<br>Height: {int(y)}\"<br>Area: {area_sqft:.1f} sq ft<br><b>Core Range</b>")
            elif in_tech:
                Z[i, j] = 1
                row_text.append(f"Width: {int(x)}\"<br>Height: {int(y)}\"<br>Area: {area_sqft:.1f} sq ft<br><b>⚠️ Extra charges may apply for extreme sizes</b>")
            else:
                Z[i, j] = 0
                if not meets_min:
                    row_text.append(f"Width: {int(x)}\"<br>Height: {int(y)}\"<br>Area: {area_sqft:.1f} sq ft<br><b>Below minimum size</b>")
                else:
                    row_text.append(f"Width: {int(x)}\"<br>Height: {int(y)}\"<br>Area: {area_sqft:.1f} sq ft<br><b>Outside technical limits</b>")
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
    
    # Technical Limit envelope - modified to exclude bottom-left corner below min_edge
    tech_x = [min_edge, tech_long, tech_long, tech_short, tech_short, 0, 0, min_edge, min_edge]
    tech_y = [0, 0, tech_short, tech_short, tech_long, tech_long, min_edge, min_edge, 0]
    
    fig.add_trace(go.Scatter(
        x=tech_x,
        y=tech_y,
        fill='toself',
        fillcolor='rgba(255, 152, 0, 0.2)',
        line=dict(color='rgba(255, 152, 0, 0.8)', width=2, dash='dash'),
        name='Technical Limit',
        hoverinfo='skip'
    ))
    
    # Core Range envelope - draw all configurations if show_all is True
    if show_all and all_configs_df is not None and not all_configs_df.empty:
        # Create a single unified shape by using None separators
        # This ensures consistent fill color without overlapping darkness
        
        all_x = []
        all_y = []
        
        for idx, row in all_configs_df.iterrows():
            c_long = row['CoreRange_ maxlongedge']
            c_short = row['CoreRange_maxshortedge']
            
            # Add this rectangle's coordinates
            rect_x = [min_edge, c_long, c_long, c_short, c_short, 0, 0, min_edge, min_edge]
            rect_y = [0, 0, c_short, c_short, c_long, c_long, min_edge, min_edge, 0]
            
            all_x.extend(rect_x)
            all_y.extend(rect_y)
            
            # Add None separator for next shape (except for last one)
            if idx < len(all_configs_df) - 1:
                all_x.append(None)
                all_y.append(None)
        
        # Draw all shapes as ONE trace with consistent color and NO border
        fig.add_trace(go.Scatter(
            x=all_x,
            y=all_y,
            fill='toself',
            fillcolor='rgba(33, 150, 243, 0.3)',
            line=dict(width=0),  # No borders
            name='Core Range',
            hoverinfo='skip'
        ))
        
        # Now compute the outer boundary by tracing the perimeter
        # Collect all unique edges from all configurations
        edges = []
        for idx, row in all_configs_df.iterrows():
            c_long = row['CoreRange_ maxlongedge']
            c_short = row['CoreRange_maxshortedge']
            
            # Define the 8 edges of each L-shaped polygon
            rect_edges = [
                ((min_edge, 0), (c_long, 0)),      # bottom horizontal
                ((c_long, 0), (c_long, c_short)),   # right vertical (short)
                ((c_long, c_short), (c_short, c_short)),  # top horizontal (short)
                ((c_short, c_short), (c_short, c_long)),  # middle vertical
                ((c_short, c_long), (0, c_long)),   # top horizontal (long)
                ((0, c_long), (0, min_edge)),       # left vertical
                ((0, min_edge), (min_edge, min_edge)),  # bottom horizontal (min)
                ((min_edge, min_edge), (min_edge, 0))   # right vertical (min)
            ]
            edges.extend(rect_edges)
        
        # Count edge occurrences - outer boundary edges appear only once
        from collections import Counter
        edge_counts = Counter()
        for edge in edges:
            # Normalize edge direction for counting
            normalized = tuple(sorted([edge[0], edge[1]]))
            edge_counts[normalized] += 1
        
        # Outer boundary edges appear an odd number of times
        outer_edges = [edge for edge, count in edge_counts.items() if count % 2 == 1]
        
        # Trace the outer boundary by connecting edges
        if outer_edges:
            # Build adjacency map
            adj = {}
            for edge in outer_edges:
                p1, p2 = edge
                if p1 not in adj:
                    adj[p1] = []
                if p2 not in adj:
                    adj[p2] = []
                adj[p1].append(p2)
                adj[p2].append(p1)
            
            # Start from (min_edge, 0) and trace the boundary
            boundary_points = []
            current = (min_edge, 0)
            visited = set()
            
            while True:
                boundary_points.append(current)
                visited.add(current)
                
                # Find next unvisited neighbor
                if current in adj:
                    next_points = [p for p in adj[current] if p not in visited]
                    if not next_points:
                        break
                    
                    # Choose the next point that continues the perimeter
                    # Sort by angle to maintain clockwise direction
                    if len(next_points) == 1:
                        current = next_points[0]
                    else:
                        # Multiple options - choose the one that goes clockwise
                        current = next_points[0]
                else:
                    break
                
                if current == (min_edge, 0):
                    break
            
            # Draw the outer boundary
            if len(boundary_points) > 2:
                boundary_x = [p[0] for p in boundary_points] + [boundary_points[0][0]]
                boundary_y = [p[1] for p in boundary_points] + [boundary_points[0][1]]
                
                fig.add_trace(go.Scatter(
                    x=boundary_x,
                    y=boundary_y,
                    mode='lines',
                    line=dict(color='rgba(33, 150, 243, 1)', width=3),
                    hoverinfo='skip',
                    showlegend=False
                ))
    else:
        # Single configuration - draw one envelope
        core_x = [min_edge, core_long, core_long, core_short, core_short, 0, 0, min_edge, min_edge]
        core_y = [0, 0, core_short, core_short, core_long, core_long, min_edge, min_edge, 0]
        
        fig.add_trace(go.Scatter(
            x=core_x,
            y=core_y,
            fill='toself',
            fillcolor='rgba(33, 150, 243, 0.3)',
            line=dict(color='rgba(33, 150, 243, 1)', width=3),
            name='Core Range',
            hoverinfo='skip'
        ))
    
    # Add corner labels for key dimensions with hover info
    annotations = [
        dict(x=core_long, y=core_short, 
             text=f"{core_long}\" × {core_short}\"<br>{(core_long*core_short)/144:.1f} sq ft",
             showarrow=True, arrowhead=2, ax=20, ay=-20,
             bgcolor="rgba(33, 150, 243, 0.8)", font=dict(color="white", size=10)),
        dict(x=core_short, y=core_long, 
             text=f"{core_short}\" × {core_long}\"<br>{(core_short*core_long)/144:.1f} sq ft",
             showarrow=True, arrowhead=2, ax=-20, ay=20,
             bgcolor="rgba(33, 150, 243, 0.8)", font=dict(color="white", size=10)),
        dict(x=tech_long, y=tech_short, 
             text=f"{tech_long}\" × {tech_short}\"<br>{(tech_long*tech_short)/144:.1f} sq ft",
             showarrow=True, arrowhead=2, ax=30, ay=-30,
             bgcolor="rgba(255, 152, 0, 0.8)", font=dict(color="white", size=10)),
        dict(x=tech_short, y=tech_long, 
             text=f"{tech_short}\" × {tech_long}\"<br>{(tech_short*tech_long)/144:.1f} sq ft",
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

# Main app logic
def main():
    # Load data
    df = load_data()
    
    if df is None:
        st.stop()
    
    # Create three columns for selectors
    col1, col2, col3 = st.columns(3)
    
    with col1:
        outer_lite_options = ['All'] + sorted(df['Outer Lites'].unique().tolist())
        outer_lite = st.selectbox(
            "Outer Lites Thickness",
            outer_lite_options,
            format_func=lambda x: x if x == 'All' else f"{x}mm"
        )
    
    with col2:
        inner_lite_options = ['All'] + sorted(df['Inner Lite'].unique().tolist())
        inner_lite = st.selectbox(
            "Center Lite Thickness",
            inner_lite_options,
            format_func=lambda x: x if x == 'All' else f"{x}mm"
        )
    
    with col3:
        tempered_options = ['All'] + sorted(df['Tempered or Annealed'].unique().tolist())
        tempered = st.selectbox(
            "Glass Treatment",
            tempered_options
        )
    
    # Filter data based on selection
    filtered_df = df.copy()
    
    if outer_lite != 'All':
        filtered_df = filtered_df[filtered_df['Outer Lites'] == outer_lite]
    
    if inner_lite != 'All':
        filtered_df = filtered_df[filtered_df['Inner Lite'] == inner_lite]
    
    if tempered != 'All':
        filtered_df = filtered_df[filtered_df['Tempered or Annealed'] == tempered]
    
    # Display configuration info
    if not filtered_df.empty:
        # Determine what to show
        show_all_configs = (outer_lite == 'All' or inner_lite == 'All' or tempered == 'All')
        
        if show_all_configs:
            st.subheader("Overall Maximum Sizes")
            config_description = []
            if outer_lite != 'All':
                config_description.append(f"Outer Lites: {outer_lite}mm")
            if inner_lite != 'All':
                config_description.append(f"Center Lite: {inner_lite}mm")
            if tempered != 'All':
                config_description.append(f"Treatment: {tempered}")
            
            if config_description:
                st.caption(f"Filtered by: {', '.join(config_description)}")
            else:
                st.caption("Showing all available configurations")
        else:
            config_name = filtered_df['Name'].values[0]
            st.subheader(f"Configuration: {config_name}")
        
        # Determine dimensions to display
        if show_all_configs:
            # Get overall max dimensions for display
            core_long_max = filtered_df['CoreRange_ maxlongedge'].max()
            core_short_max = filtered_df['CoreRange_maxshortedge'].max()
            
            filtered_df['tech_area'] = filtered_df['Technical limit_long edge'] * filtered_df['Technical limit_short edge']
            max_tech_idx = filtered_df['tech_area'].idxmax()
            tech_long_max = filtered_df.loc[max_tech_idx, 'Technical limit_long edge']
            tech_short_max = filtered_df.loc[max_tech_idx, 'Technical limit_short edge']
        else:
            # Single configuration
            core_long_max = filtered_df['CoreRange_ maxlongedge'].values[0]
            core_short_max = filtered_df['CoreRange_maxshortedge'].values[0]
            tech_long_max = filtered_df['Technical limit_long edge'].values[0]
            tech_short_max = filtered_df['Technical limit_short edge'].values[0]
        
        # Create synthetic config data for plotting
        plot_data = pd.DataFrame([{
            'CoreRange_ maxlongedge': core_long_max,
            'CoreRange_maxshortedge': core_short_max,
            'Technical limit_long edge': tech_long_max,
            'Technical limit_short edge': tech_short_max
        }])
        
        # Create two columns for the plot and specifications
        plot_col, specs_col = st.columns([2, 1])
        
        with plot_col:
            # Create and display the plot
            fig = create_envelope_plot(plot_data, show_all=show_all_configs, all_configs_df=filtered_df if show_all_configs else None)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with specs_col:
            st.markdown("### Specifications")
            
            # Core Range specifications
            st.markdown("**Core Range** (Efficient Production)")
            if show_all_configs:
                st.info(f"""
                - Maximum Long Edge: **{core_long_max}\"**
                - Maximum Short Edge: **{core_short_max}\"**
                - Showing composite of {len(filtered_df)} configuration(s)
                - Envelope represents achievable dimensions across all configs
                """)
            else:
                st.info(f"""
                - Maximum Long Edge: **{core_long_max}\"**
                - Maximum Short Edge: **{core_short_max}\"**
                - Max Size: **{core_long_max}\" × {core_short_max}\"**
                - Max Area: **{core_long_max * core_short_max} sq in** ({(core_long_max * core_short_max)/144:.1f} sq ft)
                """)
            
            # Technical Limit specifications
            st.markdown("**Technical Limit** (Premium Cost)")
            st.warning(f"""
            - Maximum Long Edge: **{tech_long_max}\"**
            - Maximum Short Edge: **{tech_short_max}\"**
            - Max Size: **{tech_long_max}\" × {tech_short_max}\"**
            - Max Area: **{tech_long_max * tech_short_max} sq in** ({(tech_long_max * tech_short_max)/144:.1f} sq ft)
            """)
            
            # Minimum size
            st.markdown("**Minimum Size Constraint**")
            st.error(f"""
            - At least one edge must be **16\"** or greater
            """)
            
            # Additional notes
            st.markdown("---")
            st.markdown("### 📝 Notes")
            
            if show_all_configs:
                st.markdown("""
                - **Composite envelope**: Shows the union of all matching configurations
                - **True capabilities**: Outer boundary shows actual maximum achievable in any dimension
                - Example: Can achieve 120"×59" OR 100"×72", creating an L-shaped envelope
                - Hover over chart to see dimensions at any point
                - Select specific values to see one configuration
                """)
            else:
                st.markdown("""
                - Hover over the chart to see dimensions and pricing info
                - Hover snaps to nearest 1" increment
                - White areas do not meet minimum size requirements
                - The chart shows both possible orientations (portrait and landscape)
                - Core Range represents the most cost-effective production envelope
                - Technical Limit sizes will incur a cost premium
                - Select "Any" in any dropdown to see overall maximum sizes
                """)
    else:
        st.error("No configuration found for the selected parameters. Please check your data file.")

if __name__ == "__main__":
    main()
