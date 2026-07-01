import numpy as np
import plotly.graph_objects as go

# ============================================================
# HYDROFUTUR — 3D Reservoir Visualization
# Version 1.0 — Initial Code (Open for future additions)
# ============================================================

# ============================================================
# SECTION 1: RESERVOIR INPUT PARAMETERS
# ============================================================

reservoir = {
    "x_min": 0,
    "x_max": 5000,
    "y_min": 0,
    "y_max": 5000,
    "depth_top": 2000,
    "depth_base": 2500,
    "GOC": 2100,
    "OWC": 2350,
    "nx": 20,
    "ny": 20,
    "nz": 10,
    "porosity_avg": 0.18,
    "permeability_avg": 150,
    "net_to_gross": 0.75,
    "field_name": "Field A",
}

# ============================================================
# SECTION 2: WELLS (Add more wells later)
# ============================================================

wells = [
    # {"name": "W-01", "x": 1000, "y": 1000, "depth_top": 2050, "depth_base": 2400},
    # {"name": "W-02", "x": 3000, "y": 2500, "depth_top": 2080, "depth_base": 2420},
]

# ============================================================
# SECTION 3: BUILD GRID
# ============================================================

def build_grid(res):
    x = np.linspace(res["x_min"], res["x_max"], res["nx"])
    y = np.linspace(res["y_min"], res["y_max"], res["ny"])
    z = np.linspace(-res["depth_base"], -res["depth_top"], res["nz"])
    X, Y, Z = np.meshgrid(x, y, z)
    return X, Y, Z

def assign_fluids(Z, res):
    fluid = np.zeros_like(Z)
    fluid[Z > -res["GOC"]] = 2
    fluid[(Z <= -res["GOC"]) & (Z > -res["OWC"])] = 1
    fluid[Z <= -res["OWC"]] = 0
    return fluid

def assign_properties(Z, X, Y, res):
    porosity = np.random.normal(res["porosity_avg"], 0.02, Z.shape)
    porosity = np.clip(porosity, 0.05, 0.35)
    permeability = np.random.lognormal(np.log(res["permeability_avg"]), 0.3, Z.shape)
    return porosity, permeability

# ============================================================
# SECTION 4: MODE 1 — FLUID VISUALIZATION
# Gas=RED / Oil=GREEN / Water=BLUE
# ============================================================

def plot_mode1(res):
    X, Y, Z = build_grid(res)
    fluid = assign_fluids(Z, res)

    fig = go.Figure()

    mask_gas = fluid == 2
    if mask_gas.any():
        fig.add_trace(go.Scatter3d(
            x=X[mask_gas].flatten(),
            y=Y[mask_gas].flatten(),
            z=Z[mask_gas].flatten(),
            mode='markers',
            marker=dict(size=3, color='red', opacity=0.4),
            name='Gas'
        ))

    mask_oil = fluid == 1
    if mask_oil.any():
        fig.add_trace(go.Scatter3d(
            x=X[mask_oil].flatten(),
            y=Y[mask_oil].flatten(),
            z=Z[mask_oil].flatten(),
            mode='markers',
            marker=dict(size=3, color='green', opacity=0.5),
            name='Oil'
        ))

    mask_water = fluid == 0
    if mask_water.any():
        fig.add_trace(go.Scatter3d(
            x=X[mask_water].flatten(),
            y=Y[mask_water].flatten(),
            z=Z[mask_water].flatten(),
            mode='markers',
            marker=dict(size=3, color='blue', opacity=0.3),
            name='Water'
        ))

    fig.add_trace(go.Surface(
        x=np.linspace(res["x_min"], res["x_max"], 10),
        y=np.linspace(res["y_min"], res["y_max"], 10),
        z=np.full((10, 10), -res["GOC"]),
        opacity=0.2,
        colorscale=[[0, 'orange'], [1, 'orange']],
        showscale=False,
        name='GOC'
    ))

    fig.add_trace(go.Surface(
        x=np.linspace(res["x_min"], res["x_max"], 10),
        y=np.linspace(res["y_min"], res["y_max"], 10),
        z=np.full((10, 10), -res["OWC"]),
        opacity=0.2,
        colorscale=[[0, 'cyan'], [1, 'cyan']],
        showscale=False,
        name='OWC'
    ))

    fig.update_layout(
        title=f"HYDROFUTUR — 3D Reservoir: {res['field_name']} | MODE 1: Fluid Distribution",
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Depth (m)",
            bgcolor="#040d1a",
            xaxis=dict(gridcolor="#0e2a4a"),
            yaxis=dict(gridcolor="#0e2a4a"),
            zaxis=dict(gridcolor="#0e2a4a"),
        ),
        paper_bgcolor="#040d1a",
        font=dict(color="#e8f0fe"),
        legend=dict(bgcolor="#071428"),
        width=1200,
        height=800,
    )

    return fig

# ============================================================
# SECTION 5: MODE 2 — FULL RESERVOIR WITH REAL COLORS
# ============================================================

def plot_mode2(res):
    X, Y, Z = build_grid(res)
    fluid = assign_fluids(Z, res)
    porosity, permeability = assign_properties(Z, X, Y, res)

    fig = go.Figure()

    fig.add_trace(go.Volume(
        x=X.flatten(),
        y=Y.flatten(),
        z=Z.flatten(),
        value=porosity.flatten(),
        isomin=0.05,
        isomax=0.35,
        opacity=0.1,
        surface_count=15,
        colorscale='RdYlGn',
        colorbar=dict(title="Porosity"),
        name='Rock (Porosity)'
    ))

    fig.add_trace(go.Surface(
        x=np.linspace(res["x_min"], res["x_max"], 10),
        y=np.linspace(res["y_min"], res["y_max"], 10),
        z=np.full((10, 10), -res["GOC"]),
        opacity=0.3,
        colorscale=[[0, '#ff4444'], [1, '#ff4444']],
        showscale=False,
        name='GOC'
    ))

    fig.add_trace(go.Surface(
        x=np.linspace(res["x_min"], res["x_max"], 10),
        y=np.linspace(res["y_min"], res["y_max"], 10),
        z=np.full((10, 10), -res["OWC"]),
        opacity=0.3,
        colorscale=[[0, '#4444ff'], [1, '#4444ff']],
        showscale=False,
        name='OWC'
    ))

    fig.update_layout(
        title=f"HYDROFUTUR — 3D Reservoir: {res['field_name']} | MODE 2: Full Reservoir Properties",
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Depth (m)",
            bgcolor="#040d1a",
        ),
        paper_bgcolor="#040d1a",
        font=dict(color="#e8f0fe"),
        width=1200,
        height=800,
    )

    return fig

# ============================================================
# SECTION 6: MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  HYDROFUTUR — 3D Reservoir Visualization v1.0")
    print("=" * 60)
    print(f"\n  Field: {reservoir['field_name']}")
    print(f"  GOC: {reservoir['GOC']} m")
    print(f"  OWC: {reservoir['OWC']} m")

    print("\n  Generating Mode 1: Fluid Visualization...")
    fig1 = plot_mode1(reservoir)
    fig1.write_html("reservoir_mode1_fluids.html")
    fig1.show()

    print("\n  Generating Mode 2: Full Reservoir Properties...")
    fig2 = plot_mode2(reservoir)
    fig2.write_html("reservoir_mode2_full.html")
    fig2.show()

    print("\n  Done!")
    print("  - reservoir_mode1_fluids.html")
    print("  - reservoir_mode2_full.html")

# ============================================================
# FUTURE: Wells, Seismic, Faults, Production simulation
# ============================================================