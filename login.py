import tkinter as tk
from healthcare_chatbot import HealthcareChatbot

app = None  # Global variable to hold the main window

def create_login_window():
    global app
    app = tk.Tk()
    # ... add login widgets and layout here ...
    app.mainloop()

def login():
    global app
    if app:
        app.destroy()  # Close the login window
    root = tk.Tk()
    chatbot = HealthcareChatbot(root)
    root.mainloop()

# Call this function to start the application
create_login_window()
