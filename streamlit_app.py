import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tmval import Annuity, Rate
import numpy_financial as npf

def pmnt_growing_annuity(pv, rate, growth, periods):
    return pv/((1/(rate-growth))*(1- ((1+growth)/(1+rate))**periods))

def pv_growing_annuity(pmnt, rate, growth, periods):
    return pmnt * ((1/(rate-growth))*(1 - ((1+growth)/(1+rate))**periods))

def pv_growing_annuity_due(pmnt, rate, growth, periods):
    return pmnt * (1+rate) * ((1/(rate-growth))*(1 - ((1+growth)/(1+rate))**periods))

st.set_page_config(
    page_title="Pension Planning Calculator")

"""
# Pension Planning Calculatior - Lite Version!

In this version of the pension planning calculator we will see how your current financial status matches your pension expectations.

It is, of course, obvious that noone can predict the future and as such the calculator/simulator allows you to tweak the options as you please.

The default options are not a recommendation or financial advice but just an example.

> Note: None of the personal information provided to the calculator is saved in any way! The information will be lost when you refresh the page.

Follow along each section below and enjoy the journey!
"""

st.header("**Current Financial Situation**")

"""
We will start with the basic information about you. First, the date of birth. That is, because we will base all our calculations on this date.

Imagine that, when you decide to go on retirement, the date this will happen will most probably be your birtday celebration at that age.

We will also need to keep track of the amount you currently have in your pension account. This is the balance you have managed to accumulate so far.
We will assume that this balance is as of your last birthday. It will help with our calculations. In the next, more advanced, version of this calculator
we will be more specific about the amounts. For now, it is just enough.

Next, we will need the monthly savings/deposits to the pension account. While we ask for the monthly depositions we will assume, in our calculations, that
a 12*deposit_amount is placed in the account at the end of each year. This means that it will start accruing interest as well as grow from the next year.
"""

personalInfo, expectations = st.columns(2)

with personalInfo:
    st.subheader("Birth Date")
    birth_date = st.date_input("When\'s your birthday", datetime(1982, 4, 20).date())
    
    st.subheader("Initial Savings")
    initial_amount_for_pension = st.number_input("Enter the amount you already have in your pension plan($): ", min_value=0.0, format='%f')

with expectations:
    st.subheader("Retirement Age")
    retirement_age = st.selectbox('When do you plan to Retire?', tuple(i for i in range(55,75,1)), index=10)
    
    st.subheader("Estimated Death Age")
    life_expectancy = st.selectbox('When do you estimate to die?', tuple(i for i in range(55,115,1)), index=45)

today_date = datetime.now().date()
this_year_birthday = today_date.replace(month=birth_date.month, day=birth_date.day)
next_year_birthday = this_year_birthday + relativedelta(years=1)
most_resent_birthday = this_year_birthday - relativedelta(years=1) if today_date < this_year_birthday else this_year_birthday

retirement_date = birth_date + relativedelta(years=retirement_age)
years_to_retirement = retirement_date.year - most_resent_birthday.year
# life_expectancy = 100 # That means that some time in the 100th year I die. 100th year starts 2084 which is the last payment
terminal_date = birth_date + relativedelta(years=life_expectancy)
count_down_years = terminal_date.year - retirement_date.year

st.markdown(f"""You were born {birth_date} and your most recent birthday was on {most_resent_birthday}.
You plan to retire on {retirement_date} and eventually die sometime in year {terminal_date}!

As of {most_resent_birthday} you have saved a total of {initial_amount_for_pension}.

Let's move to the next section and go deeper into the years you enjoy your pension.

Fill the form below ...
""")

st.header("**While In Pension**")
colPostForecast1, colPostForecast2 = st.columns(2)

with colPostForecast1:
    st.subheader("Monthly pension withdrawal")
    monthly_cost_now_net = st.number_input("Expected net monthly payment while in pension (in taday's terms)($): ", min_value=0.0, format='%f')
    
    st.subheader("Withdrawals Growth")
    growth_post_retirement = st.number_input("Annual growth of your withdrawals(%): ", min_value=0.0, format='%f', value=3.35747)
    
    st.subheader("Tax Rate while in Pension")
    tax_rate = st.number_input("Enter your tax rate(%): ", min_value=0.0, format='%f')

