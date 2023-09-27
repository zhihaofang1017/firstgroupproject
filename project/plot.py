import pandas as pd
#import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from main_app import UserAccount
from main_app import UserExpenditure
from main_app import UserBudget

def create_graph(username):
    user = UserAccount.query.filter_by(username=username).first_or_404()

    ''' caculate data '''
    day_budget = user.budget.day_loan
    day_remaining_budget = user.budget.day_remaining_budget
    day_used_budget = day_budget - day_remaining_budget
    #budegt = {"day_used_budget": [day_used_budget],
    #          "day_remaining_budget":  [day_remaining_budget]
    #    }
    budegt = [day_used_budget, day_remaining_budget]

    ''' import graph '''
    df = pd.DataFrame(budegt, index=["day_used_budget","day_remaining_budget"], columns=["user"])
    print(df)
    fig = Figure()
    ax  = fig.add_subplot(111)
    plot1 = ax.pie(df["user"],explode=[0.05]*2, shadow=True, 
                labels=["day_used_budget", "day_remaining_budget"], 
                autopct='% .0f %%')
    red_patch = mpatches.Patch(color='red', label=username)
    ax.legend(handles=[red_patch], loc='upper right',bbox_to_anchor=(1.00, 0.85))
    ax.title.set_text('day budget')
    fig.savefig('static/users_pie/'+username+'_day_budget1.png', dpi=500)

    # fig = plt.figure(figsize=(10,6))
    # #plot = plt.pie(df, labels=["day_used_budget", "day_remaining_budget"],
    # #               explode=[0.05]*2)
    # plot1 = plt.pie(df["user"],explode=[0.05]*2, shadow=True, 
    #                 labels=["day_used_budget", "day_remaining_budget"], 
    #                 autopct='% .0f %%')
    # red_patch = mpatches.Patch(color='red', label=username)
    # plt.legend(handles=[red_patch], loc='upper right',bbox_to_anchor=(1.00, 0.85))
    # plt.title("day budget")
    # #plt.show()
    # fig.savefig('static/users_pie/'+username+'_day_budget.png', dpi=500)