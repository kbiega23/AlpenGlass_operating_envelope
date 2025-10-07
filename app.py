# Add corner labels for key dimensions with hover info
    # When showing all configs, show labels for the actual achievable corners
    if show_all and all_configs_df is not None and not all_configs_df.empty:
        annotations = []
        
        # Get all unique corner combinations from the configs - keep core and tech separate
        core_corners_set = set()
        tech_corners_set = set()
        
        for idx, row in all_configs_df.iterrows():
            c_long = row['CoreRange_ maxlongedge_inches']
            c_short = row['CoreRange_maxshortedge_inches']
            t_long = row['Technical_limit_long edge_inches']
            t_short = row['Technical_limit_short edge_inches']
            
            # Add core range corners (both orientations)
            core_corners_set.add((c_long, c_short))
            core_corners_set.add((c_short, c_long))
            
            # Add tech limit corners (both orientations) - SEPARATE from core
            tech_corners_set.add((t_long, t_short))
            tech_corners_set.add((t_short, t_long))
        
        # Convert to lists and sort
        core_corners = sorted(list(core_corners_set), key=lambda p: (p[0], p[1]), reverse=True)
        tech_corners = sorted(list(tech_corners_set), key=lambda p: (p[0], p[1]), reverse=True)
        
        # For core range, find Pareto frontier points (outer boundary of blue area)
        core_frontier = []
        for x, y in core_corners:
            # A point is on the frontier if no other point dominates it in both dimensions
            is_dominated = False
            for x2, y2 in core_corners:
                if x2 > x and y2 > y:
                    is_dominated = True
                    break
            if not is_dominated:
                core_frontier.append((x, y))
        
        # Sort core frontier by distance from origin to get the actual corner points
        core_frontier_sorted = sorted(core_frontier, key=lambda p: (p[0]**2 + p[1]**2), reverse=True)
        
        # Add BLUE labels for CORE frontier points - only the actual outer corners
        labeled_core = set()
        for x, y in core_frontier_sorted[:6]:  # Take top candidates
            # Only label if this point is truly on the outer edge and not already labeled
            if (x, y) not in labeled_core:
                # Check if this is a corner point (has both high x OR high y compared to other core points)
                is_corner = True
                for x2, y2 in core_frontier:
                    if (x2, y2) != (x, y):
                        # If there's another point that's better in BOTH dimensions, skip this one
                        if x2 >= x and y2 >= y and (x2 > x or y2 > y):
                            is_corner = False
                            break
                
                if is_corner:
                    labeled_core.add((x, y))
                    # Position arrow based on which quadrant the point is in
                    if x >= y:  # More horizontal
                        ax_offset = 25
                        ay_offset = -25
                    else:  # More vertical
                        ax_offset = -25
                        ay_offset = 25
                    
                    annotations.append(
                        dict(x=x, y=y, 
                             text=f"{x}\" × {y}\"<br>{(x*y)/144:.1f} sq ft",
                             showarrow=True, arrowhead=2, 
                             ax=ax_offset, 
                             ay=ay_offset,
                             arrowcolor="rgba(33, 150, 243, 1)",
                             bgcolor="rgba(33, 150, 243, 0.8)", 
                             font=dict(color="white", size=10))
                    )
        
        # For tech limit, find Pareto frontier points (outer boundary of orange area)
        tech_frontier = []
        for x, y in tech_corners:
            is_dominated = False
            for x2, y2 in tech_corners:
                if x2 > x and y2 > y:
                    is_dominated = True
                    break
            if not is_dominated:
                tech_frontier.append((x, y))
        
        # Sort tech frontier by distance from origin
        tech_frontier_sorted = sorted(tech_frontier, key=lambda p: (p[0]**2 + p[1]**2), reverse=True)
        
        # Add ORANGE labels for TECH frontier points - only corners not already labeled as core
        labeled_tech = set()
        for x, y in tech_frontier_sorted[:6]:
            # Only label tech points that are NOT already labeled as core range points
            if (x, y) not in labeled_core and (x, y) not in labeled_tech:
                # Check if this point is truly on the tech outer edge
                is_corner = True
                for x2, y2 in tech_frontier:
                    if (x2, y2) != (x, y):
                        if x2 >= x and y2 >= y and (x2 > x or y2 > y):
                            is_corner = False
                            break
                
                if is_corner:
                    labeled_tech.add((x, y))
                    # Position arrow based on which quadrant - offset more to avoid core labels
                    if x >= y:
                        ax_offset = 40
                        ay_offset = -40
                    else:
                        ax_offset = -40
                        ay_offset = 40
                    
                    annotations.append(
                        dict(x=x, y=y, 
                             text=f"{x}\" × {y}\"<br>{(x*y)/144:.1f} sq ft",
                             showarrow=True, arrowhead=2, 
                             ax=ax_offset, 
                             ay=ay_offset,
                             arrowcolor="rgba(255, 152, 0, 1)",
                             bgcolor="rgba(255, 152, 0, 0.8)", 
                             font=dict(color="white", size=10))
                    )
