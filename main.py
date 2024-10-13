from healthcare_chatbot import HealthcareChatbot
import tkinter as tk

def main():
    root = tk.Tk()
    app = HealthcareChatbot(root)
    root.mainloop()

if __name__ == "__main__":
    main()
