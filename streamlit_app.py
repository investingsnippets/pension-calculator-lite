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
    assert rate!=growth, "rate must not equal growht!"
    return pv/((1/(rate-growth))*(1- ((1+growth)/(1+rate))**periods))

def pv_growing_annuity(pmnt, rate, growth, periods):
    assert rate!=growth, "rate must not equal growht!"
    return pmnt * ((1/(rate-growth))*(1 - ((1+growth)/(1+rate))**periods))

def pv_growing_annuity_due(pmnt, rate, growth, periods):
    assert rate!=growth, "rate must not equal growht!"
    return pmnt * (1+rate) * ((1/(rate-growth))*(1 - ((1+growth)/(1+rate))**periods))

st.set_page_config(
    page_title="Pension Planning Calculator",
    layout="wide")

st.markdown("<h1 style='text-align: center; color: black;'>Pension Planning Calculatior</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: grey;'>Lite Version!</h2>", unsafe_allow_html=True)

"""
**_The content, opinions and conclusions on this website are NOT to be construed as financial advice. Please change the inputs according to your belief._**

> Note: None of the personal information provided to the calculator is saved in any way. The information will be lost when you refresh the page.
"""

inf_annual_post=growth_post_retirement=growth_post_retirement=0
tax_rate=0.0
market_rate_pre_retirement=market_rate_post_retirement=0

with st.sidebar:
    st.sidebar.title("Parameters")
    birth_date = st.date_input("Birth Date:", datetime(1980, 1, 1).date(), help="""The birht date is used to show nicer graphs and calculate retirement and terminal dates.
> No personal data is saved. When you refresh or leave the page, the data will vanish. """)

    monthly_cost_now_net = st.number_input("Expected net monthly payment while in pension (in today's terms): ", min_value=0.0, format='%f', help=
        """As if today was your first day at retirement! Based on today's cost of living,
        how much money per month would you be happy living with?""")

    initial_amount_for_pension = st.number_input("Current Balance:", min_value=0.0, format='%f', help="""The balance you have managed to accumulate so far in your pension account.
> We will assume that this balance is as of your last birthday (If you want to be precice, try to estimate your balance at that time).
> It will help with our calculations. In the next, more advanced, version of this calculator, we will be more specific about the amounts.
""")

    with st.expander("Retirement Parameters"):
        retirement_age = st.selectbox('Retirement Age:', tuple(i for i in range(55,75,1)), index=10, help="At what age do you plan to retire?")
        life_expectancy = st.selectbox('Terminal Year:', tuple(i for i in range(55,115,1)), index=45, help="When do you estimate to stop withdrawing from your pension account?")

    with st.expander("Inflation and Taxes"):
        inf_annual_post = st.number_input("Annualized Inflation Rate (%): ", min_value=0.0, format='%f', value=3.8, help="""Inflation in this version of the calculator is static and is used
        to calculate the gross amount needed as a first payment at the retirement date. For example, in USA, during the observation period from 1960 to 2021, the average inflation rate was 3.8% per year""")
        
        growth_pre_retirement = st.number_input("Annual growth of your deposits (%): ", min_value=0.0, format='%f', value=3.8, help="""The percentage in growth of your deposits per year.
            For example, one could increase as much as the inflation increases.""")
        
        growth_post_retirement = st.number_input("Annual growth of your withdrawals (%): ", min_value=0.0, format='%f', value=3.8, help="""The percentage in growth of your withdrawals per year.
            For example, one could increase as much as the inflation increases.""")
        
        tax_rate = st.number_input("Post-Retirement Tax Rate (%): ", min_value=0.0, format='%f', help="""Usually, the gross amount you get paid by your pension account each month is taxed by the state!""")

    with st.expander("Market Returns Expectations"):
        market_rate_pre_retirement = st.number_input("Pre-Retirement Return (%): ", min_value=0.0, format='%f', value=10.15, help="""What is the annualized return on your pension porfolio?
            For example, the average annualized return ot the Standard & Poor's 500 Index (S&P 500) from 1957 through Dec. 31, 2022, is 10.15%.
            **Keep in mind that historical returns are no guarantee of future returns!**""")

        market_rate_post_retirement = st.number_input("Post-Retirement Return (%): ", min_value=0.0, format='%f', value=10.15, help="""What is the annualized return on your pension porfolio?
            For example, the average annualized return ot the Standard & Poor's 500 Index (S&P 500) from 1957 through Dec. 31, 2022, is 10.15%.
            **Keep in mind that historical returns are no guarantee of future returns!**""")

        

