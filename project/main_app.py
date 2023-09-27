import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from sqlalchemy import desc
from werkzeug.datastructures import CombinedMultiDict, MultiDict, ImmutableMultiDict
import json
# validation-email
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

# graph visualization
import plot as pt

app = Flask(__name__)
app.secret_key = 'I think this key needs to be rather long for it to be secure (from java security reading)'
#app.config["SECRET_KEY"] = "a secret key you won't forget"
#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


# --- DATABASE ---

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

# login Manager initialization

login_manager = LoginManager()
login_manager.init_app(app)

# email sending setting
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '1823075630@qq.com'
app.config['MAIL_PASSWORD'] = 'qiqfnymarjtsebfd'
app.config['MAIL_USE_TLS'] = True

# email initialize
mail = Mail(app)


# database contents:
class UserAccount(UserMixin, db.Model):
    __tablename__ = "UserAccount"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True,  nullable=False)
    password = db.Column(db.String(30), nullable=False)  # password_hash
    email = db.Column(db.String(70), unique=True, nullable=False)
    email_active = db.Column(db.Boolean, default=False, nullable=False)
    is_reset_password = db.Column(
        db.Boolean, default=False, nullable=False)  # for resetting password

    setup_budget = db.Column(db.Boolean, default=False, nullable=False)

    user_categories = db.Column(db.String(600), nullable=False,
                                default="['food', 'clothes', 'entertainment', 'sports', 'socialnetwork', \
                             'dailyuse', 'communication', 'electronicdevice', 'education', 'healthcare',\
                             'transportation', 'furniture', 'alcohol',\
                             'shopping', 'snacks', 'travel', 'beauty', 'car', 'other']")
    user_currency = db.Column(db.String(30), nullable=False,
                              default="['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', \
                             'lira(₺)', 'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']")

    # one to one relationship with budget
    budget = db.relationship(
        "UserBudget", uselist=False, back_populates="account")

    # one to many relationship, from account to expenditure
    expenditures = db.relationship("UserExpenditure", back_populates="user")

    def _repr_():
        return 'User id: ' + str(self.id)


class UserBudget(db.Model):
    __tablename__ = "UserBudget"
    id = db.Column(db.Integer, primary_key=True)

    maintanance_loan = db.Column(db.Float)  # for year
    accomodation_cost = db.Column(db.Float)  # for year
    year_budget = db.Column(db.Float)  # for year
    month_budget_list = db.Column(db.String)  # 10 months values in a list
    month_remaining_list = db.Column(db.String)  # 10 months
    week_budget_list = db.Column(db.String)  # 40 weeks values in a list
    week_remaining_list = db.Column(db.String)  # 40 weeks

    date_setup = db.Column(db.DateTime, nullable=False,
                           default=datetime.strptime(datetime.utcnow().strftime('%Y-%m-%d'), '%Y-%m-%d'))
    date_maint1 = db.Column(db.DateTime)
    date_maint2 = db.Column(db.DateTime)
    date_maint3 = db.Column(db.DateTime)
    date_accom1 = db.Column(db.DateTime)
    date_accom2 = db.Column(db.DateTime)
    date_accom3 = db.Column(db.DateTime)

    # weekly and monthly budget
    mcost = db.Column(db.Integer)  # month budget item cost
    mcategory = db.Column(db.String(600), nullable=False, default="other")
    wcost = db.Column(db.Integer)  # month budget item cost
    wcategory = db.Column(db.String(600), nullable=False, default="other")

    # one to one relationship with account
    account_id = db.Column(db.Integer, db.ForeignKey('UserAccount.id'))
    account = db.relationship("UserAccount", back_populates="budget")

    def _repr_():
        return 'User id: ' + str(self.id)


