import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import hashlib
import re
import random
from datetime import datetime
import csv
import io
import requests
from bs4 import BeautifulSoup

class HealthcareChatbot:
    def __init__(self, master):
        self.master = master
        self.master.title("Healthcare Chatbot")
        self.master.geometry("600x500")

        self.users_df = pd.read_csv('users.csv')
        self.symptoms_df = self.read_symptoms_csv()
        self.doctors_df = pd.read_csv('doctors_dataset.csv')

        self.current_user = None

        self.create_login_widgets()

    def read_symptoms_csv(self):
        try:
            return pd.read_csv('symptoms.csv')
        except pd.errors.ParserError:
            with open('symptoms.csv', 'r', newline='', encoding='utf-8') as f:
                content = f.read()
            
            content = content.replace('\x00', '')
            string_io = io.StringIO(content)
            df = pd.read_csv(string_io, error_bad_lines=False, warn_bad_lines=True)
            
            expected_columns = ['id', 'name', 'symptom', 'description', 'specialty']
            df = df.reindex(columns=expected_columns)
            
            return df

    def create_login_widgets(self):
        self.clear_widgets()

        ttk.Label(self.master, text="Welcome to HealthBot", font=("Arial", 18)).pack(pady=20)
        ttk.Label(self.master, text="Username:").pack(pady=5)
        self.username_entry = ttk.Entry(self.master, width=30)
        self.username_entry.pack(pady=5)

        ttk.Label(self.master, text="Password:").pack(pady=5)
        self.password_entry = ttk.Entry(self.master, width=30, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(self.master, text="Login", command=self.login).pack(pady=10)
        ttk.Button(self.master, text="Sign Up", command=self.create_signup_widgets).pack(pady=5)

    def create_signup_widgets(self):
        self.clear_widgets()

        ttk.Label(self.master, text="Create an Account", font=("Arial", 18)).pack(pady=20)
        ttk.Label(self.master, text="Username:").pack(pady=5)
        self.signup_username_entry = ttk.Entry(self.master, width=30)
        self.signup_username_entry.pack(pady=5)

        ttk.Label(self.master, text="Password:").pack(pady=5)
        self.signup_password_entry = ttk.Entry(self.master, width=30, show="*")
        self.signup_password_entry.pack(pady=5)

        ttk.Label(self.master, text="Email:").pack(pady=5)
        self.signup_email_entry = ttk.Entry(self.master, width=30)
        self.signup_email_entry.pack(pady=5)

        ttk.Button(self.master, text="Sign Up", command=self.signup).pack(pady=10)
        ttk.Button(self.master, text="Back to Login", command=self.create_login_widgets).pack(pady=5)

    def create_chatbot_widgets(self):
        self.clear_widgets()

        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(1, weight=1)

        ttk.Label(self.master, text=f"Welcome, {self.current_user}!", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)

        self.chat_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=50, height=20)
        self.chat_area.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.chat_area.config(state=tk.DISABLED)

        self.user_input = ttk.Entry(self.master, width=50)
        self.user_input.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        send_button = ttk.Button(self.master, text="Send", command=self.process_user_input)
        send_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.user_input.bind("<Return>", lambda event: self.process_user_input())

        logout_button = ttk.Button(self.master, text="Logout", command=self.logout)
        logout_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.display_message("HealthBot: Hello! How can I assist you today? You can ask about symptoms, get health advice, or request a doctor consultation.")

    def clear_widgets(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        hashed_password = self.hash_password(password)

        user = self.users_df[(self.users_df['username'] == username) & (self.users_df['password'] == hashed_password)]
        if not user.empty:
            self.current_user = username
            messagebox.showinfo("Success", "Login successful!")
            self.create_chatbot_widgets()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    def signup(self):
        username = self.signup_username_entry.get()
        password = self.signup_password_entry.get()
        email = self.signup_email_entry.get()

        if username in self.users_df['username'].values:
            messagebox.showerror("Error", "Username already exists.")
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email address.")
            return

        hashed_password = self.hash_password(password)
        new_user = pd.DataFrame({'username': [username], 'password': [hashed_password], 'email': [email], 'role': ['user']})
        self.users_df = pd.concat([self.users_df, new_user], ignore_index=True)
        self.users_df.to_csv('users.csv', index=False)
        messagebox.showinfo("Success", "Sign up successful!")
        self.create_login_widgets()

    def logout(self):
        self.current_user = None
        self.create_login_widgets()

    def display_message(self, message):
        print(f"Debug: Displaying message: {message}")  # Debug print
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def process_user_input(self):
        user_input = self.user_input.get().lower()
        self.user_input.delete(0, tk.END)
        print(f"Debug: User input received: {user_input}")  # Debug print
        self.display_message(f"You: {user_input}")

        if "headache" in user_input or any(symptom.lower() in user_input for symptom in self.symptoms_df['symptom']):
            response = self.process_symptoms(user_input)
        elif "doctor" in user_input or "consultation" in user_input:
            response = self.suggest_doctor()
        elif "advice" in user_input or "tip" in user_input:
            response = self.provide_health_advice()
        else:
            response = "I'm sorry, I didn't understand that. Can you please rephrase or ask about specific symptoms, doctor consultations, or health advice?"

        print(f"Debug: Bot response: {response}")  # Debug print
        self.display_message(f"HealthBot: {response}")

    def generate_response(self, user_input):
        user_input = user_input.lower()

        if "symptom" in user_input or "feel" in user_input:
            return self.process_symptoms(user_input)
        elif "doctor" in user_input or "consultation" in user_input:
            return self.suggest_doctor()
        elif "advice" in user_input or "tip" in user_input:
            return self.provide_health_advice()
        else:
            return "I'm sorry, I didn't understand that. Can you please rephrase or ask about symptoms, doctor consultations, or health advice?"

    def process_symptoms(self, user_input):
        user_symptoms = [symptom for symptom in self.symptoms_df['symptom'].tolist() if symptom.lower() in user_input.lower()]

        if not user_symptoms:
            return "I couldn't identify any specific symptoms. Can you please describe how you're feeling in more detail?"

        recommendations = self.symptoms_df[self.symptoms_df['symptom'].isin(user_symptoms)]
        
        result = "Based on the symptoms you mentioned, here are some possible conditions and recommendations:\n\n"
        for _, row in recommendations.iterrows():
            result += f"- {row['name']}:\n  {row['description']}\n"
            result += f"  Recommendation: {self.get_recommendation(row['name'])}\n\n"

        result += self.suggest_doctors(user_symptoms)
        return result

    def suggest_doctors(self, symptoms):
        relevant_doctors = self.find_relevant_doctors(symptoms)
        
        if not relevant_doctors:
            return "\nI couldn't find any doctors specifically matching your symptoms. Please consult a general physician."

        result = "\nHere are some doctors you may want to consult based on your symptoms:\n\n"
        for doctor in relevant_doctors:
            result += f"Dr. {doctor['name']}\n"
            result += f"Consultation link: {doctor['url']}\n\n"
        
        result += "\nPlease note that this is not a definitive diagnosis. If you're concerned about your symptoms, please consult a healthcare professional."
        return result

    def find_relevant_doctors(self, symptoms):
        relevant_doctors = []
        symptom_keywords = set()

        for symptom in symptoms:
            symptom_row = self.symptoms_df[self.symptoms_df['symptom'] == symptom].iloc[0]
            keywords = symptom_row['name'].lower().replace(' ', '_')
            symptom_keywords.add(keywords)
            symptom_keywords.add(symptom.lower().replace(' ', '_'))

        for _, doctor in self.doctors_df.iterrows():
            doctor_keywords = set(doctor['keywords'].lower().split())
            if symptom_keywords.intersection(doctor_keywords):
                relevant_doctors.append({
                    'name': doctor['name'],
                    'url': doctor['url']
                })

        return relevant_doctors

    def get_doctor_specialty(self, doctor_name):
        specialties = {
            'General Physician': ['Singh', 'Shrivastava', 'Biswas', 'Vij'],
            'Homoeopath': ['Arya', 'Dwivedi', 'Bansal', 'Khera', 'Mohan'],
            'Ear-Nose-Throat (ENT) Specialist': ['Munjal', 'Jain', 'Gupta', 'Khatri', 'Adhana', 'Tripathi', 'Wadhawan', 'Sood', 'Narula'],
            'Ayurveda': ['Asokan', 'Shah', 'Singh', 'Bhola', 'Monga', 'Abbot', 'Gupta', 'Mutreja'],
            'Dermatologist': ['Kashyap', 'Jain', 'Batra', 'Gupta', 'Garg', 'Sharma', 'Chopra', 'Upadhyay'],
            'Gynecologist/Obstetrician': ['Juneja']
        }

        for specialty, names in specialties.items():
            if any(name in doctor_name for name in names):
                return specialty
        
        # If no specific specialty is found, check for general keywords
        if any(keyword in doctor_name.lower() for keyword in ['general', 'physician', 'doctor']):
            return 'General Physician'
        
        return 'Specialist'  # Changed from 'General Physician' to 'Specialist' for unclassified doctors

    def provide_health_advice(self):
        advice_list = [
            "Stay hydrated by drinking at least 8 glasses of water a day.",
            "Aim for 7-9 hours of sleep each night to support your overall health.",
            "Include a variety of fruits and vegetables in your diet for essential nutrients.",
            "Regular exercise can boost your mood and improve your overall health.",
            "Practice stress-reduction techniques like meditation or deep breathing exercises.",
            "Limit processed foods and opt for whole, nutrient-dense options.",
            "Don't forget to schedule regular check-ups with your healthcare provider.",
            "Wash your hands frequently to prevent the spread of germs.",
            "Take breaks from screens and practice the 20-20-20 rule to reduce eye strain.",
            "Stay up to date with your vaccinations to protect yourself and others."
        ]
        return random.choice(advice_list)

    def get_recommendation(self, symptom):
        recommendations = {
            "Headache": "Rest in a quiet, dark room. Try over-the-counter pain relievers like ibuprofen or acetaminophen. Stay hydrated and apply a cold or warm compress to your head.",
            "Fever": "Rest and drink plenty of fluids. Take acetaminophen or ibuprofen to reduce fever. If fever persists or is high, consult a doctor.",
            "Cough": "Stay hydrated and use honey to soothe your throat. For dry coughs, try over-the-counter cough suppressants. For productive coughs, use expectorants.",
            "Fatigue": "Get plenty of rest and ensure you're staying hydrated. Eat a balanced diet and consider light exercise if you feel up to it.",
            "Nausea": "Eat small, frequent meals and avoid fatty or spicy foods. Try ginger tea or peppermint to soothe your stomach.",
        }
        return recommendations.get(symptom, "Consult a healthcare professional for personalized advice.")

def main():
    root = tk.Tk()
    app = HealthcareChatbot(root)
    root.mainloop()

if __name__ == "__main__":
    main()