if market_rate_pre_retirement == growth_pre_retirement:
    st.error("""Error! `Pre-Retirement Return` must be different than `Annual growth of your deposits`""")
    st.stop()

if market_rate_post_retirement == growth_post_retirement:
    st.error("""Error! `Post-Retirement Return` must be different than `Annual growth of your withdrawals`""")
    st.stop()

today_date = datetime.now().date()
age = today_date.year - birth_date.year - ((today_date.month, today_date.day) < (birth_date.month, birth_date.day))
this_year_birthday = today_date.replace(month=birth_date.month, day=birth_date.day)
next_year_birthday = this_year_birthday + relativedelta(years=1)
most_resent_birthday = this_year_birthday - relativedelta(years=1) if today_date < this_year_birthday else this_year_birthday

retirement_date = birth_date + relativedelta(years=retirement_age)
years_to_retirement = retirement_date.year - most_resent_birthday.year

terminal_date = birth_date + relativedelta(years=life_expectancy)
count_down_years = terminal_date.year - retirement_date.year

tax_rate = tax_rate / 100.0
growth_post_retirement = growth_post_retirement / 100.0
inf_annual_post = inf_annual_post / 100.0
market_rate_post_retirement = market_rate_post_retirement / 100.0
growth_pre_retirement = growth_pre_retirement / 100.0
market_rate_pre_retirement = market_rate_pre_retirement / 100.0

annual_cost_now_net = 12 * monthly_cost_now_net
monthly_needed_at_retirement_net = monthly_cost_now_net * (1+inf_annual_post)**years_to_retirement
annual_needed_at_retirement_net = monthly_needed_at_retirement_net * 12
annual_needed_at_retirement_gross = annual_needed_at_retirement_net * (1 + tax_rate)


pv_pension_growing_annuity = Annuity(gr=Rate(market_rate_post_retirement), n=count_down_years, gprog=(growth_post_retirement)).pv() * annual_needed_at_retirement_gross

pv_pension_most_resent_birthday = pv_pension_growing_annuity /(1+market_rate_pre_retirement)**(years_to_retirement-1)
initial_annual_deposit_amount = pmnt_growing_annuity(pv_pension_most_resent_birthday - initial_amount_for_pension, market_rate_pre_retirement, growth_pre_retirement, years_to_retirement)
initial_annual_deposit_amount = initial_annual_deposit_amount if initial_annual_deposit_amount >= 0 else -1

time_range_from_now_to_death = pd.to_datetime(pd.Series([f'{i}-{most_resent_birthday.month}-{most_resent_birthday.day}' for i in range(most_resent_birthday.year, terminal_date.year, 1)]),format='%Y-%m-%d')
pension_plan = pd.DataFrame(index=time_range_from_now_to_death)
pension_plan.index = pension_plan.index.date
pension_plan['Age'] = [age + i for i in range(0, pension_plan.shape[0])]
pension_plan['Growth'] = [0,1] + [1+growth_pre_retirement] * (years_to_retirement-2) + [1+growth_post_retirement] * count_down_years
pension_plan['Rate'] = [1+market_rate_pre_retirement] * years_to_retirement + [1+market_rate_post_retirement] * count_down_years
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

st.header("**Do you save enough?**")
if initial_annual_deposit_amount/12 >= 0:
    st.markdown(f"""<h2 style='text-align: center; color: black;'>You should be saving at least {initial_annual_deposit_amount/12:.2f} per month</h2>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<h2 style='text-align: center; color: black;'>No need to save more! Good to go with the existing balance!</h2>""", unsafe_allow_html=True)

fig = make_subplots(rows=2, cols=1, subplot_titles=("CashFlows", "Account Balance"))
fig.add_trace(
    go.Bar(x=pension_plan.Age, y=pension_plan.CF),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=pension_plan.Age, y=pension_plan.Balance),
    row=2, col=1
)

fig.update_layout(height=1000,
                  title_text='',
                  title_x=0.5,
                  showlegend=False)