class UserExpenditure(db.Model):
    __tablename__ = "UserExpenditure"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False,
                     default=datetime.strptime(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
    ref = db.Column(db.String(30), nullable=False)
    cost = db.Column(db.Float)
    category = db.Column(db.String(30), nullable=False, default="other")
    currency = db.Column(db.String(20), nullable=False, default="other")

    # one to many relationship, from account to expenditure
    user_id = db.Column(db.Integer, db.ForeignKey("UserAccount.id"))
    user = db.relationship("UserAccount", back_populates="expenditures")

    def _repr_():
        return 'User id: ' + str(self.id)


'''# initialize all the tables: ***
-----------------------------------------------------
   #   added few default records to test as following
   #   should be moved once the tables settle down'''
db.drop_all()
db.create_all()


'''# add a default test useraccount WITHOUT budget'''
test_user2 = UserAccount(username="user123", password="pbkdf2:sha256:150000$OuRhtQ4U$036fed81b7c9a2301e3d248833b299b71595e5d683b99aa07e5548a5e8c90262",
                         email="adrianskapars@gmail.com", email_active=1, setup_budget=False)
db.session.add(test_user2)

'''# add a default test user account WITH budget'''
test_user = UserAccount(username="pwdis123", password="pbkdf2:sha256:150000$3lPCe0Wu$af2a4a32b6644a6e501db3b9607b93cec4acd9f331083be4cff786331326d3b4",
                        email="xuyingyu1108@yeah.net", email_active=1, setup_budget=True)
db.session.add(test_user)


test_budget = UserBudget(maintanance_loan=9000, accomodation_cost=5000, year_budget=4000,
                         month_budget_list="222.22222 " +
                         ("444.444444 "*8)+"222.22222",
                         month_remaining_list="222.22222 444.444444 444.444444 444.444444 444.444444 247.21144400000003 17.82444399999993 340.94444400000003 444.444444 222.22222",
                         week_budget_list=("100 "*40),
                         week_remaining_list="100 100 100 100 100 100 100 100 85.6 78.42699999999999 9.86000000000001 2.280000000000012 15.219999999999999 58.0 -42.96000000000001 39.68000000000001 -41.47999999999999 85.6 82.42 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100",
                         date_maint1=datetime.strptime(
                             "10/09/2020", '%d/%m/%Y'),
                         date_maint2=datetime.strptime(
                             "18/01/2021", '%d/%m/%Y'),
                         date_maint3=datetime.strptime(
                             "19/04/2021", '%d/%m/%Y'),
                         date_accom1=datetime.strptime(
                             "22/10/2020", '%d/%m/%Y'),
                         date_accom2=datetime.strptime(
                             "21/01/2021", '%d/%m/%Y'),
                         date_accom3=datetime.strptime(
                             "26/04/2021", '%d/%m/%Y'),
                         account_id=test_user.id)

db.session.add(test_budget)
test_user.budget = test_budget


'''# add several default test record for daily'''
test_expenses = []

t_exp_ref = ["Sainsburys Groceries", "Groceries Sains", "Sainsburys",     "Grocery Lidl",
             "Weekly Shop",          "Tescos Food",     "Lidl Groceries", "Weekly Groceries",
             "Savers",               "Some Toiletries", "Deoderant",      "Shampoo Conditioner",
             "New Zeland Wines",     "Smirnoff",        "Drinks",
             "Shorts Sportsdirect",  "New Bathrobe",
             "GiffGaff Bill",        "GiffGaff Bill",   "GiffGaff Bill",
             "CompSci Textbook",
             "Leicester Train",      "Train Back",
             "New Calculator",       "Maths Notebooks"]

t_exp_category = ["food",             "food",           "food",           "food",
                  "food",             "food",           "food",           "food",
                  "dailyuse",         "dailyuse",       "dailyuse",       "dailyuse",
                  "alcohol",          "alcohol",        "alcohol",
                  "clothes",          "clothes",
                  "communication",    "communication",  "communication",
                  "education",
                  "transportation",   "transportation",
                  "electronicdevice", "education" ]

t_exp_cost = ["35.76",  "23.99",  "27.50",  "17.00",
              "21.89",  "13.30",  "25.08",  "19.99",
              "6.17",   "4.00",   "1.99",   "2.99",
              "5.00",   "10.99",  "17.28",
              "29.98",  "12.69",
              "10.00",  "10.00",  "10.00",
              "32.99",
              "13.30",  "13.30",
              "14.99",  "2.59"]

t_exp_currency = ["pound(￡)",  "pound(￡)",  "pound(￡)",  "pound(￡)",
                  "pound(￡)",  "pound(￡)",  "pound(￡)",  "pound(￡)",
                  "pound(￡)",  "pound(￡)",  "pound(￡)",  "pound(￡)",
                  "pound(￡)",  "pound(￡)",  "pound(￡)",
                  "pound(￡)",  "euro(€)",
                  "dollar($)",  "dollar($)",  "dollar($)",
                  "pound(￡)",
                  "pound(￡)", "pound(￡)",
                  "pound(￡)", "pound(￡)"]

t_exp_date = [datetime(2021, 4, 3, 20, 47),  datetime(2021, 3, 26, 18, 22),
              datetime(2021, 3, 21, 16, 13),  datetime(
    2021, 3, 13, 19, 35),

    datetime(2021, 3, 6, 19, 10),  datetime(2021, 2, 26, 17, 55),
    datetime(2021, 2, 20, 19, 27),  datetime(
    2021, 2, 15, 14, 32),

    datetime(2021, 3, 26, 17, 50),  datetime(
    2021, 3, 14, 13, 19),
    datetime(2021, 2, 26, 18, 13),  datetime(2021, 2, 23, 19, 1),

    datetime(2021, 3, 31, 22, 58),  datetime(
    2021, 3, 19, 21, 49),
    datetime(2021, 2, 28, 20, 13),

    datetime(2021, 3, 30, 13, 8),  datetime(2021, 2, 10, 8, 57),

    datetime(2021, 4, 5, 12, 0),  datetime(2021, 3, 5, 12, 0),
    datetime(2021, 2, 5, 12, 0),

    datetime(2021, 3, 16, 14, 21),

    datetime(2021, 3, 1, 7, 0),  datetime(2021, 3, 8, 7, 0),

    datetime(2021, 4, 13, 15, 23),  datetime(2021, 4, 13, 15, 25)]


# collect expenses in list
for i in range(0, len(t_exp_ref)):
    test_exp = UserExpenditure(ref=t_exp_ref[i],   category=t_exp_category[i], cost=t_exp_cost[i],
                               currency=t_exp_currency[i], date=t_exp_date[i])
    test_expenses.append(test_exp)

test_user.expenditures = test_expenses


# used this algorithm once but bad to run it every time so hardcoded results into budget
# make budget include expenses, same format as Daily
# for i in range(0, len(test_expenses)):
#     b = test_user.budget

#     monthint= int(test_expenses[i].date.strftime('%m')) # using preset date not now
#     yearint = int(test_expenses[i].date.strftime('%Y')) # using preset date not now

#     # work out which months budget we are handling
#     months_reorder = [-1, 4, 5, 6, 7, 8, 9, -1, -1, 0, 1, 2, 3]
#     month_in_list = months_reorder[monthint] # september is first month so 9->0 but june 2021 is last so 6->9
#     month_remaining_list = b.month_remaining_list.split()
#     month_being_updated = float(month_remaining_list[month_in_list])

#     # work out which weeks budget we are handling
#     days_since_start = test_expenses[i].date - datetime(yearint, 9, 13, 8, 00) # returns delta obj
#     week_in_list = days_since_start.days//7
#     week_remaining_list = b.week_remaining_list.split()
#     week_being_updated = float(week_remaining_list[week_in_list])

#     # convert cost to pounds
#     full_cu = ['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', 'lira(₺)',
#                'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']
#     expense_cost = float(test_expenses[i].cost)
#     conversion = [1, 0.72, 0.85, 0.11, 0.0065, 0.0099, 0.089, 0.00064, 0.0095, 0.55, 1]
#     for j in range(0, len(full_cu)):
#         if test_expenses[i].currency == full_cu[j]:
#             expense_cost = expense_cost * conversion[j]
#             break

#     # subtract expense from month budget remaining
#     month_remaining_list[month_in_list] = str(month_being_updated - float(expense_cost))
#     b.month_remaining_list = " ".join(month_remaining_list) # converts back to string and updates

#     # subtract expense from week budget remaining
#     week_remaining_list[week_in_list] = str(week_being_updated - float(expense_cost))
#     b.week_remaining_list = " ".join(week_remaining_list) # converts back to string and updates

#     db.session.commit()


db.session.commit()


# load user
@login_manager.user_loader
def load_user(user_id):
    return UserAccount.query.get(user_id)


# ---ADDRESS ROUTES---

# Main page
@app.route('/')
def index():
    return render_template('index.html')

########################################################################################


# Account setup page
@app.route('/setup/<username>', methods=['GET', 'POST'])
def Setup(username):
    if request.method == 'POST':

        # figure out maintanance loan and accomodation cost
        maintanance_loan = request.form.get('loan')
        if maintanance_loan == '':
            loanlevel = request.form['rad']
            homestatus = request.form['rad2']

            # if rad & rad2 not set as well:
            if loanlevel == '' and homestatus == '':
                flash('Your are not enter your maintanance loan or choose your loan level!')
                return redirect(url_for('Setup', username=username))

            if loanlevel == "min":
                if homestatus == "home":
                    maintanance_loan = 3410
                elif homestatus == "nolnd":
                    maintanance_loan = 4289
                else:
                    maintanance_loan = 5981
            elif loanlevel == "mid":
                if homestatus == "home":
                    maintanance_loan = (3410+7747)/2
                elif homestatus == "nolnd":
                    maintanance_loan = (4289+9203)/2
                else:
                    maintanance_loan = (5981+12010)/2
            elif loanlevel == "max":
                if homestatus == "home":
                    maintanance_loan = 7747
                elif homestatus == "nolnd":
                    maintanance_loan = 9203
                else:
                    maintanance_loan = 12010
            else:
                maintanance_loan = 0
        else:
            maintanance_loan = float(maintanance_loan)

        accomodation_cost = request.form.get('acost')
        if accomodation_cost == '':
            fallowfield_accomodation = [
                5975, 4394, 6328, 6174, 6185, 6693, 6338]
            optionaccom = request.form.get('optionaccom')
            accomodation_cost = fallowfield_accomodation[int(optionaccom)-1]
        else:
            accomodation_cost = float(accomodation_cost)

        # calculate budget based off of loan and cost
        year_budget = maintanance_loan - accomodation_cost
        one_month = year_budget/9
        # september and june are half months
        month_budget_list = str(one_month/2)+" " + \
            ((str(one_month)+" ")*8)+str(one_month/2)
        week_budget_list = (str(year_budget/40) + " ")*40

        date_maint1 = datetime.strptime(
            request.form.get('mtdate1'), '%d/%m/%Y')
        date_maint2 = datetime.strptime(
            request.form.get('mtdate2'), '%d/%m/%Y')
        date_maint3 = datetime.strptime(
            request.form.get('mtdate3'), '%d/%m/%Y')
        date_accom1 = datetime.strptime(
            request.form.get('acdate1'), '%d/%m/%Y')
        date_accom2 = datetime.strptime(
            request.form.get('acdate2'), '%d/%m/%Y')
        date_accom3 = datetime.strptime(
            request.form.get('acdate3'), '%d/%m/%Y')

        # get the user record via the passed username
        user = UserAccount.query.filter_by(username=username).first()
        user.setup_budget = True
        user_id = user.id

        new_budget = UserBudget(maintanance_loan=maintanance_loan, accomodation_cost=accomodation_cost,
                                year_budget=year_budget, month_budget_list=month_budget_list,
                                month_remaining_list=month_budget_list, week_budget_list=week_budget_list,
                                week_remaining_list=week_budget_list,
                                date_maint1=date_maint1, date_maint2=date_maint2, date_maint3=date_maint3,
                                date_accom1=date_accom1, date_accom2=date_accom2, date_accom3=date_accom3,
                                account_id=user_id)

        db.session.add(new_budget)
        db.session.commit()

        return redirect(url_for('Daily', username=username))

    return render_template('setup.html', username=username)


@app.route('/setup/<username>/edit', methods=['GET', 'POST'])
def Setup_edit(username):
    # get the user record via the passed username
    user = UserAccount.query.filter_by(username=username).first()
    b = user.budget

    if request.method == 'POST':

        # figure out maintanance loan and accomodation cost
        maintanance_loan = request.form.get('loan')
        if maintanance_loan == '':
            loanlevel = request.form['rad']
            homestatus = request.form['rad2']

            if loanlevel == "min":
                if homestatus == "home":
                    maintanance_loan = 3410
                elif homestatus == "nolnd":
                    maintanance_loan = 4289
                else:
                    maintanance_loan = 5981
            elif loanlevel == "mid":
                if homestatus == "home":
                    maintanance_loan = (3410+7747)/2
                elif homestatus == "nolnd":
                    maintanance_loan = (4289+9203)/2
                else:
                    maintanance_loan = (5981+12010)/2
            elif loanlevel == "max":
                if homestatus == "home":
                    maintanance_loan = 7747
                elif homestatus == "nolnd":
                    maintanance_loan = 9203
                else:
                    maintanance_loan = 12010
            else:
                maintanance_loan = 0
        else:
            maintanance_loan = float(maintanance_loan)

        accomodation_cost = request.form.get('acost')
        if accomodation_cost == '':
            fallowfield_accomodation = [
                5975, 4394, 6328, 6174, 6185, 6693, 6338]
            optionaccom = request.form.get('optionaccom')
            accomodation_cost = fallowfield_accomodation[int(optionaccom)-1]
        else:
            accomodation_cost = float(accomodation_cost)

        # calculate budget based off of loan and cost
        year_budget = maintanance_loan - accomodation_cost
        one_month = year_budget/9
        # september and june are half months
        month_budget_list = str(one_month/2)+" " + \
            ((str(one_month)+" ")*8)+str(one_month/2)
        week_budget_list = (str(year_budget/40) + " ")*40

        date_maint1 = datetime.strptime(
            request.form.get('mtdate1'), '%d/%m/%Y')
        date_maint2 = datetime.strptime(
            request.form.get('mtdate2'), '%d/%m/%Y')
        date_maint3 = datetime.strptime(
            request.form.get('mtdate3'), '%d/%m/%Y')
        date_accom1 = datetime.strptime(
            request.form.get('acdate1'), '%d/%m/%Y')
        date_accom2 = datetime.strptime(
            request.form.get('acdate2'), '%d/%m/%Y')
        date_accom3 = datetime.strptime(
            request.form.get('acdate3'), '%d/%m/%Y')

        b.maintanance_loan = maintanance_loan
        b.accomodation_cost = accomodation_cost
        b.year_budget = year_budget
        b.month_budget_list = month_budget_list
        b.month_remaining_list = month_budget_list
        b.week_budget_list = week_budget_list
        b.week_remaining_list = week_budget_list
        b.date_maint1 = date_maint1
        b.date_maint2 = date_maint2
        b.date_maint3 = date_maint3
        b.date_accom1 = date_accom1
        b.date_accom2 = date_accom2
        b.date_accom3 = date_accom3

        db.session.commit()

        return redirect(url_for('Daily', username=username))

    return render_template('setup_edit.html', budget=b, username=username)

########################################################################################


# - Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('uname')
        password = request.form.get('password')
        password = generate_password_hash(password)  # hashing password

        '''# if no such user, create a new useraccount:'''
        checkU = UserAccount.query.filter_by(username=username).first()
        checkE = UserAccount.query.filter_by(email=email).first()
        if checkU is None and checkE is None:
            user = UserAccount(username=username, email=email,
                               password=password)

            db.session.add(user)
            db.session.commit()

            emptyUser = UserAccount.query.filter_by(username='').first()
            if emptyUser is None:

                user = UserAccount(username=username, email=email,
                                   password=password)

                # validate email -- generate email token
                token = ts.dumps(user.email, salt='email-confirm-key')
                print(token)
                #send_email(user.email,'Please confirm your account','auth/email/confirm',user,token)
                send_email(user.email, 'Please confirm your account',
                           '/confirm/', user, token)
                flash('Validation email has been sent!')
                return redirect(url_for('login'))

                # return render_template('login.html')
            else:
                '''empty exist --- need to change'''
                #msg = "existing empty"
                # print(msg)
                db.session.delete(emptyUser)
                db.session.commit()
                #isUser = False
                flash("Input username is empty")
                return render_template('register.html')
        else:
            '''# already exist  --- wrong  *need to modify'''
            #isUser = False
            flash("User already exists, Please change to another username", 'warning')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/confirm/<token>')
# @login_required
def confirm(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        print('email_token', email)
        user = UserAccount.query.filter_by(email=email).first_or_404()
        print('email-- user', user)
        user.email_confirmed = True
        user.email_active = True
        # db.session.add(user)
        db.session.commit()
        flash("email activated")
        return redirect(url_for('login'))
    except:
        print("error", token)

    return redirect(url_for('login'))


# submit reset form
@app.route('/password_reset_success/', methods=['GET', 'POST'])
def password_reset_success():
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('password')
        password = generate_password_hash(password)  # hashing password

        checkU = UserAccount.query.filter_by(username=username).first()
        if checkU is not None and checkU.is_reset_password == 1:
            checkU.password = password
            checkU.is_reset_password = 0
            db.session.commit()
            flash("Reset was successful")
            return render_template('reset_pwd2.html')
        else:
            flash("Username is incorrect or has already been reset")
            return render_template('reset_pwd2.html')
    return render_template('reset_pwd2.html')


# @app.before_app_request
# def before_request():
#    if current_user.is_authenticated \
#            and not current_user.confirmed \
#            and request.endpoint[:5] != 'auth.'\
#            and request.endpoint != 'static':
#        return redirect(url_for('index'))


# @app.route("/mail_send_test")
# definition to send email(register confirm && password reset)
def send_email(to, subject, template, user, token):
    #msg = Message(subject='Hello', sender='1659335946@qq.com', recipients=['xuyingyu1108@yeah.net'])
    confirm_url = url_for(
        'confirm',
        token=token,
        _external=True)
    msg = Message(subject=subject, sender='1823075630@qq.com',
                  recipients=[to], body="link here",
                  html=render_template(
                      'activate.html',
                      confirm_url=confirm_url))

    mail.send(msg)


def send_email_reset(to, subject, template, user, token):
    #msg = Message(subject='Hello', sender='1659335946@qq.com', recipients=['xuyingyu1108@yeah.net'])
    confirm_url = url_for(
        'password_reset',
        token=token,
        _external=True)
    msg = Message(subject=subject, sender='1823075630@qq.com',
                  recipients=[to], body="link here",
                  html=render_template(
                      'activate.html',
                      confirm_url=confirm_url))

    mail.send(msg)


# - login page
@ app.route('/login', methods=['POST', 'GET'])
def login():
    isLogin = True
    #form = LoginForm()

    if request.method == 'POST':
        un = request.form.get('uname')
        pwd = request.form.get('psw')
        #user = UserAccount.query.filter_by(username=form.username.data).first()
        user = UserAccount.query.filter_by(username=un).first()
        # if user and check_password_hash(user.password, form.password.data):
        if user and check_password_hash(user.password, pwd):
            if user.email_active:
                login_user(user)
                # print(user.id)
                if not user.setup_budget:
                    return redirect(url_for('Setup', username=user.username))
                else:
                    return redirect(url_for('Daily', username=user.username))

                # return redirect(url_for('account', \
                #    user=[user.id, user.username]))
            else:
                flash('Email address not confirmed yet ', 'warning')
                return redirect('/login')
        else:
            flash('Invalid credentials ', 'warning')
            return redirect('/login')
    #flash('failed in if')

    # return render_template("login.html", isLogin=isLogin, form=form)
    return render_template("login.html", isLogin=isLogin)


@app.route('/account/<id>/<username>', methods=['POST', 'GET'])
def account(id, username):
    # print(username)
    user = UserAccount.query.filter_by(username=username).first_or_404()

    #app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

    user_ca = json.loads(user.user_categories.replace('\'', '"'))
    user_cu = json.loads(user.user_currency.replace('\'', '"'))

    if request.method == 'POST':

        result = request.form
        # print(result)
        result = ImmutableMultiDict(result)
        user_currency = result.getlist("user_currency")
        user_categories = result.getlist("user_categories")

        mcost = result.getlist("mcost")
        mcost = " ".join(mcost)
        wcost = result.getlist("wcost")
        wcost = " ".join(wcost)

        mcategory = result.getlist("mcategory")
        mcategory = " ".join(mcategory)
        wcategory = result.getlist("wcategory")
        wcategory = " ".join(wcategory)
            
        all_budget_detail = UserBudget(mcost=mcost, mcategory=mcategory,wcost=wcost, wcategory=wcategory)

        db.session.add(all_budget_detail)
        print("added new budget.")

        db.session.commit()
        return redirect(url_for('account', id=user.id, username=user.username))

    else:
        user_categories = user.user_categories
        user_currency = user.user_currency

        all_mcost = UserBudget.query.all()
        all_wcost = UserBudget.query.all()

        expense_detail = UserExpenditure.query.all()

        list = []
        data = {}
        for x in expense_detail:
            if x.category not in list:
                list.append(x.category)

        for x in list:
            category_expense = UserExpenditure.query.filter_by(
                user_id=user.id).filter_by(category=x)
            sum = 0
            for i in category_expense:
                sum = sum + i.cost
            data[x] = sum

        category_data_weekly = {}
        category_average_4weeks = {}
        avg4weeks = []
        for x in list:
            category_expense = UserExpenditure.query.filter_by(
                user_id=user.id).filter_by(category=x)
            sum = 0
            category_average_4weeks[x] = 0
            for i in category_expense:
                current = datetime.now()
                if ((current - i.date).days <= 7):
                    sum = sum + i.cost
                elif (current - i.date).days <= 36:
                    category_average_4weeks[x] = category_average_4weeks[x] + i.cost
            category_data_weekly[x] = sum

        return render_template("account.html", username=username, user=user, budget=user.budget,
                               user_currency=user.user_currency, user_categories=user.user_categories,
                               user_ca=user_ca, user_cu=user_cu, mcost=all_mcost,
                               wcost=all_wcost, cost=expense_detail,data=data,
                               monthdata=category_average_4weeks,weekdata=category_data_weekly)
                               


# set user preference in account page
@app.route('/account/preference/<id>/<username>', methods=['POST', 'GET'])
def user_prefer(id, username):
    # print(username)
    user = UserAccount.query.filter_by(username=username).first_or_404()

    #app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

    user_ca = json.loads(user.user_categories.replace('\'', '"'))
    user_cu = json.loads(user.user_currency.replace('\'', '"'))

    full_cu_o = "['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', \
                             'lira(₺)', 'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']"
    full_cu = json.loads(full_cu_o.replace('\'', '"'))

    full_ca_o = "['food', 'clothes', 'entertainment', 'sports', 'socialnetwork', \
                             'dailyuse', 'communication', 'electronicdevice', 'education', 'healthcare',\
                             'transportation', 'furniture','alcohol',\
                             'shopping', 'snacks', 'travel', 'beauty', 'car', 'other']"
    full_ca = json.loads(full_ca_o.replace('\'', '"'))

    if request.method == 'POST':
        user = UserAccount.query.filter_by(username=username).first_or_404()
        result = request.form
        print(result)
        result = ImmutableMultiDict(result)
        user_currency = result.getlist("user_currency")

        user_categories = result.getlist("user_categories")

        print(result)
        # print(user_currency)
        # print(user_categories)

        user.user_currency = str(user_currency)
        user.user_categories = str(user_categories)
        db.session.commit()

        user_ca = json.loads(user.user_categories.replace('\'', '"'))
        user_cu = json.loads(user.user_currency.replace('\'', '"'))
        # print('user_ca?', user_ca)

        print("added perference.")
        return render_template("user_preference.html", username=username, user=user, budget=user.budget,
                               user_currency=user.user_currency, user_categories=user.user_categories,
                               user_ca=user_ca, user_cu=user_cu,
                               full_cu=full_cu, full_ca=full_ca)

    user_categories = user.user_categories
    user_currency = user.user_currency

    return render_template("user_preference.html", username=username, user=user, budget=user.budget,
                           user_currency=user.user_currency, user_categories=user.user_categories,
                           user_ca=user_ca, user_cu=user_cu,
                           full_cu=full_cu, full_ca=full_ca)


# - Reset password page
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('uname')
        email = request.form.get('email')
        userU = UserAccount.query.filter_by(username=username).first()
        userE = UserAccount.query.filter_by(email=email).first()
        # if UserAccount.query.filter_by(email=email).first() is not None:
        if userU is not None and userE is not None:
            if userU == userE:
                userU.is_reset_password = 1
                db.session.commit()
                # validate email -- generate email token
                token = ts.dumps(email, salt='email-confirm-key')
                # print(token)
                send_email_reset(
                    userU.email, 'You are resetting your account', '/reset/', userU, token)
                flash('Validation email has been sent!')
                # return redirect(url_for('index'))
            else:
                flash('Username and email cannot match')
        else:
            flash('Username or email is not registered')

    return render_template('reset_pwd.html')


@app.route('/change/<username>', methods=['GET', 'POST'])
def changepassword(username):
    if request.method == 'POST':
        current_pass = request.form.get('oldpass')
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')

        user = UserAccount.query.filter_by(username=username).first()

        if pass1 != pass2:
            flash("Password does not match")
            return render_template('change.html')

        if check_password_hash(user.password, current_pass):
            user.password = generate_password_hash(pass1)
            db.session.commit()
            flash("Password updated successfully")
            return redirect(url_for('Daily', username=user.username))

    return render_template('change.html')


# reset password by accessing link sended to registered email
@app.route('/reset/<token>')
def password_reset(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        #print('email_token', email)
        user = UserAccount.query.filter_by(email=email).first_or_404()
        if UserAccount.query.filter_by(email=email).first() is not None:
            #print('email-- user -- reset', user)
            flash("Email sent! Enter the new password.")
        # return redirect(url_for('reset_password'))
        return render_template('reset_pwd2.html')

    except:
        print("error", token)
        # abort(404)

    return render_template('reset_pwd2.html')


# - Logout page
@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')


########################################################################################


# Daily use page
@ app.route('/daily/<username>', methods=['GET', 'POST'])
def Daily(username):
    user = UserAccount.query.filter_by(username=username).first_or_404()
    b = user.budget

    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

    user_ca = json.loads(user.user_categories.replace('\'', '"'))
    user_cu = json.loads(user.user_currency.replace('\'', '"'))

    # Working out how far into week and month and amount of days in month
    weeklyprog = datetime.utcnow().weekday()
    monthlyprog = int(datetime.utcnow().strftime('%d'))

    daysinmonth = 30
    monthint = int(datetime.utcnow().strftime('%m'))
    yearint = int(datetime.utcnow().strftime('%Y'))

    leapint = 0
    if yearint % 400 == 0:
        leapint = 1
    elif yearint % 100 == 0:
        leapint = 0
    elif yearint % 4 == 0:
        leapint = 1

    listint = [1, 3, 5, 7, 8, 10, 12]
    if monthint == 2:
        daysinmonth = 28 + leapint
    elif monthint in listint:
        daysinmonth = 31

    # work out which months budget we are handling
    months_reorder = [-1, 4, 5, 6, 7, 8, 9, -1, -1, 0, 1, 2, 3]
    # september is first month so 9->0 but june 2021 is last so 6->9
    month_in_list = months_reorder[monthint]
    month_budget_list = b.month_budget_list.split()
    month_current = float(month_budget_list[month_in_list])

    month_remaining_list = b.month_remaining_list.split()
    month_being_updated = float(month_remaining_list[month_in_list])

    # work out which weeks budget we are handling
    days_since_start = datetime.utcnow() - datetime(yearint, 9, 13,
                                                    8, 00)  # returns delta obj
    week_in_list = days_since_start.days//7
    week_budget_list = b.week_budget_list.split()
    week_current = float(week_budget_list[week_in_list])

    week_remaining_list = b.week_remaining_list.split()
    week_being_updated = float(week_remaining_list[week_in_list])

    # Handling new expense
    if request.method == 'POST':
        id = request.form['user_id']
        if id is not None:  # login user
            expense_ref = request.form['ref']
            expense_cost = float(request.form['cost'])
            expense_category = request.form['category']
            expense_currency = request.form['currency']
            new_expense = UserExpenditure(ref=expense_ref, cost=expense_cost, user_id=id,
                                          category=expense_category, currency=expense_currency)
            db.session.add(new_expense)

            # convert cost to pounds
            full_cu = ['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', 'lira(₺)',
                       'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']
            conversion = [1, 0.72, 0.85, 0.11, 0.0065,
                          0.0099, 0.089, 0.00064, 0.0095, 0.55, 1]
            for i in range(0, len(full_cu)):
                if expense_currency == full_cu[i]:
                    expense_cost = expense_cost * conversion[i]
                    break

            # subtract expense from month budget remaining
            month_remaining_list[month_in_list] = str(
                month_being_updated - float(expense_cost))
            # converts back to string and updates
            b.month_remaining_list = " ".join(month_remaining_list)

            # subtract expense from week budget remaining
            week_remaining_list[week_in_list] = str(
                week_being_updated - float(expense_cost))
            # converts back to string and updates
            b.week_remaining_list = " ".join(week_remaining_list)

            db.session.commit()

            return redirect(url_for('Daily', username=username))
        else:
            # not login: user_id=null
            return redirect(url_for('Daily', username=username))

    else:
        return render_template('daily.html', username=username, budget=b,
                               user_ca=user_ca, user_cu=user_cu, weeklyprog=weeklyprog,
                               monthlyprog=monthlyprog, daysinmonth=daysinmonth,
                               monthbudget=month_current, monthremaining=month_being_updated,
                               weekbudget=week_current, weekremaining=week_being_updated)

    return render_template('daily.html', username=username, budget=b,
                           user_ca=user_ca, user_cu=user_cu, weeklyprog=weeklyprog,
                           monthlyprog=monthlyprog, daysinmonth=daysinmonth,
                           monthbudget=month_current, monthremaining=month_being_updated,
                           weekbudget=week_current, weekremaining=week_being_updated)


# Statistics and history page
@ app.route('/statistics/<username>/<int:page>', methods=['GET', 'POST'])
def Statistics(username, page):

    # divide into several pages

    show_shouye_status = 0  # display start page

    if page == '':
        page = 1
    else:
        page = int(page)
    if page > 1:
        show_shouye_status = 1

    #print("page: ", page)

    user = UserAccount.query.filter_by(username=username).first_or_404()
    user_expenditure_all = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).all()
    user_list = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items

    count = len(user_expenditure_all)  # total records number
    total = int((count/10.0))  # total page number
    print('count', count, 'total', total)
    # judge if there is another paginate page:
    x = count - total*10
    if x is not None:
        total += 1
        if page == total:
            user_list_extra = UserExpenditure.query.filter_by(
                user_id=user.id).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=x, error_out=False).items

            dic = get_page(total, page)
            datas = {
                'mode': 'normal',
                'user_list': user_list_extra,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('datas,', datas)

        else:
            dic = get_page(total, page)
            datas = {
                'mode': 'normal',
                'user_list': user_list,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('datas,', datas)

    else:

        dic = get_page(total, page)
        datas = {
            'mode': 'normal',
            'user_list': user_list,
            'page': int(page),
            'total': total,
            'show_shouye_status': show_shouye_status,
            'dic_list': dic

        }
        #print('datas,', datas)

    user = UserAccount.query.filter_by(username=username).first_or_404()

    user_expenditure_all = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).all()
    # check the pages:
    user_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items

    #print('pages: ', user_expenditure)

    # display only recorded categories -calculate lists
    list = []
    list0 = []
    list1 = []
    for exp in user_expenditure_all:
        list.append(exp.category)
    for i in range(len(list)):
        for j in range(i+1, len(list)):
            if list[i] == list[j]:
                list[j] = ''
            if list[i] == '':
                i += 1
    while '' in list:
        list.remove('')

    for i in range(int(len(list)/2)):
        list0.append(list[i])
        if list[i+int(len(list)/2)] is None:
            pass
        else:
            list1.append(list[i+int(len(list)/2)])
    print(list0, list1)

    # testtt
    print("testtt-page: ", page, "lenofex: ", len(user_expenditure))
    return render_template('statistics.html', expense=user_expenditure_all,
                           category_list0=list0, category_list1=list1,
                           page=page, page_expense=user_expenditure, datas=datas)


def get_page(total, p):
    """get page enspul"""
    show_page = 5
    pageoffset = 2
    start = 1  #
    end = total

    if total > show_page:
        if p > pageoffset:
            start = p - pageoffset
            if total > p + pageoffset:
                end = p + pageoffset
            else:
                end = total
        else:
            start = 1
            if total > show_page:
                end = show_page
            else:
                end = total
        if p + pageoffset > total:
            start = start - (p + pageoffset - end)
    # loop purpose
    dic = range(start, end + 1)
    return dic


@ app.route('/statistics/<username>/category/<category>/<int:page>', methods=['GET', 'POST'])
def Statistics_category(username, category, page):

    # add divide:
    show_shouye_status = 0  # display start page

    if page == '':
        page = 1
    else:
        page = int(page)
    if page > 1:
        show_shouye_status = 1

    print("page: ", page)

    user = UserAccount.query.filter_by(username=username).first_or_404()
    category_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id).filter_by(
        category=category).order_by(UserExpenditure.date.desc()).all()
    user_list = UserExpenditure.query.filter_by(
        user_id=user.id).filter_by(
        category=category).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items

    count = len(category_expenditure)  # total records number
    total = int((count/10.0))  # total page number
    print('count', count, 'total', total)
    # judge if there is another paginate page:
    x = count - total*10
    if x is not None:
        total += 1
        if page == total:
            user_list_extra = UserExpenditure.query.filter_by(
                user_id=user.id).filter_by(
                category=category).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=x, error_out=False).items

            dic = get_page(total, page)
            datas = {
                'mode': 'category',
                'user_list': user_list_extra,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('category datas,', datas)

        else:
            dic = get_page(total, page)
            datas = {
                'mode': 'category',
                'user_list': user_list,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('category datas,', datas)

    else:

        dic = get_page(total, page)
        datas = {
            'mode': 'category',
            'user_list': user_list,
            'page': int(page),
            'total': total,
            'show_shouye_status': show_shouye_status,
            'dic_list': dic

        }
        #print('category datas,', datas)

    # check the pages:
    #user_expenditure = []
    user_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id).filter_by(
        category=category).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items
    user_expenditure_all = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).all()
    print('pages: ', user_expenditure)

    list = []
    list0 = []
    list1 = []
    for exp in user_expenditure_all:
        list.append(exp.category)
    for i in range(len(list)):
        for j in range(i+1, len(list)):
            if list[i] == list[j]:
                list[j] = ''
            if list[i] == '':
                i += 1
    while '' in list:
        list.remove('')
    # print(list)
    for i in range(int(len(list)/2)):
        list0.append(list[i])
        if list[i+int(len(list)/2)] is None:
            pass
        else:
            list1.append(list[i+int(len(list)/2)])
    print(list0, list1)
    return render_template('statistics.html', expense=category_expenditure,
                           category_list0=list0, category_list1=list1,
                           page=page, page_expense=user_expenditure, datas=datas)


