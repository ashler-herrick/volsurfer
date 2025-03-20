import pulp
import numpy as np
from chain import Chain
from vol_surface import VolSurface


dtes = [7,14,21]
vol_surface = VolSurface(
    atm_strike=100,
    dtes=[7,14,21],
    atm_vols=[1.0,0.8,0.7],
    skews=[-0.5,-0.4,-0.2],
    kurtosis=[2,1,0.5],
    )

s_range = np.linspace(80, 120, 40)
chain = Chain(
    dtes=dtes,
    vol_surface=vol_surface,
    underlying_price=100,
    s_range=s_range,
    strike_width=5,
)

prob = pulp.LpProblem("Opt", pulp.LpMaximize)
df = chain.df
delta = df['Delta'].to_dict()
gamma = df['Gamma'].to_dict()
theta = df['Theta'].to_dict()
vega = df['Vega'].to_dict()
price = df['Price'].to_dict()
options = list(df.index)

calls = df[df['Type'] == 'Call'].index.tolist()
puts = df[df['Type'] == 'Put'].index.tolist()

# Set weights for each Greek
w_gamma = 5
w_theta = 1
w_vega  = -0.5

# Tolerance for delta neutrality
epsilon = 0.05
max_loss = 2.5

# Create the optimization problem
prob = pulp.LpProblem("OptionPortfolioOptimization", pulp.LpMaximize)

# Define decision variables for each option
x = pulp.LpVariable.dicts("Contracts", options, lowBound=-8, upBound=8, cat='Integer')

# Define auxiliary variables for the absolute value of each contract
abs_x = pulp.LpVariable.dicts("AbsContracts", options, lowBound=0, cat='Integer')

# Add constraints to relate abs_x to x
for i in options:
    prob += abs_x[i] >= x[i], f"Abs_Positive_{i}"
    prob += abs_x[i] >= -x[i], f"Abs_Negative_{i}"

# Constraint: Total number of contracts (absolute values) cannot exceed 10
prob += pulp.lpSum([abs_x[i] for i in options]) <= 16, "TotalContractLimit"

prob += pulp.lpSum([price[i] * x[i] for i in options]) <= max_loss, "MaxLossConstraint"
prob += pulp.lpSum([price[i] * x[i] for i in options]) >= -max_loss, "DebitStratConstraint"

prob += pulp.lpSum([x[i] for i in calls]) == 0, "Call_Net_Neutral"
prob += pulp.lpSum([x[i] for i in puts]) == 0, "Put_Net_Neutral"

# Define the objective: maximize weighted sum of gamma, theta, and vega exposures
prob += pulp.lpSum([
    w_gamma * gamma[i] * x[i] +
    w_theta * theta[i] * x[i] +
    w_vega  * vega[i]  * x[i]
    for i in options
]), "TotalGreekExposure"

# Delta neutrality constraints (within epsilon tolerance)
prob += pulp.lpSum([delta[i] * x[i] for i in options]) <= epsilon, "Delta_Positive"
prob += pulp.lpSum([delta[i] * x[i] for i in options]) >= -epsilon, "Delta_Negative"

# Add constraints to ensure each Greek is positive
prob += pulp.lpSum([gamma[i] * x[i] for i in options]) >= 0, "Gamma_Positive"
prob += pulp.lpSum([theta[i] * x[i] for i in options]) >= 0, "Theta_Positive"
prob += pulp.lpSum([vega[i]  * x[i] for i in options]) >= 0, "Vega_Positive"

# Solve the problem using the default CBC solver
result_status = prob.solve()

# Display the results
print("Status:", pulp.LpStatus[prob.status])
for option in options:
    print(f"{option}: {x[option].varValue}")

print(chain.df)