with colPostForecast2:
    st.subheader("Inflation Rate")
    inf_annual_post = st.number_input("Annualized inflation rate(%): ", min_value=0.0, format='%f', value=3.35747)
    
    st.subheader("Post-Retirement Market Rate")
    market_rate_post_retirement = st.number_input("Annualized market rate post(%): ", min_value=0.0, format='%f', value=5.26)

tax_rate = tax_rate / 100.0
growth_post_retirement = growth_post_retirement / 100.0
inf_annual_post = inf_annual_post / 100.0
market_rate_post_retirement = market_rate_post_retirement / 100.0

annual_cost_now_net = 12 * monthly_cost_now_net
monthly_needed_at_retirement_net = monthly_cost_now_net * (1+inf_annual_post)**years_to_retirement
annual_needed_at_retirement_net = monthly_needed_at_retirement_net * 12
annual_needed_at_retirement_gross = annual_needed_at_retirement_net * (1 + tax_rate)

time_range_from_retirement_to_death = pd.to_datetime(pd.Series([f'{retirement_date.year + i}-{retirement_date.month}-{retirement_date.day}' for i in range(0,terminal_date.year-retirement_date.year,1)]),format='%Y-%m-%d')
pension_balance = pd.DataFrame(data=[annual_needed_at_retirement_gross]*time_range_from_retirement_to_death.shape[0], columns=["Outflow"], index=time_range_from_retirement_to_death)
pension_balance['InflationFactor'] = pd.Series([(1+growth_post_retirement)**i for i in range(0, time_range_from_retirement_to_death.shape[0], 1)]).values
pension_balance['InflatedOutflow'] = pension_balance['InflationFactor'] * pension_balance['Outflow']
assert annual_needed_at_retirement_gross * (1+growth_post_retirement)**(time_range_from_retirement_to_death.shape[0]-1) == pension_balance['InflatedOutflow'][-1]
pv_pension_growing_annuity = Annuity(gr=Rate(market_rate_post_retirement), n=time_range_from_retirement_to_death.shape[0], gprog=(growth_post_retirement)).pv() * annual_needed_at_retirement_gross
pension_balance['Rate'] = [market_rate_post_retirement] * pension_balance.shape[0]
pension_balance['Balance'] = np.ones(pension_balance.shape[0])
previous_year_balance = pv_pension_growing_annuity
for year in pension_balance.index:
    withdrawn_amount = pension_balance.InflatedOutflow[year]
    rate = pension_balance.Rate[year]
    previous_year_balance = pension_balance.Balance[year] = (previous_year_balance * (1+rate)) - withdrawn_amount

# assert pension_balance.Balance[-1].round(6) == 0
# assert (pension_balance.Balance[-2] * (1+market_rate_post_retirement)).round(6) == pension_balance.InflatedOutflow[-1].round(6)


st.markdown(f"""With today's cost of living standards, you would feel comfortable with a monthly pension payment of {monthly_cost_now_net}.
That is an annual cost in today's terms of {annual_cost_now_net}

With an inflation rate at {inf_annual_post*100.0:.2f}% the net amount you will need as a first pension salary is {monthly_needed_at_retirement_net:.2f}.
That is an annual amount of {annual_needed_at_retirement_net:.2f}. Since the retirement tax rate is {tax_rate*100.0:.2f}% the gross amount you will need to pay yourself
the moment you start your retirement ({retirement_date}) should be {annual_needed_at_retirement_gross:.2f}.

As you can see in the `CashFlows` graph below, an initial amount of {annual_needed_at_retirement_gross:.2f} needs to be paid to you at {retirement_date}. Of cource, you will split it down
to monthly payments as we described above, but every {retirement_date.month}-{retirement_date.day} of each consecutive year, you will need to be able to withdraw
the amount you need.

Now, due to inflation (mostly), to be able to keep the same quality of leaving, you will need to grow the annual amount you pay yourself by a growth rate of {growth_post_retirement*100.0:.2f}% every year.
That means that at the beginning of the second year after retirement ({retirement_date+relativedelta(years=1)}) you will need to pay yourself {annual_needed_at_retirement_gross * (1+growth_post_retirement)**1:.2f},
the third year ({retirement_date+relativedelta(years=2)}) {annual_needed_at_retirement_gross * (1+growth_post_retirement)**2:.2f} and so on.
At the start of the terminal year ({terminal_date-relativedelta(years=1)}) you will need a wooping amount of {pension_balance['InflatedOutflow'][-1]:.2f}.

All these annual payments will need to be financed of cource! The second part of the graph below shows the optimal balance of your pension account at the beginning
of each year. The amount shown per year is after you have withdrawn your annual payment. The last payment date is {terminal_date-relativedelta(years=1)}
 and if all goes ok you should see a 0 or even possitive amount in your account.
""")

