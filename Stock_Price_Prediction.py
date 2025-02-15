import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import yfinance as yf
import matplotlib.pyplot as plt
from prophet import Prophet
from gtts import gTTS
import os
import openai

# Set OpenAI API Key
openai.api_key = "API_KEY"

# Common Company Ticker Mappings
COMMON_TICKERS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "facebook": "META",
    "netflix": "NFLX",
    "nvidia": "NVDA"
}

# Function: Speak Text
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("response.mp3")
    os.system("afplay response.mp3")  # MacOS: afplay, Windows: start, Linux: mpg321

# Function: Recognize Speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        result_label.config(text="Listening...", fg="red")
        root.update()
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio).lower()
            result_label.config(text=f"You said: {text}", fg="black")
            return text
        except sr.UnknownValueError:
            result_label.config(text="Could not understand.", fg="red")
            return None
        except sr.RequestError:
            result_label.config(text="Speech service unavailable.", fg="red")
            return None

# Function: Get Stock Ticker Symbol
def get_ticker(company_name):
    company_name = company_name.lower().strip()
    return COMMON_TICKERS.get(company_name, company_name.upper())

# Function: Get Live Stock Price
def get_stock_price(company_name):
    ticker = get_ticker(company_name)
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close'].iloc[-1]
        response = f"The price of {company_name.capitalize()} ({ticker}) is ${round(price, 2)}."
    except:
        response = "Error fetching stock price."
    
    update_history(company_name, response)
    result_label.config(text=response, fg="black")
    speak(response)

# Function: Predict Stock Trend
def predict_stock_trend(company_name):
    ticker = get_ticker(company_name)
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        df.reset_index(inplace=True)
        df['Date'] = df['Date'].dt.tz_localize(None)
        df = df[['Date', 'Close']]
        df.columns = ['ds', 'y']

        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        response = f"Trend predicted for {company_name.capitalize()} ({ticker})."
        update_history(company_name, response)
        result_label.config(text=response, fg="red")
        speak(response)

        plt.figure(figsize=(8, 4))
        plt.plot(df['ds'], df['y'], label="Actual Prices", color="black")
        plt.plot(forecast['ds'], forecast['yhat'], label="Predicted Trend", color="red")
        plt.xlabel("Date")
        plt.ylabel("Stock Price")
        plt.title(f"{company_name.capitalize()} ({ticker}) Stock Prediction", color="black")
        plt.legend()
        plt.show()

    except:
        response = "Error predicting trend."
        update_history(company_name, response)
        result_label.config(text=response, fg="red")
        speak(response)

# Function: Stock Market Q&A using ChatGPT
def stock_market_qna(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a stock market expert."},
                      {"role": "user", "content": question}]
        )
        answer = response["choices"][0]["message"]["content"]
        update_history(question, answer)
        result_label.config(text=answer, fg="black")
        speak(answer)
    except:
        response = "Error retrieving answer."
        update_history(question, response)
        result_label.config(text=response, fg="red")
        speak(response)

# Function: Process User Input
def process_query():
    query = user_input.get().lower()

    if any(phrase in query for phrase in ["price of", "stock price", "how much is"]):
        company_name = query.split("price of")[-1].strip()
        get_stock_price(company_name)
    
    elif any(phrase in query for phrase in ["predict", "forecast", "future of"]):
        company_name = query.split("predict")[-1].strip()
        predict_stock_trend(company_name)
    
    elif "exit" in query or "stop" in query:
        root.quit()
    
    else:
        stock_market_qna(query)

# Function: Process Voice Command
def process_voice():
    query = recognize_speech()
    if query:
        user_input.delete(0, tk.END)
        user_input.insert(0, query)
        process_query()

# Function: Update History
def update_history(query, response):
    history_list.insert(tk.END, f"Q: {query} | A: {response}")

# UI Elements
root = tk.Tk()
root.title("Stock Market Assistant")
root.geometry("700x600")
root.configure(bg="white")

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), padding=10, background="red", foreground="white")

# Title
title_label = tk.Label(root, text="Stock Market Assistant", font=("Arial", 18, "bold"), fg="red", bg="white")
title_label.pack(pady=10)

# Entry Box
user_input = tk.Entry(root, width=50, font=("Arial", 14), bg="white", fg="black", insertbackground="black")
user_input.pack(pady=10)

# Buttons
button_frame = tk.Frame(root, bg="white")
button_frame.pack(pady=10)

submit_button = tk.Button(button_frame, text="Submit", font=("Arial", 12, "bold"), bg="red", fg="black",
                          activebackground="darkred", activeforeground="white", command=process_query)
submit_button.pack(side=tk.LEFT, padx=10)

voice_button = tk.Button(button_frame, text="Speak", font=("Arial", 12, "bold"), bg="red", fg="black",
                         activebackground="darkred", activeforeground="white", command=process_voice)
voice_button.pack(side=tk.RIGHT, padx=10)

# Result Label
result_label = tk.Label(root, text="", font=("Arial", 12), fg="black", bg="white", wraplength=600, justify="left")
result_label.pack(pady=10)

# History Section
history_label = tk.Label(root, text="History", font=("Arial", 14, "bold"), fg="red", bg="white")
history_label.pack(pady=5)

history_list = tk.Listbox(root, width=80, height=10, font=("Arial", 12), bg="white", fg="black")
history_list.pack(pady=5)

# Run App
root.mainloop()

