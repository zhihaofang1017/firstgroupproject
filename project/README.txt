###### environment set up instruction#####
# to enter the environment, use the following instructions:
# . env/bin/activate
# or:
# source env/bin/activate 
# win: venv\scripts\activate

# to exit the env:
# deactivate

##### program run instruction#####

# package needed:(plz pip or pip3 install first)
flask, flask-sqlalchemy, flask-login, flask_mail, pandas, matplotlib

# first run the main python file:
python3 main_app.py

# After running py, open the browser and access  localhost or 'http://0.0.0.0:8080/'
# If use windows system, access  'http://127.0.0.1:8080/'(localhost)


##### GIT VERSION CONTROL #####
(Before make changes)
git pull
git branch nameOfBranch01
git checkout nameOfBranch01
(Make changes)
git add -A (add changes)
git commit -m "message" (commit changes)
git checkout master
git pull
git merge nameOfBranch01 -m "message" 
(double tap tab if forgotten what you called the branch and it will give u suggestion)
git push
(Also good if then delete branch pointer once finished)
git branch -d nameOfBranch01


##### login account instruction #####
# when meet none column error in login:
***should drop_all the tables and create_all since new column appears
has already add these two commands in main_app

***If u need to reserve the data, Plz comment/delete those two line(drop_all&create_all) in  main_app***

# Register:
need to input valid email account since email validation was set

# After register: (perhaps need modify)
will receive a new email with activate link from the given email
need to click it to activate account
otherwise ur account is not valid and cannot login

# Forgot password?
Click 'forget password?' to '/reset_password' page
Enter ur username and email
Then, will receive another email called 'You are resetting your account'
Click the link in the email mentioned above
Then enter your new password (need to enter the correct username)
Finally successfully reset pwd(in the situation that u forget old password)