@ app.route('/statistics/<username>/search/<stuff>/<int:page>', methods=['GET', 'POST'])
def Statistics_search(username, page, stuff):

    show_shouye_status = 0  # display start page
    if page == '':
        page = 1
    else:
        page = int(page)
    if page > 1:
        show_shouye_status = 1
    #print("page: ", page)

    user = UserAccount.query.filter_by(username=username).first_or_404()

    user_expenditure_all = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).all()
    # check the pages:
    user_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id).filter_by(
        ref=stuff).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items

    #print('pages: ', user_expenditure)

    search_expense = UserExpenditure.query.filter_by(user_id=user.id).filter_by(
        ref=stuff).order_by(UserExpenditure.date.desc()).all()

    count = len(search_expense)  # total records number
    total = int((count/10.0))  # total page number
    print('count', count, 'total', total)
    # judge if there is another paginate page:
    x = count - total*10
    if x is not None:
        total += 1
        if page == total:
            user_list_extra = UserExpenditure.query.filter_by(
                user_id=user.id).filter_by(
                ref=stuff).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=x, error_out=False).items

            dic = get_page(total, page)
            datas = {
                'mode': 'search',
                'user_list': user_list_extra,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('datas,', datas)

        else:
            dic = get_page(total, page)
            datas = {
                'mode': 'search',
                'user_list': user_list,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('datas,', datas)

    else:

        dic = get_page(total, page)
        datas = {
            'mode': 'search',
            'user_list': user_list,
            'page': int(page),
            'total': total,
            'show_shouye_status': show_shouye_status,
            'dic_list': dic

        }
        #print('datas,', datas)

    # display only recorded categories -calculate lists
    list = []
    list0 = []
    list1 = []
    for exp in user_expenditure_all:
        list.append(exp.category)
    for i in range(len(list)):
        for j in range(i+1, len(list)):
            if list[i] == list[j]:
                list[j] = ''
            if list[i] == '':
                i += 1
    while '' in list:
        list.remove('')
    # print(list)
    for i in range(int(len(list)/2)):
        list0.append(list[i])
        if list[i+int(len(list)/2)] is None:
            pass
        else:
            list1.append(list[i+int(len(list)/2)])
    #print(list0, list1)

    # if search certain ref name?
    if request.method == 'POST':
        search = request.form['search']
        #category = request.form['Category']
        user = UserAccount.query.filter_by(username=username).first_or_404()
        if search is not None:
            search_expense = UserExpenditure.query.filter_by(user_id=user.id).filter_by(
                ref=search).order_by(UserExpenditure.date.desc()).all()
        # elif category is not None:
        #    search_expense  = UserExpenditure.query.filter_by(user_id=user.id).filter_by(category=category).order_by(UserExpenditure.date).all()

        show_shouye_status = 0  # display start page

        if page == '':
            page = 1
        else:
            page = int(page)
        if page > 1:
            show_shouye_status = 1

        #print("page: ", page)

        user = UserAccount.query.filter_by(username=username).first_or_404()

        user_list = UserExpenditure.query.filter_by(
            user_id=user.id).filter_by(
            ref=search).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items

        user_expenditure = UserExpenditure.query.filter_by(
            user_id=user.id).filter_by(
            ref=search).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=10, error_out=False).items

        #print('pages: ', user_expenditure)

        count = len(search_expense)  # total records number
        total = int((count/10.0))  # total page number
        print('count', count, 'total', total)
        # judge if there is another paginate page:
        x = count - total*10
        if x is not None:
            total += 1
            if page == total:
                user_list_extra = UserExpenditure.query.filter_by(
                    user_id=user.id).filter_by(
                    ref=search).order_by(UserExpenditure.date.desc()).paginate(page=page, per_page=x, error_out=False).items

                dic = get_page(total, page)
                datas = {
                    'mode': 'search',
                    'user_list': user_list_extra,
                    'page': int(page),
                    'total': total,
                    'show_shouye_status': show_shouye_status,
                    'dic_list': dic

                }
                #print('datas,', datas)

            else:
                dic = get_page(total, page)
                datas = {
                    'mode': 'search',
                    'user_list': user_list,
                    'page': int(page),
                    'total': total,
                    'show_shouye_status': show_shouye_status,
                    'dic_list': dic

                }
                #print('datas,', datas)

        else:

            dic = get_page(total, page)
            datas = {
                'mode': 'search',
                'user_list': user_list,
                'page': int(page),
                'total': total,
                'show_shouye_status': show_shouye_status,
                'dic_list': dic

            }
            #print('datas,', datas)

        return render_template('statistics.html', expense=search_expense,
                               category_list0=list0, category_list1=list1,
                               page=page, page_expense=user_expenditure, datas=datas)
    return render_template('statistics.html', expense=search_expense,
                           category_list0=list0, category_list1=list1,
                           page=page, page_expense=user_expenditure, datas=datas)


@ app.route('/statistics/delete/<username>/<stuff>/<mode>/<page>', methods=['GET', 'POST'])
def Statistics_delete(username, stuff, mode, page):
    user = UserAccount.query.filter_by(username=username).first_or_404()
    delete_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id).filter_by(id=stuff).first()
    b = user.budget

    expense_currency = delete_expenditure.currency
    expense_cost = float(delete_expenditure.cost)

    # convert cost to pounds
    full_cu = ['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', 'lira(₺)',
               'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']
    conversion = [1, 0.72, 0.85, 0.11, 0.0065,
                  0.0099, 0.089, 0.00064, 0.0095, 0.55, 1]
    for i in range(0, len(full_cu)):
        if expense_currency == full_cu[i]:
            expense_cost = expense_cost * conversion[i]
            break

    monthint = int(delete_expenditure.date.strftime('%m'))
    yearint = int(delete_expenditure.date.strftime('%Y'))
    # work out which months budget we are handling, add old and subtract new
    months_reorder = [-1, 4, 5, 6, 7, 8, 9, -1, -1, 0, 1, 2, 3]
    # september is first month so 9->0 but june 2021 is last so 6->9
    month_in_list = months_reorder[monthint]
    month_remaining_list = b.month_remaining_list.split()
    month_being_updated = float(month_remaining_list[month_in_list])
    month_being_updated = month_being_updated + expense_cost
    month_remaining_list[month_in_list] = str(month_being_updated)
    # converts back to string and updates
    b.month_remaining_list = " ".join(month_remaining_list)

    # work out which weeks budget we are handling, subtract old and add new
    days_since_start = delete_expenditure.date - \
        datetime(yearint, 9, 13, 8, 00)  # returns delta obj
    week_in_list = days_since_start.days//7
    week_remaining_list = b.week_remaining_list.split()
    week_being_updated = float(week_remaining_list[week_in_list])
    week_being_updated = week_being_updated + expense_cost
    week_remaining_list[week_in_list] = str(week_being_updated)
    # converts back to string and updates
    b.week_remaining_list = " ".join(week_remaining_list)

    db.session.delete(delete_expenditure)
    db.session.commit()

    # determine certain back page:
    #mode = request.args.getlist('mode')
    print("mode: ", mode)
    print("page", page)

    if mode == 'normal':
        #print("is there?")
        return redirect(url_for('Statistics', username=username, page=int(page)))
    elif mode == 'category':
        return redirect(url_for('Statistics_category', username=username, page=int(page),
                                category=delete_expenditure.category))
    elif mode == 'search':
        return redirect(url_for('Statistics_search', username=username, page=int(page),
                                stuff=delete_expenditure.ref))
    # return redirect(url_for('Statistics', username=username, page=1))


