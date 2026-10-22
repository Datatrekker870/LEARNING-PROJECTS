# A program with a main menu and three sub-menus (Data, SMS, Minutes). 
# The user picks a category, then picks a specific bundle, confirms the purchase, and 
# the cost is deducted from a starting balance. 
# The program keeps running until the user chooses Exit.

bundles = {
    "Data": [
        {"name": "50MB - Daily",   "price": 5,   "validity": "24 hours"},
        {"name": "500MB - Weekly", "price": 50,  "validity": "7 days"},
        {"name": "2GB - Monthly",  "price": 200, "validity": "30 days"},
    ],
    "SMS": [
        {"name": "20 SMS - Daily",   "price": 5,  "validity": "24 hours"},
        {"name": "200 SMS - Weekly", "price": 20, "validity": "7 days"},
    ],
    "Minutes": [
        {"name": "10 Min - Daily",    "price": 10,  "validity": "24 hours"},
        {"name": "100 Min - Monthly", "price": 100, "validity": "30 days"},
    ]
}

# Step 1: Write a function main_menu() that prints the main menu below 
# and returns the user's choice (as a string or int - your choice, just be consistent):
balance = 200.00   # starting airtime balance in Ksh
menu = ['Buy Data Bundle','Buy SMS Bundle','Buy Minutes Bundle','Check Balance','Exit']
def show_menu():
    for i, item in enumerate(menu, start=1):
        print(f"{i}. {item}")
    
    choice = int(input("Enter choice: "))
    return choice

# Step 2: Write a function show_bundles(category, bundle_list) 
# that displays all bundles in a given category, numbered using enumerate(), 
# plus a '0. Back to main menu' option. 
def show_bundles(category, bundles): #sub-menu
    for  i,bundle in enumerate(bundles,start=1):
        name = bundle.get('name')
        price = bundle.get('price')
        validity = bundle.get('validity')
        print(f"{i}. {name} | Ksh {price} | Valid for {validity}")
    print("0.Back to Main Menu")
    choice = int(input("Enter your choice: "))
    return choice


# Step 3: Write a function buy_bundle(category, bundle_list, balance) that:
# • Calls show_bundles() in a
# while True loop so the sub-menu keeps showing until the user picks a bundle or goes back
# • If the user enters 0, break out of the loop (back to main menu)
# • If the user enters a valid bundle number, show a confirmation prompt:
# "Confirm purchase of <name> for Ksh <price>? (y/n):"
# • If confirmed and balance is enough, deduct the price from balance and
# print a success message with the new balance
# • If balance is not enough, print "Insufficient balance. Please top up."
# and do NOT deduct anything
# • If the input is invalid (not a number, or out of range), print an error 
# and continue the loop instead of crashing
# • Return the (possibly updated) balance


def buy_bundle(category, bundle_list, balance=200):
    while True:
        choice = show_bundles(category, bundle_list)
        
        # If user enters 0, break out of the loop (back to main menu)
        if choice == 0:
            break
        if 1 <= choice <= len(bundle_list):
            selected_bundle = bundle_list[choice - 1]
            name = selected_bundle['name'] 
            price = selected_bundle['price']
        
            confirm = input(f"Confirm purchase of {name} for Ksh {price}? (y/n): ")
            
            if confirm == 'y' :
                if balance >= price:
                    balance -= price
                    print(f"Purchase successful! You have purchased {name} ")
                    print(f"Your new balance is: Ksh {balance}")
                else:
                    print("Insufficient balance. Please top up.")
            elif confirm == 'n' :
                print("Purchase cancelled.")
            elif  confirm == ''  :
                print('please select y/n')   
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        else:
            print("Invalid choice. Please select a valid bundle number.")
    
    return balance

## Write a function check_balance(balance) that prints:
#  "Your current balance is Ksh <balance>" formatted to 2 decimal places.
def check_balance(balance):
    return f"Your current balance is Ksh.{balance:.2f}"

# Write the main program loop: a while True loop that calls main_menu(),
#  then uses if/elif/else to route to the right function based on the choice:
# • 1 → call buy_bundle("Data", bundles["Data"], balance) and update balance with what it returns
# • 2 → same, but for "SMS"
# • 3 → same, but for "Minutes"
# • 4 → call check_balance(balance)
# • 5 → print a goodbye message and break out of the main loop
# • Anything else → print an error message and continue

while True:
    choice_menu = show_menu()

    if choice_menu == 1:
        balance = buy_bundle("Data", bundles["Data"], balance)
        print(f"Balance :{balance}")
    elif choice_menu == 2 :
        balance = buy_bundle("SMS", bundles["SMS"], balance)
        print(f"Balance :{balance}")   
    elif choice_menu == 3 :
        balance = buy_bundle("Minutes", bundles["Minutes"], balance)
        print(f"Balance :{balance}")
    elif choice_menu == 4 :
        print(check_balance(balance))
    elif choice_menu == 5 :
        print("Thank you for choosing us!")
        break
    else:
        print("That is a wrong choice try again!")




      
            
            
        





        