fig = make_subplots(rows=2, cols=1, subplot_titles=("CashFlows", "Account Balance"))
fig.add_trace(
    go.Bar(x=pension_balance.index, y=pension_balance.InflatedOutflow),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=pension_balance.index, y=pension_balance.Balance),
    row=2, col=1
)

fig.update_layout(height=1000, title_text="Retirement CFs & Balance", showlegend=False)
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Amount", row=1, col=1)
fig.update_yaxes(title_text="Amount", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.header("**The path towards retirement**")
colPreForecast1, colPreForecast2 = st.columns(2)

with colPreForecast1:
    st.subheader("Deposit Growth")
    growth_pre_retirement = st.number_input("Annual growth of your deposits(%): ", min_value=0.0, format='%f', value=3.35747)

with colPreForecast2:
    st.subheader("Pre-Retirement Market Rate")
    market_rate_pre_retirement = st.number_input("Annualized market rate pre(%): ", min_value=0.0, format='%f', value=5.26)

growth_pre_retirement = growth_pre_retirement / 100.0
market_rate_pre_retirement = market_rate_pre_retirement / 100.0

pv_pension_most_resent_birthday = pv_pension_growing_annuity /(1+market_rate_pre_retirement)**(years_to_retirement-1)
initial_annual_deposit_amount = pmnt_growing_annuity(pv_pension_most_resent_birthday - initial_amount_for_pension, market_rate_pre_retirement, growth_pre_retirement, years_to_retirement)

time_range_from_now_to_retirement = pd.to_datetime(pd.Series([f'{i}-{retirement_date.month}-{retirement_date.day}' for i in range(most_resent_birthday.year, retirement_date.year+1,1)]),format='%Y-%m-%d')
pre_pension_balance = pd.DataFrame(data=[-initial_amount_for_pension] + [-initial_annual_deposit_amount * (1+growth_pre_retirement)** i for i in range(0, time_range_from_now_to_retirement.shape[0]-1, 1)], columns=["Depositions"], index=time_range_from_now_to_retirement)
pre_pension_balance['Rate'] = [1+market_rate_pre_retirement] * pre_pension_balance.shape[0]
pre_pension_balance['Balance'] = np.zeros(pre_pension_balance.shape[0])
previous_year_amount = 0
for year in pre_pension_balance.index:
    depo = pre_pension_balance.Depositions[year]
    rate = pre_pension_balance.Rate[year]
    if year == most_resent_birthday:
        previous_year_amount = pre_pension_balance.Balance[year] = - depo
        continue
    previous_year_amount = pre_pension_balance.Balance[year] = previous_year_amount*rate - depo

# assert pension_balance.Balance[0].round(2) + pension_balance.InflatedOutflow[0].round(2) == pre_pension_balance.Balance[-1].round(2) # The balance we have in the account when we first get into pension is after we have taken out the first pension payment 

st.markdown(f"""Well well, we know that just the day before {retirement_date} we will need to have a total of {pension_balance.Balance[0] + pension_balance.InflatedOutflow[0]:.2f} in our
pension account (Just the exact {retirement_date} we withdraw the first pension annual amount of {pension_balance.InflatedOutflow[0]:.2f} and we are left with {pension_balance.Balance[0]:.2f}). To achieve that, we need to be investing. We will do that by placing our money in an investment account which we estimate it will return an annual rate of
{market_rate_pre_retirement*100.0:.2f}%. We also think that we should be growing our annual deposits to the pension account to account for the inflation (mostly).
This growth is at {growth_pre_retirement*100:.2f}% per year.

According to the information above, we would need a total of {pv_pension_most_resent_birthday:.2f} in our account as of {most_resent_birthday}. If we had that,
and the market was in our favor for the years to come (at an annual {market_rate_pre_retirement*100.0:.2f}%) we wouldn't need to make any deposits to our account again
and retire properly at {retirement_date}.

However, we only have {initial_amount_for_pension} and in order to reach our target, we need to be depositing (and probably growing) to our account.

So far, we have to be depositing {initial_annual_deposit_amount/12:.2f} ({initial_annual_deposit_amount:.2f} annual) per month to our account and each turn of the year we should be growing that amount by {growth_pre_retirement*100:.2f}%. 
""")

fig = make_subplots(rows=2, cols=1, subplot_titles=("CashFlows", "Account Balance"))
fig.add_trace(
    go.Bar(x=pre_pension_balance.index, y=pre_pension_balance.Depositions),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=pre_pension_balance.index, y=pre_pension_balance.Balance),
    row=2, col=1
)

