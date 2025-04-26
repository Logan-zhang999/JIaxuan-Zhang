import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

# 1. Reading data from a CSV file
df = pd.read_csv("C:/Users/lenovo/Desktop/Results_21MAR2022_nokcaladjust.csv")

# 2. Environmental indicator definitions and labels
radar_vars = [
    "mean_ghgs", "mean_land", "mean_watscar", "mean_eut",
    "mean_ghgs_ch4", "mean_ghgs_n2o", "mean_bio", "mean_watuse", "mean_acid"
]

label_dict = {
    "mean_ghgs": "Greenhouse Gas Emissions",
    "mean_land": "Land Use",
    "mean_watscar": "Water Scarcity",
    "mean_eut": "Eutrophication Potential",
    "mean_ghgs_ch4": "Methane Emissions",
    "mean_ghgs_n2o": "Nitrous Oxide Emissions",
    "mean_bio": "Biodiversity Impact",
    "mean_watuse": "Agricultural Water Use",
    "mean_acid": "Acidification Potential"
}
indicators = [label_dict[v] for v in radar_vars]

# 3. Age group treatment
df['age_group'] = df['age_group'].astype(str)
age_groups = ['20-29', '30-39', '40-49', '50-59', '60-69', '70-79']
df = df[df['age_group'].isin(age_groups)]

# 4. Data grouping and normalization
df[radar_vars] = df[radar_vars].apply(pd.to_numeric, errors='coerce').fillna(0)
# Group by diet_group, sex and age_group
grouped_by_age = df.groupby(['diet_group', 'sex', 'age_group'])[radar_vars].mean().reset_index()

total_age_grouped = df.groupby(['diet_group', 'sex'])[radar_vars].mean().reset_index()
total_age_grouped['age_group'] = 'All Ages'

total_sex_grouped = df.groupby(['diet_group'])[radar_vars].mean().reset_index()
total_sex_grouped['sex'] = 'Total'
total_sex_grouped['age_group'] = 'All Ages'

total_for_each_age = df.groupby(['diet_group', 'age_group'])[radar_vars].mean().reset_index()
total_for_each_age['sex'] = 'Total'

grouped = pd.concat([grouped_by_age, total_age_grouped, total_sex_grouped, total_for_each_age], ignore_index=True)

for var in radar_vars:
    range_val = grouped[var].max() - grouped[var].min()
    if range_val > 0:
        grouped[var] = (grouped[var] - grouped[var].min()) / range_val
    else:
        grouped[var] = 0  # 如果所有值相同，则设置为0

# 5. Convert to long format
plot_data = grouped.melt(id_vars=['diet_group', 'sex', 'age_group'], value_vars=radar_vars,
                         var_name='indicator', value_name='value')
plot_data['indicator'] = plot_data['indicator'].map(label_dict)
plot_data['value'] = plot_data['value'].fillna(0)

# 6. Initialize the graphics
fig = go.Figure()

sex_list = sorted(grouped['sex'].unique())
age_list = sorted(grouped['age_group'].unique(), key=lambda x: 0 if x == 'All Ages' else int(x.split('-')[0]))

default_sex = 'Total'
default_age = 'All Ages'

colors = {
    'fish': '#00BFFF',  # DeepSkyBlue
    'meat100': '#FF4500',  # OrangeRed
    'meat50': '#32CD32',  # LimeGreen
    'vegan': '#FF69B4',  # HotPink
    'veggie': '#FFD700'  # Gold
}
fill_colors = {k: f"rgba{tuple(list(int(c.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) + [0.2])}"
               for k, c in colors.items()}

diet_display_names = {
    'fish': 'Fish-based Diet',
    'meat100': 'Full Meat Diet',
    'meat50': 'Reduced Meat Diet (50%)',
    'vegan': 'Vegan Diet',
    'veggie': 'Vegetarian Diet'
}

