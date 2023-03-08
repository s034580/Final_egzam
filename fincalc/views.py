import base64
from io import BytesIO
from matplotlib.figure import Figure
import seaborn as sns
from pdb import post_mortem
from flask import Blueprint, g, flash, redirect, render_template, request, url_for

bp = Blueprint('views', __name__)

@bp.route('/', methods=('GET','POST'))
def index():
    return render_template('index.html')

@bp.route('/loan', methods=('GET', 'POST'))
def loan():
    if request.method == 'POST':
        if 'reset' in request.form:
                return redirect(url_for('views.loan'))
        error = None
        if not request.form['loanAmount']:
            error = "Loan amount is required"
        elif (not request.form['years'] and not request.form['months']):
            error = "You must enter a minimum of 1 month or 1 year with a value greater than 0."

        elif not request.form['interestRate'] or float(request.form['interestRate']) <= 0:
            error = "Please enter an interest rate greater than 0"
        elif not request.form['payFrequency']:
            error = "Please select your payment frequency"
        if error is not None:
            flash('Error: ' + error)
            return redirect(url_for('views.loan'))
        else:
            loan_amount = float(request.form['loanAmount'])
            interest_rate = float(request.form['interestRate'])
            if len(request.form['years']) == 0:
                years = 0
            else:
                years = int(request.form['years'])
            if len(request.form['months']) == 0:
                months = 0
            else:
                months = int(request.form['months'])
            if years == 0 and months == 0:
                error = "You must enter a minimum of 1 month or 1 year with a value greater than 0."
                flash("Error: " + error)
                return redirect(url_for('views.loan'))
            pay_frequency = request.form['payFrequency']

            total_months = (years * 12) + months
            loan_details = loan_calculator(loan_amount, interest_rate, pay_frequency, total_months)
            loan_chart = pie_chart(loan_amount, float(loan_details["interest_paid"]))

            return render_template('loan.html', LOAN_DETAILS = loan_details, SUBMIT = True, LOAN_CHART = loan_chart)
    return render_template('loan.html', SUBMIT = False)

@bp.route('/invest', methods=('POST','GET'))
def invest():
    if request.method == 'POST':

        if 'reset' in request.form:
                return redirect(url_for('views.invest'))
        error = None
        if not request.form['initialDeposit'] and not request.form['monthlyDeposit']:
            error = 'You must enter a value greater than 0 for either Initial Deposit or Monthtly Deposit.'
        elif not request.form['interestRate']:
            error = 'You must enter an interest rate greater than 0.'
        elif not request.form['years']:
            error = 'You must enter a number of years greater than 0.'
        if error is not None:
            flash('Error: ' + error)
            return redirect(url_for('views.invest'))
        else:

            if len(request.form['initialDeposit']) == 0:
                initial_deposit = 0
            else:
                initial_deposit = float(request.form['initialDeposit'])
            if len(request.form['monthlyDeposit']) == 0:
                monthly_deposit = 0
            else:
                monthly_deposit = float(request.form['monthlyDeposit'])
            if initial_deposit == 0 and monthly_deposit == 0:
                error = 'You must enter a value greater than 0 for either Initial Deposit or Monthtly Deposit.'
                flash('Error: ' + error)
                return redirect(url_for('views.invest'))




            interest_rate = float(request.form['interestRate'])
            years = int(request.form['years'])
            invest_details = invest_calculator(initial_deposit, monthly_deposit, interest_rate, years)
            yearly_returns = invest_details["returns_each_year"]
            invest_graph = line_graph(yearly_returns, years)
            return render_template('invest.html', INVEST_DETAILS = invest_details, SUBMIT = True, INVEST_GRAPH = invest_graph)

    return render_template('invest.html', SUBMIT = False)

def loan_calculator(loan_amount: float, interest_rate: float, pay_frequency: str, total_months: int) -> dict:
    if pay_frequency == 'monthly':
        period_interest = interest_rate / 1000
        total_periods = total_months
    elif pay_frequency == 'bi-weekly':
        period_interest = interest_rate /2600
        total_periods = (total_months / 12) * 26
    else:
        period_interest = interest_rate / 5200
        total_periods = (total_months / 12) * 52
    total_loan_cost = (
        (loan_amount * period_interest * total_periods)
        /(1-(pow(1+ period_interest, -total_periods)))
    )
    period_payment = round(total_loan_cost / total_periods, 2)
    interest_paid = round(total_loan_cost - loan_amount,2)
    total_loan_cost = round(total_loan_cost, 2)
    loan_details = {"total_loan_cost": total_loan_cost, "period_payment": period_payment, "interest_paid": interest_paid, "period_type": pay_frequency}
    return loan_details

def pie_chart(total_loan : float, interest_paid: float) -> base64:
    pie_list = [total_loan, interest_paid] #list of values for pie chart
    pie_labels = ["Principal", "Interest"]
    colors = sns.dark_palette("#198754", reverse=True)
    fig = Figure()
    ax = fig.subplots()
    fig.set_facecolor("#FFF")
    ax.pie(pie_list, labels=pie_labels,colors = colors, autopct='%.1f%%', explode = [0, .025], )
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0.25)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data

def invest_calculator(initial_deposit: float, monthly_deposit: float, avg_annual_rate: float, years: int) -> dict:
    #calculation will be done with monthly compounding so years need to be converted
    initial_deposit_return = initial_deposit * pow((1 + avg_annual_rate / 100), years)
    '''
    for the monthly deposits, we are assuming annual compounding to keep things simple, so _monthly_deposit will be multiplied by 12. Credit to https://www.wallstreetiswaiting.com/running-the-numbers-1/calculating-interest-recurring-payments/ for the math regarding monthly contributions.
    '''
    monthly_deposits_return = (
        monthly_deposit * ((pow((1 +avg_annual_rate / 100), years)-1)/(avg_annual_rate / 100)) * 12

    )

    returns_each_year = []

    for i in range(1, years + 1):
        initial_deposit_yearly = initial_deposit * pow((1 + avg_annual_rate / 100), i)
        monthly_deposits_yearly = (
        monthly_deposit * ((pow((1 +avg_annual_rate / 100), i)-1)/(avg_annual_rate / 100)) * 12
    )
        returns_each_year.append(initial_deposit_yearly + monthly_deposits_yearly)

    total = initial_deposit_return + monthly_deposits_return
    total_deposits = initial_deposit + (monthly_deposit * years * 12)
    # A list of yearly values can also be used to create an informative graph
    total = round(total, 2)
    profit = round(total - total_deposits,2)
    total_str = "{:,.2f}".format(total)
    profit_str = "{:,.2f}".format(profit)
    total_deposits_str = "{:,.2f}".format(round(total_deposits, 2))
    invest_details = {"total": total_str, "years": years, "total_deposits":total_deposits_str, "profit":profit_str, "returns_each_year": returns_each_year}
    return invest_details

def line_graph(running_returns :list, years :int) -> base64:

    years_list = list(range(1, years + 1))
    
    fig = Figure()
    ax = fig.subplots()
    
    fig.set_facecolor("#FFF")
    ax.plot(years_list, running_returns, color="#198754")
    ax.set(title=f"Returns over {years} years", xlabel="Years", ylabel="Returns")
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0.25)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data