fig.update_layout(height=1000, title_text="Pre-Retirement CFs & Balance", showlegend=False)
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Amount", row=1, col=1)
fig.update_yaxes(title_text="Amount", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.header("**The full picture**")

time_range_from_now_to_death = pd.to_datetime(pd.Series([f'{i}-{most_resent_birthday.month}-{most_resent_birthday.day}' for i in range(most_resent_birthday.year, terminal_date.year, 1)]),format='%Y-%m-%d')
pension_plan = pd.DataFrame(index=time_range_from_now_to_death)
pension_plan.index = pension_plan.index.date
pension_plan['Growth'] = [0,1] + [1+growth_pre_retirement] * (pre_pension_balance.shape[0]-2) + [1+growth_post_retirement] * (pension_balance.shape[0]-1)
pension_plan['Rate'] = [1+market_rate_pre_retirement] * pre_pension_balance.shape[0] + [1+market_rate_post_retirement] * (pension_balance.shape[0]-1)
pension_plan['Balance'] = np.zeros(pension_plan.shape[0])
pension_plan['CF'] = np.zeros(pension_plan.shape[0])
previous_year_cf_pre_retirement = -initial_annual_deposit_amount
previous_year_cf_post_retirement = annual_needed_at_retirement_gross
previous_year_balance_amount = 0
for year in pension_plan.index:
    rate = pension_plan.Rate[year]
    growth = pension_plan.Growth[year]
    if year == most_resent_birthday: # Initial Lump sum
        pension_plan.CF.loc[year] = -initial_amount_for_pension
        previous_year_balance_amount = pension_plan.Balance.loc[year] = initial_amount_for_pension
        continue
    if year < retirement_date:
        previous_year_cf_pre_retirement = pension_plan.CF.loc[year] = previous_year_cf_pre_retirement * growth
        previous_year_balance_amount = pension_plan.Balance.loc[year] = abs(previous_year_balance_amount) * rate + abs(pension_plan.CF[year])
        continue
    if year == retirement_date:
        pension_plan.CF.loc[year] = annual_needed_at_retirement_gross + (previous_year_cf_pre_retirement * growth)
        previous_year_balance_amount = pension_plan.Balance.loc[year] = (abs(previous_year_balance_amount) * rate) + abs(previous_year_cf_pre_retirement * growth) - annual_needed_at_retirement_gross
        continue
    if year > retirement_date:
        previous_year_cf_post_retirement = pension_plan.CF.loc[year] = previous_year_cf_post_retirement * growth
        previous_year_balance_amount = pension_plan.Balance.loc[year] = (abs(previous_year_balance_amount) * rate) - pension_plan.CF[year]
        continue

fig = make_subplots(rows=2, cols=1, subplot_titles=("CashFlows", "Account Balance"))
fig.add_trace(
    go.Bar(x=pension_plan.index, y=pension_plan.CF),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=pension_plan.index, y=pension_plan.Balance),
    row=2, col=1
)

fig.update_layout(height=1000,
                  title_text='CashFlow and Balance forecasting',
                  title_x=0.5,
                  showlegend=False)
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Amount", row=1, col=1)
fig.update_yaxes(title_text="Amount", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.header("**Conclusion**")

st.markdown(f"""I really hope you liked the calculator so far! 

The next phase of such a simulation is to allow for variable market, inflation and growth rates.
This way, we can model different scenarios and plan even better.
My aspiration is to create the next version soon!

If you liked the content so far, buy me a coffee :wink:

Enjoy!
""")

html_buy_me_coffee = """<a href="https://www.buymeacoffee.com/invsnippets"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=invsnippets&button_colour=6f8eec&font_colour=000000&font_family=Comic&outline_colour=000000&coffee_colour=FFDD00" /></a>"""

st.markdown(html_buy_me_coffee, unsafe_allow_html=True)