fig.update_xaxes(title_text="Age", tickmode='linear')
fig.update_yaxes(title_text="Amount", row=1, col=1)
fig.update_yaxes(title_text="Amount", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.header("**Current Financial Situation**")

st.markdown(f"""
You were born {birth_date} and you celebrated your most recent birthday on {most_resent_birthday} :fireworks:.
You plan to retire on {retirement_date} and continue withdrawing from your pension account sometime in year {terminal_date.year}!

You have {years_to_retirement} years until you retire, and from that point, you have {count_down_years} years until the end of your pension plan.

As of {most_resent_birthday}, you have saved a total of {initial_amount_for_pension:,}.

Let's move on to the next section and visualise what will happen when you are in retirement.
""")

st.header("**While In Pension**")

time_range_from_retirement_to_death = pd.to_datetime(pd.Series([f'{retirement_date.year + i}-{retirement_date.month}-{retirement_date.day}' for i in range(0,terminal_date.year-retirement_date.year,1)]),format='%Y-%m-%d')
pension_balance = pd.DataFrame(data=[annual_needed_at_retirement_gross]*time_range_from_retirement_to_death.shape[0], columns=["Outflow"], index=time_range_from_retirement_to_death)
pension_balance['Age'] = [age+years_to_retirement + i for i in range(0, pension_balance.shape[0])]
pension_balance['InflationFactor'] = pd.Series([(1+growth_post_retirement)**i for i in range(0, time_range_from_retirement_to_death.shape[0], 1)]).values
pension_balance['InflatedOutflow'] = pension_balance['InflationFactor'] * pension_balance['Outflow']
assert annual_needed_at_retirement_gross * (1+growth_post_retirement)**(time_range_from_retirement_to_death.shape[0]-1) == pension_balance['InflatedOutflow'][-1]
pension_balance['Rate'] = [market_rate_post_retirement] * pension_balance.shape[0]
pension_balance['Balance'] = np.ones(pension_balance.shape[0])
previous_year_balance = pv_pension_growing_annuity
for year in pension_balance.index:
    withdrawn_amount = pension_balance.InflatedOutflow[year]
    rate = pension_balance.Rate[year]
    previous_year_balance = pension_balance.Balance[year] = (previous_year_balance * (1+rate)) - withdrawn_amount

st.markdown(f"""
It's important to mention that due to the time value of money, \$1 today is worth more than \$1 in a year from now. This is due to inflation.
For example, with an inflation rate of 10%, the same product you bought for \$1 today will cost \$1.10 in a year.

The same applies to pensions. With an annual inflation rate of 5%, \$1 today will be worth \${1*(1+0.05)**years_to_retirement:.2f} when you retire :dizzy_face:!

With today's cost of living standards, you would feel comfortable with a monthly pension payment of {monthly_cost_now_net:,.2f}.
That is an annual cost, in today's terms, of {annual_cost_now_net:,.2f}.

With an inflation rate of {inf_annual_post*100.0:.2f}%, the net amount you will need as a first pension salary is {monthly_needed_at_retirement_net:,.2f}.
That is a gross annual amount of {annual_needed_at_retirement_net:,.2f}. Since the retirement tax rate is {tax_rate*100.0:.2f}%, the gross amount you will need
to pay yourself the moment you start your retirement ({retirement_date}) should be {annual_needed_at_retirement_gross:,.2f}.

As you can see in the `CashFlows` section of the image below, an initial annual amount of {annual_needed_at_retirement_gross:,.2f}
needs to be paid to you on {retirement_date} at the age of {retirement_age}. Of cource, you will split it down to equal monthly payments throughout the year.
However, on the `{retirement_date.day}` day of the `{retirement_date.month}` month of each consecutive year, your total account balance should be able to 
allow you to withdraw the annual amount you need and continue growing with the remaining balance.

Now, due to inflation, to be able to keep the same standard of leaving while in pension, you will need to grow
the annual amount you pay yourself by a growth rate. This rate is set to {growth_post_retirement*100.0:.2f}%.
That means that at the beginning of the second year after retirement ({retirement_date+relativedelta(years=1)}) you will
need to pay yourself {annual_needed_at_retirement_gross * (1+growth_post_retirement)**1:.2f},
the third year ({retirement_date+relativedelta(years=2)}) {annual_needed_at_retirement_gross * (1+growth_post_retirement)**2:,.2f} and so on.
At the start of the terminal year ({terminal_date-relativedelta(years=1)}) you will need
an whopping annual amount of {pension_balance['InflatedOutflow'][-1]:,.2f} :cold_sweat:.

All these annual payments will need to be somehow financed, of cource! The second part of the graph below shows
the optimal balance of your pension account at the beginning of each year.
The amount shown per year is _after_ you have withdrawn your annual payment.

On {retirement_date} you should have a total of {pension_balance.Balance[0]:,.2f} :open_mouth:.
The day before ({retirement_date-relativedelta(days=1)}) the balance should be {pension_balance.Balance[0] + pension_balance.InflatedOutflow[0]:,.2f}.

The last payment date is on {terminal_date-relativedelta(years=1)}, and you should see a 0 balance in your account (since you withdrew the last annual payment).
""")

fig = make_subplots(rows=2, cols=1, subplot_titles=("CashFlows", "Account Balance"))
fig.add_trace(
    go.Bar(x=pension_balance.Age, y=pension_balance.InflatedOutflow),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=pension_balance.Age, y=pension_balance.Balance),
    row=2, col=1
)