@ app.route('/statistics/edit/<username>/<stuff>/<mode>/<page>', methods=['GET', 'POST'])
def Statistics_edit(username, stuff, mode, page):
    user = UserAccount.query.filter_by(username=username).first_or_404()
    edit_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id).filter_by(id=stuff).first()
    b = user.budget

    user_ca = json.loads(user.user_categories.replace('\'', '"'))
    user_cu = json.loads(user.user_currency.replace('\'', '"'))

    # determine certain back page:
    #mode = request.args.getlist('mode')

    #print("data???", datas)
    #print("data type", type(datas))
    #data_l = json.loads(eval(datas))
    #print("data type", type(data_l))
    #mode = data_l.value("mode")
    print("mode: ", mode)
    print("page: ", page)

    if request.method == 'POST':
        edit_expenditure.ref = request.form['ref']
        edit_expenditure.category = request.form['category']

        # dealing with changes in currency and cost

        original_cost = float(edit_expenditure.cost)
        original_currency = edit_expenditure.currency

        # convert original cost to pounds
        full_cu = ['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', 'lira(₺)',
                   'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']
        conversion = [1, 0.72, 0.85, 0.11, 0.0065,
                      0.0099, 0.089, 0.00064, 0.0095, 0.55, 1]
        for i in range(0, len(full_cu)):
            if original_currency == full_cu[i]:
                original_cost = original_cost * conversion[i]
                break

        expense_cost = float(request.form['cost'])
        expense_currency = request.form['currency']

        # convert new cost to pounds
        for i in range(0, len(full_cu)):
            if expense_currency == full_cu[i]:
                expense_cost = expense_cost * conversion[i]
                break

        monthint = int(edit_expenditure.date.strftime('%m'))
        yearint = int(edit_expenditure.date.strftime('%Y'))
        # work out which months budget we are handling, add old and subtract new
        months_reorder = [-1, 4, 5, 6, 7, 8, 9, -1, -1, 0, 1, 2, 3]
        # september is first month so 9->0 but june 2021 is last so 6->9
        month_in_list = months_reorder[monthint]
        month_remaining_list = b.month_remaining_list.split()
        month_being_updated = float(month_remaining_list[month_in_list])
        month_being_updated = month_being_updated + original_cost - expense_cost
        month_remaining_list[month_in_list] = str(month_being_updated)
        # converts back to string and updates
        b.month_remaining_list = " ".join(month_remaining_list)

        # work out which weeks budget we are handling, subtract old and add new
        days_since_start = edit_expenditure.date - \
            datetime(yearint, 9, 13, 8, 00)  # returns delta obj
        week_in_list = days_since_start.days//7
        week_remaining_list = b.week_remaining_list.split()
        week_being_updated = float(week_remaining_list[week_in_list])
        week_being_updated = week_being_updated + original_cost - expense_cost
        week_remaining_list[week_in_list] = str(week_being_updated)
        # converts back to string and updates
        b.week_remaining_list = " ".join(week_remaining_list)

        # finally overwrite old values in db since no longer need to use them
        edit_expenditure.cost = float(request.form['cost'])
        edit_expenditure.currency = request.form['currency']

        db.session.commit()

        if mode == 'normal':

            print("is there?")
            # pass
            return redirect(url_for('Statistics', username=username, page=int(page),
                                    edit=edit_expenditure))
        elif mode == 'category':
            return redirect(url_for('Statistics_category', username=username, page=int(page),
                                    category=edit_expenditure.category, edit=edit_expenditure))
        elif mode == 'search':
            return redirect(url_for('Statistics_search', username=username, page=int(page),
                                    stuff=edit_expenditure.ref, edit=edit_expenditure))
        # print("ok??")
        # return redirect(url_for('Statistics', username=username, page=1, edit=edit_expenditure))

    # return redirect(url_for('Statistics', username=username, edit=edit_expenditure))
    return render_template('daily_edit.html', edit=edit_expenditure,
                           user_ca=user_ca, user_cu=user_cu,
                           page=int(page), mode=mode)