# 7. Add traces for all combinations
for sex in sex_list:
    for age in age_list:
        filtered_data = plot_data[(plot_data['sex'] == sex) & (plot_data['age_group'] == age)]

        diet_groups = sorted(filtered_data['diet_group'].unique())

        for diet in diet_groups:
            diet_data = filtered_data[filtered_data['diet_group'] == diet]

            if len(diet_data) < len(radar_vars):
                print(f"Warning: Incomplete data for {diet} ({sex}, {age})")
                continue

            diet_data = diet_data.sort_values('indicator', key=lambda x: [indicators.index(i) for i in x])

            r = diet_data['value'].tolist()
            theta = diet_data['indicator'].tolist()

            is_visible = (sex == default_sex) and (age == default_age)

            display_name = diet_display_names.get(diet, diet)

            fig.add_trace(go.Scatterpolar(
                r=r + [r[0]],
                theta=theta + [theta[0]],
                fill='toself',
                fillcolor=fill_colors.get(diet, 'rgba(128, 128, 128, 0.2)'),
                name=display_name,
                visible=is_visible,
                line=dict(width=3, color=colors.get(diet, '#333333')),
                opacity=0.8,
                hovertemplate=f"{display_name}<br>%{{theta}}: %{{r:.3f}}<extra>({sex}, {age})</extra>"
            ))

# 8. Setting layout and style
fig.update_layout(
    title=dict(
        text=f"Environmental Impact by Diet Group ({default_sex}, {default_age})",
        x=0.5,
        xanchor="center",
        font=dict(size=22, family="Arial", color="#ffffff")
    ),
    template="plotly_dark",
    font=dict(family="Arial", size=14, color="#ffffff"),
    polar=dict(
        bgcolor="rgba(50, 50, 50, 0.8)",
        radialaxis=dict(
            visible=True,
            range=[0, 1],
            showline=True,
            linewidth=1,
            gridcolor="#777",
            tickfont=dict(size=12, color="#ffffff")
        ),
        angularaxis=dict(
            showline=True,
            linewidth=1,
            gridcolor="#777",
            tickfont=dict(size=14, color="#ffffff", weight="bold")
        )
    ),
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="right",
        x=1.2,  # 位置更靠右以为控件腾出空间
        font=dict(size=14, color="#ffffff"),
        bgcolor="rgba(0, 0, 0, 0.6)",
        bordercolor="#ffffff",
        borderwidth=1,
        title=dict(text="Diet Groups", font=dict(size=16, color="#ffffff", family="Arial Bold"))
    ),
    margin=dict(l=20, r=150, t=120, b=80),  # 减少右边距
    showlegend=True,
    hovermode="closest",
    dragmode="pan",
    paper_bgcolor="#222",
    plot_bgcolor="#222"
)

