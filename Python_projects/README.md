## Bundle Purchase Simulator (*544#)
This project is similar to safaricom's data bundle,SMS and Minutes  purchase menu using basic python logic.

## Data Structure
We are using a dicionary of dictionaries where the keyss are Data,SMS and Minutes followed by their respective  values.

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
    ]}
balance = 200.00     #starting airtime balance in Ksh

## Build It - Step by Step

`Step 1`: Write a function `main_menu()` that prints the main menu below and returns the user's choice (as a string or int - your choice, just be consistent):

`========================================`

              `*544#`

`========================================`
1. Buy Data Bundle
2. Buy SMS Bundle
3. Buy Minutes Bundle
4. Check Balance
5. Exit

========================================

Enter choice (1-5):

`Step 2`: Write a function `show_bundles(category, bundle_list)` that displays all bundles in a given category, numbered using `enumerate()`, `plus a '0`. Back to main menu' option. For example, calling it with "Data" should print:

`--- DATA BUNDLES ---`

`1. 50MB - Daily     | Ksh 5   | Valid: 24 hours`

`2. 500MB - Weekly   | Ksh 50  | Valid: 7 days`

`3. 2GB - Monthly    | Ksh 200 | Valid: 30 days`

`0. Back to main menu`
 
Enter choice:

`Step 3`: Write a function `buy_bundle(category, bundle_list, balance)` that:
* Calls `show_bundles()` in a `while True` loop so the sub-menu keeps showing until the user picks a bundle or goes back
* If the user enters `0`, `break out` of the loop (back to main menu)
* If the user enters a valid bundle number, show a confirmation prompt:`"Confirm purchase of <name> for Ksh <price>? (y/n):"`
* If confirmed and balance is enough, deduct the price from balance and print a success message with the new balance
* If balance is not enough, print `"Insufficient balance. Please top up." and do NOT deduct anything`
* If the input is *invalid (not a number, or out of range)`, print an error and continue the loop instead of crashing`
* Return the (possibly updated) balance.

`Step 4:` Write a function `check_balance(balance)` that prints: `"Your current balance is Ksh <balance>" formatted to 2 decimal places.`

`Step 5:` Write the main program loop: a while True loop that calls `main_menu()`, then uses if/elif/else to route to the right function based on the choice:
* 1 → call buy_bundle("Data", bundles["Data"], balance) and update balance with what it returns
* 2 → same, but for "SMS"
* 3 → same, but for "Minutes"
* 4 → call check_balance(balance)
* 5 → print a goodbye message and break out of the main loop
* 6  Anything else → print an error message and continue

## Sample Run (what your program should look and feel like)
`Enter choice (1-5): 1`
 
`--- DATA BUNDLES ---`

`1. 50MB - Daily     | Ksh 5   | Valid: 24 hours`

`2. 500MB - Weekly   | Ksh 50  | Valid: 7 days`

`3. 2GB - Monthly    | Ksh 200 | Valid: 30 days`

`0. Back to main menu`
 
`Enter choice: 2`

`Confirm purchase of 500MB - Weekly for Ksh 50? (y/n): y`

`Purchase successful! New balance: Ksh 150.00`
 
`Enter choice (1-5): 3`
 
`--- MINUTES BUNDLES ---`

`1. 10 Min - Daily     | Ksh 10  | Valid: 24 hours`

`2. 100 Min - Monthly  | Ksh 100 | Valid: 30 days`

`0. Back to main menu`
 
`Enter choice: 2`
`Confirm purchase of 100 Min - Monthly for Ksh 100? (y/n): y`

`Insufficient balance. Please top up.`
 
`Enter choice: 0`
 
`Enter choice (1-5): 4`

`Your current balance is Ksh 150.00`
 
`Enter choice (1-5): 5`

`Thank you for using *544#. Goodbye!`

## Things to Think About While Building
* You'll have a while loop INSIDE another while loop (the sub-menu inside the main menu). Be careful which break sends you back to the main menu vs. which one exits the whole program.
* Since balance can change inside buy_bundle(), you need to return it and reassign it in the main loop - a function can't permanently change a variable that was passed to it unless you return the new value and store it.
* Test what happens when balance is exactly equal to the bundle price - should the purchase go through?
* Bonus (optional): if you're comfortable with try/except, wrap your input() calls with it so a non-number entry doesn't crash the whole program - a simple if/isdigit() check works fine too if you haven't covered try/except yet.