@ app.route('/account/monthbudget', methods=['GET', 'POST'])
def new_mbudget():

    if request.method == 'POST':
        mbudgets.mcost = request.form['mcost']
        print(mbudgets.mcost)
        #chosen_mcategory = request.form['mcategory']
        new_mbudget = UserBudget(mcost=chosen_mbudget_cost)
        db.session.add(new_mbudget)
        db.session.commit()
        return redirect('/account/<id>/<username>')
    else:
        return render_template('budget_m.html')


@ app.route('/account/weekbudget', methods=['GET', 'POST'])
def new_wbudget():
    if request.method == 'POST':
        wbudgets.wcost = request.form['wcost']
        new_wbudget = UserBudget(wcost=chosen_wbudget_cost)
        db.session.add(new_wbudget)
        db.session.commit()
        return render_template('/account/<id>/<username>')
    else:
        return render_template('budget_w.html')


# Graphs and insights page
@ app.route('/insights/<username>', methods=['GET', 'POST'])
def Insights(username):
    user = UserAccount.query.filter_by(username=username).first_or_404()
    user_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id)
    user_expenditure_all = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).all()

    list_categories = []
    category_data = {'Category': 'Expenditure'}

    for x in user_expenditure_all:
        if x.category not in list_categories:
            list_categories.append(x.category)

    for x in list_categories:
        category_expense = UserExpenditure.query.filter_by(
            user_id=user.id).filter_by(category=x)
        sum = 0
        for i in category_expense:
            sum = sum + i.cost
        category_data[x] = sum

    # print(category_data)

    category_data_weekly = {'Category': 'Expendtiure'}
    category_average_4weeks = {}
    avg4weeks = []
    for x in list_categories:
        category_expense = UserExpenditure.query.filter_by(
            user_id=user.id).filter_by(category=x)
        sum = 0
        category_average_4weeks[x] = 0
        for i in category_expense:
            current = datetime.now()
            if ((current - i.date).days <= 7):
                sum = sum + i.cost
            elif (current - i.date).days <= 36:
                category_average_4weeks[x] = category_average_4weeks[x] + i.cost
        category_data_weekly[x] = sum

    print(category_data_weekly)
    # print(category_average_4weeks)

    for l in list_categories:
        if category_average_4weeks[l] != 0:
            category_average_4weeks[l] = (category_average_4weeks[l] / 30) * 7

    for x in list_categories:
        # category_expense = UserExpenditure.query.filter_by(
        #     user_id=user.id).filter_by(category=x)
        # sum = 0
        # for i in category_expense:
        #     current = datetime.now()
        #     if ((current - i.date).days <= 6):
        #         sum = sum + i.cost
        #     elif (current - i.date).days <= 36:
        #         avg4weeks.append(i)
        # category_data_weekly[x] = sum
        avg4weeks.append(
            [x, category_data_weekly[x], category_average_4weeks[x]])
    print(category_average_4weeks)
    print(avg4weeks)

    alert = []
    for x in avg4weeks:
        if x[2] != 0 and x[1] != 0:
            div = x[1] / (x[2] * 0.25)
            if (div) >= 1.2:
                alert.append(x[0])

    if (len(alert)) != 0:
        alert2 = "" ############################ added this part to get rid of square brackets
        for i in range(len(alert)):
            if i == 0:
                alert2 += str(alert[i])
            elif i > 0 and i == (len(alert) -1):
                alert2 += " and " +str(alert[i])
            elif i > 0 and i != (len(alert) -1):
                alert2 += ", " +str(alert[i]) 
        print("ejfbejfbeeeeeeeeeeeeeeeeeeeeee")
        flash(f"You are spending more on {alert2} than last week")

    # judge if week digram would be empty:
    x = 0
    empty_week = 0
    # print(len(category_data_weekly))
    for v in category_data_weekly:
        # print(v)
        if category_data_weekly[v] == 0:
            x += 1
    if x == len(category_data_weekly) - 1:
        empty_week = 1
    #print(empty_week, "empty?", "x:", x)

    return render_template('insights.html', username=username, budget=user.budget, data=category_data, weekly_category=category_data_weekly, avg=category_average_4weeks,
                           empty_week=empty_week)

########################################################################################

# Support page - Qna/privacy policy


@ app.route('/qna', methods=['GET', 'POST'])
def QnA():
    whichOption = True
    msg = "This is page where u can ask us."
    return render_template('support.html', msg=msg, whichOption=whichOption)


@ app.route('/privacy', methods=['POST', 'GET'])
def Privacy():
    whichOption = False
    msg = "This is page with privacy policy infomation."
    return render_template('support.html', msg=msg, whichOption=whichOption)


# ---MAIN CALL---

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True)