fig.update_layout(height=1000, title_text="Retirement CFs & Balance", showlegend=False)
fig.update_xaxes(title_text="Age", tickmode='linear')
fig.update_yaxes(title_text="Amount", row=1, col=1)
fig.update_yaxes(title_text="Amount", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.header("**The path towards retirement**")
# assert pension_balance.Balance[0].round(2) + pension_balance.InflatedOutflow[0].round(2) == pre_pension_balance.Balance[-1].round(2) # The balance we have in the account when we first get into pension is after we have taken out the first pension payment 

st.markdown(f"""
Well, we know that just the day before {retirement_date}, you will need to have a total of {pension_balance.Balance[0] + pension_balance.InflatedOutflow[0]:,.2f} in your
pension account. On {retirement_date} you will withdraw the first pension annual amount of {pension_balance.InflatedOutflow[0]:,.2f}, leaving you with {pension_balance.Balance[0]:,.2f}).

To achieve this plan, you need to invest. That is usually done by placing the money in an investment account.
You estimate an annual rate of return of {market_rate_pre_retirement*100.0:.2f}% from your investments.
You also think that you should be increasing your annual deposits to your pension account by {growth_pre_retirement*100:.2f}% (to account for inflation, at least).

According to the information above, you would need a total of {pv_pension_most_resent_birthday:,.2f} in your account as of {most_resent_birthday}. If you had that,
and the market was in your favor for the years to come (at an annual {market_rate_pre_retirement*100.0:.2f}%) you wouldn't need to make any more deposits to your
account again and could retire properly on {retirement_date}.

However, your current balance is {initial_amount_for_pension:,.2f}, and in order to reach your target,
you will need to be depositing money to your account.

So far, you have to be depositing **{initial_annual_deposit_amount/12:,.2f} per month** ({initial_annual_deposit_amount:,.2f} annual) to your
account, and each time you celebrate your next birthday, you should be increasing that amount by {growth_pre_retirement*100:.2f}%.
""")

time_range_from_now_to_retirement = pd.to_datetime(pd.Series([f'{i}-{retirement_date.month}-{retirement_date.day}' for i in range(most_resent_birthday.year, retirement_date.year+1,1)]),format='%Y-%m-%d')
pre_pension_balance = pd.DataFrame(data=[-initial_amount_for_pension] + [-initial_annual_deposit_amount * (1+growth_pre_retirement)** i for i in range(0, time_range_from_now_to_retirement.shape[0]-1, 1)], columns=["Depositions"], index=time_range_from_now_to_retirement)
pre_pension_balance['Age'] = [age + i for i in range(0, pre_pension_balance.shape[0])]
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

fig = make_subplots(rows=2, cols=1, subplot_titles=("CashFlows", "Account Balance"))
fig.add_trace(
    go.Bar(x=pre_pension_balance.Age, y=pre_pension_balance.Depositions),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=pre_pension_balance.Age, y=pre_pension_balance.Balance),
    row=2, col=1
)

fig.update_layout(height=1000, title_text="Pre-Retirement CFs & Balance", showlegend=False)
fig.update_xaxes(title_text="Age", tickmode='linear')
fig.update_yaxes(title_text="Amount", row=1, col=1)
fig.update_yaxes(title_text="Amount", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.header("**Conclusion**")

st.markdown(f"""I really hope you liked the calculator so far!

The next phase of such a simulation is to allow for variable market, inflation and growth rates.
This way, you can model different scenarios and plan even better.
My aspiration is to create the next version soon!

If you liked the content so far, please consider buying me a coffee :wink:

Enjoy!
""")

html_buy_me_coffee = """<a href="https://www.buymeacoffee.com/invsnippets"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=invsnippets&button_colour=6f8eec&font_colour=000000&font_family=Comic&outline_colour=000000&coffee_colour=FFDD00" /></a>"""

st.markdown(html_buy_me_coffee, unsafe_allow_html=True)