# 9. HTML Templates
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Environmental Impact by Diet Group</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #151515;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        .container {{
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            box-sizing: border-box;
            position: relative;
        }}
        .header {{
            text-align: center;
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 1px solid #444;
        }}
        .header h1 {{
            font-size: 28px;
            margin: 0;
            color: #f0f0f0;
        }}
        .header p {{
            font-size: 16px;
            margin: 10px 0 0;
            color: #aaa;
        }}
        #plotly-div {{
            width: 100%;
            height: 700px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        }}
        .filter-controls {{
            background-color: rgba(20, 20, 20, 0.9);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
            border: 2px solid #3080e8;
            display: flex;
            justify-content: center;
            gap: 30px;
            position: relative; 
            z-index: 100; 
        }}
        .control-group {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .control-label {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
            color: white;
        }}
        select {{
            padding: 10px 15px;
            background-color: #333;
            color: white;
            border: 2px solid #3080e8;
            border-radius: 5px;
            font-size: 16px;
            min-width: 150px;
            cursor: pointer;
            outline: none;
            appearance: auto; 
        }}
        select:hover {{
            background-color: #444;
        }}
        select:focus {{
            box-shadow: 0 0 8px rgba(48, 128, 232, 0.8);
        }}
        .legend-note {{
            margin: 20px 0;
            padding: 15px;
            background-color: rgba(0, 0, 0, 0.3);
            border-radius: 6px;
            font-size: 14px;
            line-height: 1.5;
            color: #ccc;
        }}
        .diet-color {{
            display: inline-block;
            width: 12px;
            height: 12px;
            margin-right: 5px;
            border-radius: 50%;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 14px;
            color: #888;
            padding: 20px 0;
            border-top: 1px solid #444;
        }}
        @keyframes highlight {{
            0% {{ box-shadow: 0 0 5px #3080e8; }}
            50% {{ box-shadow: 0 0 20px #3080e8; }}
            100% {{ box-shadow: 0 0 5px #3080e8; }}
        }}
        .highlight {{
            animation: highlight 2s infinite;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Environmental Impact by Diet Group</h1>
            <p>Analysis of different dietary choices and their environmental footprints</p>
        </div>

        <div class="filter-controls highlight" id="filter-controls">
            <div class="control-group">
                <div class="control-label">SELECT GENDER</div>
                <select id="sex-select">
                    {sex_options}
                </select>
            </div>

            <div class="control-group">
                <div class="control-label">SELECT AGE GROUP</div>
                <select id="age-select">
                    {age_options}
                </select>
            </div>
        </div>

        <div id="plotly-div"></div>

        <div class="legend-note">
            <p><strong>About this visualization:</strong> This radar chart shows the environmental impact of different diet groups across multiple sustainability metrics. Each diet is represented by a unique color: 
            <span class="diet-color" style="background-color: #00BFFF;"></span> Fish-based, 
            <span class="diet-color" style="background-color: #FF4500;"></span> Full Meat, 
            <span class="diet-color" style="background-color: #32CD32;"></span> Reduced Meat, 
            <span class="diet-color" style="background-color: #FF69B4;"></span> Vegan, and 
            <span class="diet-color" style="background-color: #FFD700;"></span> Vegetarian.
            Lower values (closer to center) indicate less environmental impact.</p>
        </div>

        <div class="footer">
            Created with Plotly and Python • Environmental Impact Analysis • Data normalized for comparison
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const figureData = {figure_data};
            const figureLayout = {figure_layout};

            Plotly.newPlot('plotly-div', figureData, figureLayout, {{responsive: true}});

            const sexSelect = document.getElementById('sex-select');
            const ageSelect = document.getElementById('age-select');
            const filterControls = document.getElementById('filter-controls');

            sexSelect.addEventListener('change', updateChart);
            ageSelect.addEventListener('change', updateChart);

            setTimeout(() => {{
                filterControls.classList.remove('highlight');
            }}, 5000);

            function updateChart() {{
                const selectedSex = sexSelect.value;
                const selectedAge = ageSelect.value;

                Plotly.relayout('plotly-div', {{
                    'title.text': `Environmental Impact by Diet Group (${{selectedSex}}, ${{selectedAge}})`
                }});

                const updatedVisibility = figureData.map(trace => {{
                    const hoverExtra = trace.hovertemplate || '';
                    const matches = hoverExtra.match(/\\(([^)]+)\\)/);

                    if (matches && matches[1]) {{
                        const [traceSex, traceAge] = matches[1].split(', ');
                        return (traceSex === selectedSex && traceAge === selectedAge);
                    }}
                    return false;
                }});

                Plotly.restyle('plotly-div', {{
                    visible: updatedVisibility
                }});
            }}

            console.log("Filter controls initialized");
            console.log("Available sex options:", sexSelect.options.length);
            console.log("Available age options:", ageSelect.options.length);
        }});
    </script>
</body>
</html>
"""

sex_options = ""
for sex in sex_list:
    selected = "selected" if sex == default_sex else ""
    sex_options += f'<option value="{sex}" {selected}>{sex}</option>\n'

age_options = ""
for age in age_list:
    selected = "selected" if age == default_age else ""
    age_options += f'<option value="{age}" {selected}>{age}</option>\n'

figure_data = json.dumps(fig.to_dict()["data"])
figure_layout = json.dumps(fig.to_dict()["layout"])

html_content = html_template.format(
    sex_options=sex_options,
    age_options=age_options,
    figure_data=figure_data,
    figure_layout=figure_layout
)

with open("environmental_impact_fixed.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Fixed interactive visualization created: environmental_impact_fixed.html")

#fig.show()